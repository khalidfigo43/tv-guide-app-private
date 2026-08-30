from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


DATABASE_URL = "sqlite:///data/tvguide.db"


class Base(DeclarativeBase):
    pass


# ============================================================
# CHANNELS
# ============================================================

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    name_ar: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    name_en: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_channel_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    transmissions = relationship(
        "ChannelTransmission",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    broadcasts = relationship(
        "Broadcast",
        back_populates="channel",
        cascade="all, delete-orphan",
    )


# ============================================================
# CHANNEL TRANSMISSIONS
# ============================================================

class ChannelTransmission(Base):
    __tablename__ = "channel_transmissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id"),
        nullable=False,
    )

    satellite: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    frequency: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    polarization: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    symbol_rate: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    fec: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    channel = relationship(
        "Channel",
        back_populates="transmissions",
    )


# ============================================================
# CONTENT
# ============================================================

class Content(Base):
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    title_ar: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    title_en: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    original_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    normalized_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    release_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    poster_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    backdrop_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    overview_ar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    overview_en: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rating: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    external_ids = relationship(
        "ContentExternalId",
        back_populates="content",
        cascade="all, delete-orphan",
    )

    aliases = relationship(
        "ContentAlias",
        back_populates="content",
        cascade="all, delete-orphan",
    )

    broadcasts = relationship(
        "Broadcast",
        back_populates="content",
        cascade="all, delete-orphan",
    )


# ============================================================
# EXTERNAL IDS
# ============================================================

class ContentExternalId(Base):
    __tablename__ = "content_external_ids"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    content = relationship(
        "Content",
        back_populates="external_ids",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            name="uq_provider_external_id",
        ),
    )


# ============================================================
# CONTENT ALIASES
# ============================================================

class ContentAlias(Base):
    __tablename__ = "content_aliases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    normalized_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    content = relationship(
        "Content",
        back_populates="aliases",
    )


# ============================================================
# BROADCASTS
# ============================================================

class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id"),
        nullable=False,
    )

    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id"),
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_item_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    end_datetime: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    content = relationship(
        "Content",
        back_populates="broadcasts",
    )

    channel = relationship(
        "Channel",
        back_populates="broadcasts",
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def create_database():
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    Base.metadata.create_all(engine)

    return engine


if __name__ == "__main__":
    Path("data").mkdir(
        parents=True,
        exist_ok=True,
    )

    engine = create_database()

    print("Database created successfully.")
    print("Location: data/tvguide.db")