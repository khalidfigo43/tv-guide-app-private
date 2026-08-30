import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import (
    Channel,
    Content,
    ContentExternalId,
    Broadcast,
)


DATABASE_URL = "sqlite:///data/tvguide.db"
SCHEDULE_FILE = Path("data/rotana_schedule.json")


def normalize_title(title):
    """
    Normalization مبدئية للعناوين العربية.
    سنطورها لاحقًا في Matching Engine.
    """

    if not title:
        return ""

    title = title.strip()

    # إزالة التشكيل
    title = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        title,
    )

    # توحيد أشكال الألف
    title = title.replace("أ", "ا")
    title = title.replace("إ", "ا")
    title = title.replace("آ", "ا")

    # توحيد الياء والألف المقصورة
    title = title.replace("ى", "ي")

    # إزالة التطويل
    title = title.replace("ـ", "")

    # المسافات المتكررة
    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip().lower()


def parse_datetime(date, time):
    return datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M",
    )


def load_schedule():
    if not SCHEDULE_FILE.exists():
        raise FileNotFoundError(
            f"Schedule file not found: {SCHEDULE_FILE}"
        )

    return json.loads(
        SCHEDULE_FILE.read_text(
            encoding="utf-8"
        )
    )


def get_or_create_channel(
    session,
    channel_id,
    channel_name,
):
    channel = session.scalar(
        select(Channel).where(
            Channel.source == "rotana",
            Channel.source_channel_id == str(channel_id),
        )
    )

    if channel:
        return channel

    channel = Channel(
        name=channel_name,
        name_ar=channel_name,
        source="rotana",
        source_channel_id=str(channel_id),
    )

    session.add(channel)
    session.flush()

    return channel


def get_or_create_content(
    session,
    title,
):
    normalized = normalize_title(title)

    content = session.scalar(
        select(Content).where(
            Content.normalized_title == normalized
        )
    )

    if content:
        return content

    content = Content(
        content_type="unknown",
        title_ar=title,
        normalized_title=normalized,
    )

    session.add(content)
    session.flush()

    return content


def ensure_external_id(
    session,
    content,
    source_item_id,
):
    external_id = str(source_item_id)

    existing = session.scalar(
        select(ContentExternalId).where(
            ContentExternalId.provider == "rotana",
            ContentExternalId.external_id == external_id,
        )
    )

    if existing:
        return existing

    external = ContentExternalId(
        content_id=content.id,
        provider="rotana",
        external_id=external_id,
        external_type="schedule_item",
    )

    session.add(external)

    return external


def import_schedule():
    data = load_schedule()

    programs = data.get("data", [])

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    created_channels = 0
    created_content = 0
    created_broadcasts = 0
    skipped_broadcasts = 0

    with Session(engine) as session:

        # -----------------------------------------------------
        # Process programs
        # -----------------------------------------------------

        for index, program in enumerate(programs, 1):

            channel_id = program["channelId"]
            channel_name = program["channelName"]

            title = program["title"]

            source_item_id = str(
                program["sourceItemId"]
            )

            date = program["date"]
            start_time = program["startTime"]

            end_time = program.get("endTime")
            end_date = program.get("endDate")

            # -------------------------------------------------
            # Channel
            # -------------------------------------------------

            channel_before = session.scalar(
                select(Channel).where(
                    Channel.source == "rotana",
                    Channel.source_channel_id
                    == str(channel_id),
                )
            )

            channel = get_or_create_channel(
                session,
                channel_id,
                channel_name,
            )

            if channel_before is None:
                created_channels += 1

            # -------------------------------------------------
            # Content
            # -------------------------------------------------

            content_before = session.scalar(
                select(Content).where(
                    Content.normalized_title
                    == normalize_title(title)
                )
            )

            content = get_or_create_content(
                session,
                title,
            )

            if content_before is None:
                created_content += 1

            # -------------------------------------------------
            # External ID
            # -------------------------------------------------

            ensure_external_id(
                session,
                content,
                source_item_id,
            )

            # -------------------------------------------------
            # Broadcast datetime
            # -------------------------------------------------

            start_datetime = parse_datetime(
                date,
                start_time,
            )

            end_datetime = None

            if end_time and end_date:
                end_datetime = parse_datetime(
                    end_date,
                    end_time,
                )

            # -------------------------------------------------
            # Check duplicate broadcast
            # -------------------------------------------------

            existing_broadcast = session.scalar(
                select(Broadcast).where(
                    Broadcast.channel_id == channel.id,
                    Broadcast.source == "rotana",
                    Broadcast.source_item_id
                    == source_item_id,
                )
            )

            if existing_broadcast:
                skipped_broadcasts += 1
                continue

            # -------------------------------------------------
            # Create broadcast
            # -------------------------------------------------

            broadcast = Broadcast(
                content_id=content.id,
                channel_id=channel.id,
                source="rotana",
                source_item_id=source_item_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

            session.add(broadcast)
            created_broadcasts += 1

            # -------------------------------------------------
            # Commit every 100 records
            # -------------------------------------------------

            if index % 100 == 0:
                session.commit()

                print(
                    f"Processed "
                    f"{index}/{len(programs)}"
                )

        session.commit()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("ROTANA IMPORT COMPLETE")
    print("=" * 70)

    print(
        f"Channels created    : "
        f"{created_channels}"
    )

    print(
        f"Content created     : "
        f"{created_content}"
    )

    print(
        f"Broadcasts created  : "
        f"{created_broadcasts}"
    )

    print(
        f"Broadcasts skipped  : "
        f"{skipped_broadcasts}"
    )

    print()
    print("Database:")
    print("data/tvguide.db")


if __name__ == "__main__":
    import_schedule()