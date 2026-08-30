import json
import re
from pathlib import Path
from difflib import SequenceMatcher

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Content, Broadcast, Channel


DATABASE_URL = "sqlite:///data/tvguide.db"

SEARCH_FILE = Path("data/tmdb_search_results.json")
OUTPUT_FILE = Path("data/tmdb_matches_v2.json")


# ============================================================
# Channel type hints
# ============================================================

CHANNEL_HINTS = {
    "روتانا سينما السعودية": "movie",
    "روتانا سينما مصر": "movie",
    "روتانا كوميدي": "movie",
    "روتانا كلاسيك": "movie",
    "روتانا دراما": "series",
    "الرسالة": "program",
    "إل بي سي": "mixed",
    "روتانا خليجية": "mixed",
}


# ============================================================
# Arabic normalization
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower().strip()

    # Remove tashkeel
    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

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

    # Arabic digits -> English digits
    arabic_digits = {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }

    for old, new in arabic_digits.items():
        text = text.replace(old, new)

    # Tatweel
    text = text.replace("ـ", "")

    # Punctuation
    text = re.sub(
        r"[^\w\u0600-\u06FF]+",
        " ",
        text,
    )

    # Extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# Similarity
# ============================================================

def similarity(a, b):

    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


# ============================================================
# Detect title hints
# ============================================================

def title_hint(title):

    n = normalize(title)

    # Examples:
    # صبايا ج5
    # الكندوش الجزء الثاني
    # مسلسل الموسم الأول

    if re.search(r"\bج[0-9]+\b", n):
        return "series"

    if "جزء" in n:
        return "series"

    if "الموسم" in n:
        return "series"

    if re.search(r"\bموسم\b", n):
        return "series"

    return None


# ============================================================
# Score candidate
# ============================================================

def score_candidate(
    source_title,
    candidate,
    kind,
    channel_hint,
):

    if kind == "movie":

        title = (
            candidate.get("title")
            or ""
        )

        original = (
            candidate.get("original_title")
            or ""
        )

        release_date = (
            candidate.get("release_date")
            or ""
        )

    else:

        title = (
            candidate.get("name")
            or ""
        )

        original = (
            candidate.get("original_name")
            or ""
        )

        release_date = (
            candidate.get("first_air_date")
            or ""
        )

    title_score = similarity(
        source_title,
        title,
    )

    original_score = similarity(
        source_title,
        original,
    )

    best_similarity = max(
        title_score,
        original_score,
    )

    # Base score
    score = best_similarity * 70

    reasons = []

    source_norm = normalize(
        source_title
    )

    title_norm = normalize(
        title
    )

    original_norm = normalize(
        original
    )

    # --------------------------------------------------------
    # Exact title
    # --------------------------------------------------------

    if source_norm == title_norm:

        score += 25

        reasons.append(
            "exact title"
        )

    elif source_norm == original_norm:

        score += 20

        reasons.append(
            "exact original title"
        )

    # --------------------------------------------------------
    # Channel type
    # --------------------------------------------------------

    if channel_hint == kind:

        score += 15

        reasons.append(
            "channel type matches"
        )

    elif channel_hint in (
        "movie",
        "series",
    ):

        score -= 20

        reasons.append(
            "channel type mismatch"
        )

    # --------------------------------------------------------
    # Title type hint
    # --------------------------------------------------------

    hint = title_hint(
        source_title
    )

    if hint == kind:

        score += 10

        reasons.append(
            "title indicates same type"
        )

    elif hint and hint != kind:

        score -= 20

        reasons.append(
            "title indicates different type"
        )

    # --------------------------------------------------------
    # Release year information
    # --------------------------------------------------------

    if release_date:

        reasons.append(
            f"release year {release_date[:4]}"
        )

    return {
        "tmdb_id": candidate.get("id"),
        "type": kind,
        "title": title,
        "original_title": original,
        "release_date": release_date,
        "poster_path": candidate.get(
            "poster_path"
        ),
        "backdrop_path": candidate.get(
            "backdrop_path"
        ),
        "overview": candidate.get(
            "overview"
        ),
        "popularity": candidate.get(
            "popularity"
        ),
        "score": round(
            max(
                0,
                min(
                    score,
                    100,
                ),
            ),
            2,
        ),
        "reasons": reasons,
    }


# ============================================================
# Classification
# ============================================================

