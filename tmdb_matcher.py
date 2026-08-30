import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Content


DATABASE_URL = "sqlite:///data/tvguide.db"

SEARCH_FILE = Path(
    "data/tmdb_search_results.json"
)

OUTPUT_FILE = Path(
    "data/tmdb_matches.json"
)


# ============================================================
# Arabic normalization
# ============================================================

def normalize_arabic(text):
    if not text:
        return ""

    text = str(text).strip().lower()

    # Remove tashkeel
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    # Normalize Arabic letters
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove tatweel
    text = text.replace("ـ", "")

    # Arabic/English punctuation → spaces
    text = re.sub(
        r"[^\w\u0600-\u06FF]+",
        " ",
        text,
    )

    # Remove extra whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# Token normalization
# ============================================================

def tokens(text):
    normalized = normalize_arabic(text)

    if not normalized:
        return set()

    return set(
        token
        for token in normalized.split()
        if len(token) > 1
    )


# ============================================================
# Similarity
# ============================================================

def similarity(a, b):
    a_norm = normalize_arabic(a)
    b_norm = normalize_arabic(b)

    if not a_norm or not b_norm:
        return 0.0

    if a_norm == b_norm:
        return 1.0

    sequence_score = SequenceMatcher(
        None,
        a_norm,
        b_norm,
    ).ratio()

    a_tokens = tokens(a)
    b_tokens = tokens(b)

    if a_tokens and b_tokens:
        intersection = len(
            a_tokens & b_tokens
        )

        union = len(
            a_tokens | b_tokens
        )

        token_score = (
            intersection / union
        )
    else:
        token_score = 0.0

    return max(
        sequence_score,
        token_score,
    )


# ============================================================
# Detect content hints from title
# ============================================================

def content_hint(title):

    normalized = normalize_arabic(title)

    series_keywords = [
        "ج1",
        "ج2",
        "ج3",
        "ج4",
        "ج5",
        "ج6",
        "جزء",
        "الموسم",
        "موسم",
    ]

    for keyword in series_keywords:
        if normalize_arabic(keyword) in normalized:
            return "series"

    return None


# ============================================================
# Score candidate
# ============================================================

def score_candidate(
    source_title,
    candidate,
    candidate_type,
):

    if candidate_type == "movie":

        title = candidate.get(
            "title"
        )

        original_title = candidate.get(
            "original_title"
        )

        release_date = candidate.get(
            "release_date"
        )

    else:

        title = candidate.get(
            "name"
        )

        original_title = candidate.get(
            "original_name"
        )

        release_date = candidate.get(
            "first_air_date"
        )

    title_score = similarity(
        source_title,
        title,
    )

    original_score = similarity(
        source_title,
        original_title,
    )

    best_title_score = max(
        title_score,
        original_score,
    )

    score = best_title_score * 100

    reasons = []

    if normalize_arabic(
        source_title
    ) == normalize_arabic(title):

        score += 25

        reasons.append(
            "exact Arabic title"
        )

    elif normalize_arabic(
        source_title
    ) == normalize_arabic(
        original_title
    ):

        score += 20

        reasons.append(
            "exact original title"
        )

    if best_title_score >= 0.90:
        reasons.append(
            "very high title similarity"
        )

    elif best_title_score >= 0.75:
        reasons.append(
            "high title similarity"
        )

    elif best_title_score >= 0.60:
        reasons.append(
            "moderate title similarity"
        )

    return {
        "tmdb_id": candidate.get("id"),
        "type": candidate_type,
        "title": title,
        "original_title": original_title,
        "release_date": release_date,
        "poster_path": candidate.get(
            "poster_path"
        ),
        "overview": candidate.get(
            "overview"
        ),
        "popularity": candidate.get(
            "popularity"
        ),
        "score": round(
            min(score, 100),
            2,
        ),
        "reasons": reasons,
    }


# ============================================================
# Decide confidence
# ============================================================

def classify_match(
    best,
    second,
):

    if not best:
        return "NO_MATCH"

    score = best["score"]

    second_score = (
        second["score"]
        if second
        else 0
    )

    gap = score - second_score

    # Very strong match
    if score >= 95 and gap >= 10:
        return "AUTO_MATCH"

    # Strong exact title
    if score >= 90 and gap >= 5:
        return "AUTO_MATCH"

    # Needs human review
    if score >= 65:
        return "REVIEW"

    return "NO_MATCH"


# ============================================================
# Main
# ============================================================

def main():

    if not SEARCH_FILE.exists():

        print(
            f"Missing file: {SEARCH_FILE}"
        )

        return

    raw = json.loads(
        SEARCH_FILE.read_text(
            encoding="utf-8"
        )
    )

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    results = {}

    stats = {
        "AUTO_MATCH": 0,
        "REVIEW": 0,
        "NO_MATCH": 0,
        "ERROR": 0,
    }

    with Session(engine) as session:

        contents = session.scalars(
            select(Content)
            .order_by(Content.id)
        ).all()

        print(
            f"Matching {len(contents)} "
            f"content records..."
        )

        for index, content in enumerate(
            contents,
            start=1,
        ):

            key = str(content.id)

            title = content.title_ar

            search_result = raw.get(
                key
            )

            print()
            print(
                f"[{index}/{len(contents)}] "
                f"{title}"
            )

            if not search_result:

                print(
                    "  ERROR: no TMDB search result"
                )

                stats["ERROR"] += 1

                continue

            if search_result.get(
                "status"
            ) != "success":

                print(
                    "  ERROR: search failed"
                )

                stats["ERROR"] += 1

                continue

            candidates = []

            # ------------------------------------------------
            # Movie candidates
            # ------------------------------------------------

            for movie in search_result.get(
                "movies",
                [],
            ):

                candidates.append(
                    score_candidate(
                        title,
                        movie,
                        "movie",
                    )
                )

            # ------------------------------------------------
            # TV candidates
            # ------------------------------------------------

            for tv in search_result.get(
                "tv",
                [],
            ):

                candidates.append(
                    score_candidate(
                        title,
                        tv,
                        "series",
                    )
                )

            # ------------------------------------------------
            # Sort
            # ------------------------------------------------

            candidates.sort(
                key=lambda x: x["score"],
                reverse=True,
            )

            best = (
                candidates[0]
                if candidates
                else None
            )

            second = (
                candidates[1]
                if len(candidates) > 1
                else None
            )

            status = classify_match(
                best,
                second,
            )

            stats[status] += 1

            results[key] = {
                "content_id": content.id,
                "source_title": title,
                "status": status,
                "best_match": best,
                "second_match": second,
                "candidate_count": len(
                    candidates
                ),
            }

            # ------------------------------------------------
            # Console output
            # ------------------------------------------------

            if best:

                print(
                    f"  → {status}"
                )

                print(
                    f"  → "
                    f"{best['type']} | "
                    f"{best['title']} | "
                    f"TMDB={best['tmdb_id']} | "
                    f"Score={best['score']}"
                )

            else:

                print(
                    "  → NO_MATCH"
                )

    # ========================================================
    # Save
    # ========================================================

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # Summary
    # ========================================================

    print()
    print("=" * 80)
    print("TMDB MATCHING COMPLETE")
    print("=" * 80)

    print(
        f"AUTO_MATCH : "
        f"{stats['AUTO_MATCH']}"
    )

    print(
        f"REVIEW     : "
        f"{stats['REVIEW']}"
    )

    print(
        f"NO_MATCH   : "
        f"{stats['NO_MATCH']}"
    )

    print(
        f"ERROR      : "
        f"{stats['ERROR']}"
    )

    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()