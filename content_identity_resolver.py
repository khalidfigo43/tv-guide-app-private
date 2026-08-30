import json
import re
from pathlib import Path
from difflib import SequenceMatcher

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Content, Broadcast, Channel


DATABASE_URL = "sqlite:///data/tvguide.db"

TMDB_FILE = Path(
    "data/tmdb_matches_v2.json"
)

OUTPUT_FILE = Path(
    "data/content_identity_resolution.json"
)


# ============================================================
# CHANNEL PROFILES
# ============================================================

CHANNEL_PROFILES = {
    "روتانا سينما السعودية": {
        "movie": 1.00,
        "series": 0.05,
        "program": 0.00,
    },

    "روتانا سينما مصر": {
        "movie": 1.00,
        "series": 0.05,
        "program": 0.00,
    },

    "روتانا كوميدي": {
        "movie": 0.95,
        "series": 0.10,
        "program": 0.00,
    },

    "روتانا كلاسيك": {
        "movie": 0.95,
        "series": 0.05,
        "program": 0.00,
    },

    "روتانا دراما": {
        "movie": 0.10,
        "series": 0.95,
        "program": 0.05,
    },

    "إل بي سي": {
        "movie": 0.50,
        "series": 0.70,
        "program": 0.60,
    },

    "روتانا خليجية": {
        "movie": 0.40,
        "series": 0.60,
        "program": 0.70,
    },

    "الرسالة": {
        "movie": 0.00,
        "series": 0.10,
        "program": 1.00,
    },
}