def classify(candidates):

    if not candidates:
        return "NO_MATCH"

    best = candidates[0]

    second = (
        candidates[1]
        if len(candidates) > 1
        else None
    )

    best_score = best["score"]

    second_score = (
        second["score"]
        if second
        else 0
    )

    gap = (
        best_score
        - second_score
    )

    # --------------------------------------------------------
    # Very strong match
    # --------------------------------------------------------

    if (
        best_score >= 92
        and gap >= 12
    ):
        return "AUTO_MATCH"

    # --------------------------------------------------------
    # Very strong result with only one candidate
    # --------------------------------------------------------

    if (
        best_score >= 90
        and second is None
    ):
        return "AUTO_MATCH"

    # --------------------------------------------------------
    # Strong but ambiguous
    # --------------------------------------------------------

    if (
        best_score >= 85
        and gap < 12
    ):
        return "REVIEW"

    # --------------------------------------------------------
    # Moderate confidence
    # --------------------------------------------------------

    if best_score >= 65:
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

    output = {}

    stats = {
        "AUTO_MATCH": 0,
        "REVIEW": 0,
        "NO_MATCH": 0,
        "ERROR": 0,
    }

    with Session(engine) as session:

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        contents = session.scalars(
            select(Content)
            .order_by(Content.id)
        ).all()

        # ----------------------------------------------------
        # Channels
        # ----------------------------------------------------

        channels = session.scalars(
            select(Channel)
        ).all()

        channel_names = {
            channel.id: (
                channel.name_ar
                or channel.name
                or channel.name_en
                or ""
            )
            for channel in channels
        }

        # ----------------------------------------------------
        # Broadcasts
        # ----------------------------------------------------

        broadcasts = session.scalars(
            select(Broadcast)
        ).all()

        channel_by_content = {}

        for broadcast in broadcasts:

            if broadcast.content_id is None:
                continue

            channel_name = channel_names.get(
                broadcast.channel_id
            )

            if not channel_name:
                continue

            channel_by_content.setdefault(
                broadcast.content_id,
                set(),
            ).add(
                channel_name
            )

        print(
            f"Matching {len(contents)} "
            f"content records..."
        )

        # ====================================================
        # Process Content
        # ====================================================

        for index, content in enumerate(
            contents,
            start=1,
        ):

            title = content.title_ar

            print()
            print(
                f"[{index}/{len(contents)}] "
                f"{title}"
            )

            channels_for_content = (
                channel_by_content.get(
                    content.id,
                    set(),
                )
            )

            # ------------------------------------------------
            # Determine channel hint
            # ------------------------------------------------

            hints = []

            for channel_name in (
                channels_for_content
            ):

                hint = CHANNEL_HINTS.get(
                    channel_name
                )

                if hint:
                    hints.append(hint)

            if "movie" in hints:

                channel_hint = "movie"

            elif "series" in hints:

                channel_hint = "series"

            elif "program" in hints:

                channel_hint = "program"

            else:

                channel_hint = "mixed"

            # ------------------------------------------------
            # TMDB search result
            # ------------------------------------------------

            search = raw.get(
                str(content.id)
            )

            if not search:

                print(
                    "  ERROR: search result missing"
                )

                stats["ERROR"] += 1

                continue

            if search.get("status") != "success":

                print(
                    "  ERROR: TMDB search failed"
                )

                stats["ERROR"] += 1

                continue

            candidates = []

            # ------------------------------------------------
            # Movie candidates
            # ------------------------------------------------

            for item in search.get(
                "movies",
                [],
            ):

                candidates.append(
                    score_candidate(
                        title,
                        item,
                        "movie",
                        channel_hint,
                    )
                )

            # ------------------------------------------------
            # TV candidates
            # ------------------------------------------------

            for item in search.get(
                "tv",
                [],
            ):

                candidates.append(
                    score_candidate(
                        title,
                        item,
                        "series",
                        channel_hint,
                    )
                )

            # ------------------------------------------------
            # Sort
            # ------------------------------------------------

            candidates.sort(
                key=lambda x: x["score"],
                reverse=True,
            )

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            status = classify(
                candidates
            )

            stats[status] += 1

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

            # ------------------------------------------------
            # Save result
            # ------------------------------------------------

            output[
                str(content.id)
            ] = {
                "content_id": content.id,
                "source_title": title,
                "channels": sorted(
                    channels_for_content
                ),
                "channel_hint": channel_hint,
                "status": status,
                "best_match": best,
                "second_match": second,
                "candidates": candidates[:10],
            }

            # ------------------------------------------------
            # Console
            # ------------------------------------------------

            if best:

                print(
                    f"  → {status} | "
                    f"{best['type']} | "
                    f"{best['title']} | "
                    f"TMDB={best['tmdb_id']} | "
                    f"Score={best['score']}"
                )

            else:

                print(
                    f"  → {status}"
                )

    # ========================================================
    # Save
    # ========================================================

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
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
    print("TMDB MATCHING V2 COMPLETE")
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