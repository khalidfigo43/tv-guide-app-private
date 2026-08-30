import json
import time
from pathlib import Path

import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config import TMDB_ACCESS_TOKEN
from database import Content


DATABASE_URL = "sqlite:///data/tvguide.db"

TMDB_BASE_URL = "https://api.themoviedb.org/3"

OUTPUT_FILE = Path("data/tmdb_search_results.json")

HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json",
}


session_http = requests.Session()
session_http.headers.update(HEADERS)


def tmdb_search(endpoint, title):
    url = f"{TMDB_BASE_URL}/{endpoint}"

    params = {
        "query": title,
        "language": "ar-SA",
        "include_adult": "false",
    }

    last_error = None

    for attempt in range(1, 4):

        try:
            response = session_http.get(
                url,
                params=params,
                timeout=(5, 15),
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:

            last_error = e

            print(
                f"  Attempt {attempt}/3 failed: {e}"
            )

            if attempt < 3:
                time.sleep(attempt * 2)

    raise last_error


def search_title(title):

    movie_data = tmdb_search(
        "search/movie",
        title,
    )

    tv_data = tmdb_search(
        "search/tv",
        title,
    )

    return {
        "movies": movie_data.get(
            "results",
            []
        ),
        "tv": tv_data.get(
            "results",
            []
        ),
    }


def clean_movie(item):

    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "original_title": item.get(
            "original_title"
        ),
        "release_date": item.get(
            "release_date"
        ),
        "popularity": item.get(
            "popularity"
        ),
        "poster_path": item.get(
            "poster_path"
        ),
        "backdrop_path": item.get(
            "backdrop_path"
        ),
        "overview": item.get(
            "overview"
        ),
    }


def clean_tv(item):

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "original_name": item.get(
            "original_name"
        ),
        "first_air_date": item.get(
            "first_air_date"
        ),
        "popularity": item.get(
            "popularity"
        ),
        "poster_path": item.get(
            "poster_path"
        ),
        "backdrop_path": item.get(
            "backdrop_path"
        ),
        "overview": item.get(
            "overview"
        ),
    }


def main():

    if not TMDB_ACCESS_TOKEN:
        print(
            "ERROR: TMDB_ACCESS_TOKEN is missing."
        )
        return

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Load previous results if available
    # ---------------------------------------------------------

    if OUTPUT_FILE.exists():

        try:
            results = json.loads(
                OUTPUT_FILE.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            results = {}

    else:
        results = {}

    # ---------------------------------------------------------
    # Load content
    # ---------------------------------------------------------

    with Session(engine) as db:

        contents = db.scalars(
            select(Content)
            .order_by(Content.id)
        ).all()

    print(
        f"Found {len(contents)} content records."
    )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    for index, content in enumerate(
        contents,
        start=1,
    ):

        title = content.title_ar

        key = str(content.id)

        # Already processed
        if key in results:

            print(
                f"[{index}/{len(contents)}] "
                f"{title} → already processed"
            )

            continue

        print()
        print(
            f"[{index}/{len(contents)}] "
            f"Searching: {title}"
        )

        try:

            data = search_title(title)

            movies = [
                clean_movie(x)
                for x in data["movies"][:10]
            ]

            tv = [
                clean_tv(x)
                for x in data["tv"][:10]
            ]

            results[key] = {
                "content_id": content.id,
                "title": title,
                "status": "success",
                "movies": movies,
                "tv": tv,
            }

            print(
                f"  Movies: {len(movies)}"
            )

            print(
                f"  TV: {len(tv)}"
            )

        except Exception as e:

            print(
                f"  ERROR: {e}"
            )

            results[key] = {
                "content_id": content.id,
                "title": title,
                "status": "error",
                "error": str(e),
                "movies": [],
                "tv": [],
            }

        # -----------------------------------------------------
        # Save after EVERY title
        # -----------------------------------------------------

        OUTPUT_FILE.write_text(
            json.dumps(
                results,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # Small delay
        time.sleep(0.5)

    print()
    print("=" * 80)
    print("TMDB SEARCH COMPLETE")
    print("=" * 80)

    success = sum(
        1
        for x in results.values()
        if x.get("status") == "success"
    )

    errors = sum(
        1
        for x in results.values()
        if x.get("status") == "error"
    )

    print(
        f"Successful : {success}"
    )

    print(
        f"Errors     : {errors}"
    )

    print(
        f"Output     : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()