# ============================================================
# NORMALIZATION
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

    # Arabic digits
    digits = {
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

    for old, new in digits.items():
        text = text.replace(old, new)

    text = text.replace("ـ", "")

    text = re.sub(
        r"[^\w\u0600-\u06FF]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


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
# TITLE HINTS
# ============================================================

def title_type_hint(title):

    n = normalize(title)

    if re.search(
        r"\bج[0-9]+\b",
        n,
    ):
        return "series"

    if "جزء" in n:
        return "series"

    if "الموسم" in n:
        return "series"

    if "موسم" in n:
        return "series"

    return None


# ============================================================
# CHANNEL TYPE
# ============================================================

def get_channel_profile(channels):

    profile = {
        "movie": 0.0,
        "series": 0.0,
        "program": 0.0,
    }

    matched = []

    for channel in channels:

        channel_profile = CHANNEL_PROFILES.get(
            channel
        )

        if not channel_profile:
            continue

        matched.append(channel)

        for kind in profile:
            profile[kind] += (
                channel_profile[kind]
            )

    if not matched:
        return "unknown", profile

    best_type = max(
        profile,
        key=profile.get,
    )

    return best_type, profile


# ============================================================
# CANDIDATE SCORING
# ============================================================

def score_candidate(
    source_title,
    candidate,
    channels,
    channel_type,
):

    kind = candidate.get(
        "type"
    )

    candidate_title = (
        candidate.get("title")
        or ""
    )

    original_title = (
        candidate.get("original_title")
        or ""
    )

    # --------------------------------------------------------
    # Base score from V2
    # --------------------------------------------------------

    base_score = float(
        candidate.get(
            "score",
            0,
        )
    )

    score = base_score

    reasons = list(
        candidate.get(
            "reasons",
            [],
        )
    )

    # --------------------------------------------------------
    # Channel profile
    # --------------------------------------------------------

    profile = {}

    for channel in channels:

        p = CHANNEL_PROFILES.get(
            channel
        )

        if not p:
            continue

        for candidate_kind in (
            "movie",
            "series",
            "program",
        ):

            profile[
                candidate_kind
            ] = max(
                profile.get(
                    candidate_kind,
                    0,
                ),
                p.get(
                    candidate_kind,
                    0,
                ),
            )

    channel_preference = profile.get(
        kind,
        0,
    )

    if channel_preference >= 0.9:

        score += 8

        reasons.append(
            "strong channel preference"
        )

    elif channel_preference >= 0.6:

        score += 4

        reasons.append(
            "channel preference"
        )

    elif channel_preference <= 0.1:

        score -= 15

        reasons.append(
            "channel type unlikely"
        )

    # --------------------------------------------------------
    # Title hint
    # --------------------------------------------------------

    hint = title_type_hint(
        source_title
    )

    if hint == kind:

        score += 10

        reasons.append(
            "title type matches"
        )

    elif hint and hint != kind:

        score -= 15

        reasons.append(
            "title type mismatch"
        )

    # --------------------------------------------------------
    # Exact title
    # --------------------------------------------------------

    if normalize(
        source_title
    ) == normalize(
        candidate_title
    ):

        reasons.append(
            "exact normalized title"
        )

    # --------------------------------------------------------
    # Keep within range
    # --------------------------------------------------------

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    return {
        **candidate,
        "resolver_score": round(
            score,
            2,
        ),
        "resolver_reasons": reasons,
    }


# ============================================================
# RESOLVE
# ============================================================

def resolve(candidates):

    if not candidates:
        return (
            "UNRESOLVED",
            None,
            None,
        )

    candidates.sort(
        key=lambda x: x[
            "resolver_score"
        ],
        reverse=True,
    )

    best = candidates[0]

    second = (
        candidates[1]
        if len(candidates) > 1
        else None
    )

    best_score = best[
        "resolver_score"
    ]

    second_score = (
        second["resolver_score"]
        if second
        else 0
    )

    gap = (
        best_score
        - second_score
    )

    # --------------------------------------------------------
    # Very strong unique match
    # --------------------------------------------------------

    if (
        best_score >= 95
        and gap >= 15
    ):
        return (
            "CONFIRMED",
            best,
            second,
        )

    # --------------------------------------------------------
    # Strong unique match
    # --------------------------------------------------------

    if (
        best_score >= 90
        and gap >= 20
    ):
        return (
            "CONFIRMED",
            best,
            second,
        )

    # --------------------------------------------------------
    # Ambiguous
    # --------------------------------------------------------

    if (
        best_score >= 80
        and gap < 15
    ):
        return (
            "REVIEW",
            best,
            second,
        )

    # --------------------------------------------------------
    # Medium confidence
    # --------------------------------------------------------

    if best_score >= 65:
        return (
            "REVIEW",
            best,
            second,
        )

    return (
        "UNRESOLVED",
        best,
        second,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not TMDB_FILE.exists():

        print(
            f"Missing: {TMDB_FILE}"
        )

        return

    tmdb_data = json.loads(
        TMDB_FILE.read_text(
            encoding="utf-8"
        )
    )

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    output = {}

    stats = {
        "CONFIRMED": 0,
        "REVIEW": 0,
        "UNRESOLVED": 0,
        "ERROR": 0,
    }

    with Session(engine) as db:

        contents = db.scalars(
            select(Content)
            .order_by(Content.id)
        ).all()

        channels = db.scalars(
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

        broadcasts = db.scalars(
            select(Broadcast)
        ).all()

        content_channels = {}

        for broadcast in broadcasts:

            if broadcast.content_id is None:
                continue

            channel_name = channel_names.get(
                broadcast.channel_id
            )

            if not channel_name:
                continue

            content_channels.setdefault(
                broadcast.content_id,
                set(),
            ).add(
                channel_name
            )

        print(
            f"Resolving {len(contents)} "
            f"content records..."
        )

        # ====================================================
        # CONTENT
        # ====================================================

        for index, content in enumerate(
            contents,
            start=1,
        ):

            content_id = str(
                content.id
            )

            title = content.title_ar

            channels_for_content = (
                sorted(
                    content_channels.get(
                        content.id,
                        set(),
                    )
                )
            )

            channel_type, profile = (
                get_channel_profile(
                    channels_for_content
                )
            )

            print()
            print(
                f"[{index}/{len(contents)}] "
                f"{title}"
            )

            print(
                f"  Channels: "
                f"{', '.join(channels_for_content)}"
            )

            print(
                f"  Profile: "
                f"{channel_type}"
            )

            tmdb = tmdb_data.get(
                content_id
            )

            if not tmdb:

                print(
                    "  → UNRESOLVED "
                    "(no TMDB data)"
                )

                stats[
                    "UNRESOLVED"
                ] += 1

                output[
                    content_id
                ] = {
                    "content_id": content.id,
                    "source_title": title,
                    "channels": channels_for_content,
                    "channel_type": channel_type,
                    "status": "UNRESOLVED",
                    "best_match": None,
                    "second_match": None,
                }

                continue

            raw_candidates = tmdb.get(
                "candidates",
                [],
            )

            scored = []

            for candidate in raw_candidates:

                scored.append(
                    score_candidate(
                        title,
                        candidate,
                        channels_for_content,
                        channel_type,
                    )
                )

            status, best, second = resolve(
                scored
            )

            stats[status] += 1

            output[
                content_id
            ] = {
                "content_id": content.id,
                "source_title": title,
                "channels": channels_for_content,
                "channel_type": channel_type,
                "channel_profile": profile,
                "status": status,
                "best_match": best,
                "second_match": second,
                "candidates": scored,
            }

            if best:

                print(
                    f"  → {status} | "
                    f"{best.get('type')} | "
                    f"{best.get('title')} | "
                    f"TMDB={best.get('tmdb_id')} | "
                    f"Score="
                    f"{best.get('resolver_score')}"
                )

            else:

                print(
                    f"  → {status}"
                )

    # ========================================================
    # SAVE
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
    # SUMMARY
    # ========================================================

    print()
    print("=" * 80)
    print(
        "CONTENT IDENTITY RESOLUTION COMPLETE"
    )
    print("=" * 80)

    print(
        f"CONFIRMED  : "
        f"{stats['CONFIRMED']}"
    )

    print(
        f"REVIEW     : "
        f"{stats['REVIEW']}"
    )

    print(
        f"UNRESOLVED : "
        f"{stats['UNRESOLVED']}"
    )

    print(
        f"ERROR      : "
        f"{stats['ERROR']}"
    )

    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()
    print(
        "NO DATABASE CHANGES WERE MADE."
    )


if __name__ == "__main__":
    main()