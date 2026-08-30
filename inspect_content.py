from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Content


engine = create_engine(
    "sqlite:///data/tvguide.db"
)


with Session(engine) as session:

    contents = session.scalars(
        select(Content).order_by(Content.id)
    ).all()

    print("=" * 80)
    print("CURRENT CONTENT")
    print("=" * 80)

    for content in contents:

        print(
            f'{content.id:4} | '
            f'{content.content_type:8} | '
            f'{content.title_ar}'
        )

    print()
    print("=" * 80)
    print(f"TOTAL: {len(contents)}")
    print("=" * 80)