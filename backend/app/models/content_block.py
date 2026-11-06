"""Content block bank."""

from sqlalchemy import ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ActivityType, ComplexityLevel, db_enum


class ContentBlock(Base):
    """Content block created by a coordinator.

    Two blocks with the same description, subject and activity type are
    duplicates (RN-03); the complexity does not distinguish them. The
    description is compared by the md5 of its trimmed, lower-cased text, so
    the unique index stays small (a btree row is limited to about 2.7 KB) and
    ``'x'``, ``'x '`` and ``'X'`` count as the same block. ``lower`` runs with
    the ICU ``und-x-icu`` collation so accented letters fold too regardless of
    the database collation (``'Á'`` equals ``'á'`` even under ``C``).
    """

    __tablename__ = "content_blocks"
    __table_args__ = (
        Index(
            "uq_content_blocks_subject_activity_description",
            "subject_id",
            "activity_type",
            text('md5(lower(btrim(description) COLLATE "und-x-icu"))'),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    description: Mapped[str] = mapped_column(Text)
    activity_type: Mapped[ActivityType] = mapped_column(db_enum(ActivityType, "activity_type"))
    complexity: Mapped[ComplexityLevel] = mapped_column(
        db_enum(ComplexityLevel, "complexity_level")
    )
    creator_id: Mapped[int] = mapped_column(ForeignKey("coordinators.id"), index=True)
