"""Content block bank."""

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ActivityType, ComplexityLevel, db_enum


class ContentBlock(Base):
    """Content block created by a coordinator.

    Two blocks with the same description, subject and activity type are
    duplicates (RN-03); the complexity does not distinguish them.
    """

    __tablename__ = "content_blocks"
    __table_args__ = (UniqueConstraint("subject_id", "description", "activity_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    description: Mapped[str] = mapped_column(Text)
    activity_type: Mapped[ActivityType] = mapped_column(db_enum(ActivityType, "activity_type"))
    complexity: Mapped[ComplexityLevel] = mapped_column(
        db_enum(ComplexityLevel, "complexity_level")
    )
    creator_id: Mapped[int] = mapped_column(ForeignKey("coordinators.id"), index=True)
