"""Schedule change requests made by students."""

import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ChangeRequestStatus, db_enum


class ChangeRequest(Base):
    """Request of a student to move from one schedule to another.

    A pending request has neither resolution date nor target; an accepted one
    has both; a rejected one has a resolution date and no target (RN-17).
    """

    __tablename__ = "change_requests"
    __table_args__ = (
        CheckConstraint(
            "(status = 'pendiente' AND resolved_at IS NULL AND target_schedule_id IS NULL)"
            " OR (status = 'aceptada' AND resolved_at IS NOT NULL"
            " AND target_schedule_id IS NOT NULL)"
            " OR (status = 'rechazada' AND resolved_at IS NOT NULL"
            " AND target_schedule_id IS NULL)",
            name="status_consistent",
        ),
        CheckConstraint("resolved_at >= requested_at", name="resolved_after_requested"),
        CheckConstraint("target_schedule_id <> origin_schedule_id", name="target_differs"),
        CheckConstraint(
            "support_coordinator_id <> attending_coordinator_id", name="support_differs"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    requested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[ChangeRequestStatus] = mapped_column(
        db_enum(ChangeRequestStatus, "change_request_status"),
        server_default=ChangeRequestStatus.PENDING.value,
    )
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    origin_schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), index=True)
    target_schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id"), index=True
    )
    attending_coordinator_id: Mapped[int] = mapped_column(
        ForeignKey("coordinators.id"), index=True
    )
    support_coordinator_id: Mapped[int | None] = mapped_column(
        ForeignKey("coordinators.id"), index=True
    )
