"""Schedules, their sessions, student assignments and attendance."""

import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AttendanceStatus, ReviewDecision, db_enum

RATIO = Numeric(4, 3)


class Schedule(Base):
    """Generated schedule of a program for a semester.

    The generation parameters, the coordinator validation, the department
    head review and the replaced schedule are stored in the same row because
    they all depend on the schedule. A schedule is final when its review
    decision is ``aprobado``.
    """

    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint("theory_ratio BETWEEN 0 AND 1", name="theory_ratio_range"),
        CheckConstraint("practice_ratio BETWEEN 0 AND 1", name="practice_ratio_range"),
        CheckConstraint("lab_ratio BETWEEN 0 AND 1", name="lab_ratio_range"),
        CheckConstraint(
            "theory_ratio + practice_ratio + lab_ratio = 1", name="ratios_sum_one"
        ),
        CheckConstraint("subject_coverage BETWEEN 0 AND 1", name="subject_coverage_range"),
        CheckConstraint("block_count > 0", name="block_count_positive"),
        CheckConstraint("previous_schedule_id <> id", name="not_replacing_itself"),
        CheckConstraint(
            "(validator_id IS NULL) = (validated_at IS NULL)", name="validation_complete"
        ),
        CheckConstraint(
            "validation_notes IS NULL OR validator_id IS NOT NULL",
            name="validation_notes_valid",
        ),
        CheckConstraint("validated_at >= created_at", name="validated_after_creation"),
        CheckConstraint(
            "(head_id IS NULL AND reviewed_at IS NULL AND review_decision IS NULL)"
            " OR (head_id IS NOT NULL AND reviewed_at IS NOT NULL"
            " AND review_decision IS NOT NULL)",
            name="review_complete",
        ),
        CheckConstraint(
            "review_notes IS NULL OR head_id IS NOT NULL", name="review_notes_valid"
        ),
        CheckConstraint("reviewed_at >= created_at", name="reviewed_after_creation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("academic_programs.id"), index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("coordinators.id"), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    theory_ratio: Mapped[Decimal] = mapped_column(RATIO)
    practice_ratio: Mapped[Decimal] = mapped_column(RATIO)
    lab_ratio: Mapped[Decimal] = mapped_column(RATIO)
    subject_coverage: Mapped[Decimal] = mapped_column(RATIO)
    block_count: Mapped[int]
    previous_schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id"), unique=True
    )
    validator_id: Mapped[int | None] = mapped_column(
        ForeignKey("coordinators.id"), index=True
    )
    validated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    validation_notes: Mapped[str | None] = mapped_column(Text)
    head_id: Mapped[int | None] = mapped_column(
        ForeignKey("department_heads.id"), index=True
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    review_decision: Mapped[ReviewDecision | None] = mapped_column(
        db_enum(ReviewDecision, "review_decision")
    )
    review_notes: Mapped[str | None] = mapped_column(Text)


class ScheduleSession(Base):
    """Content block programmed in a schedule on a date, time slot and classroom.

    A block is programmed at most once per schedule, and a schedule has at
    most one session per date and time slot (RN-09).
    """

    __tablename__ = "schedule_sessions"
    __table_args__ = (
        UniqueConstraint("schedule_id", "time_slot_id", "session_date"),
        Index(
            "ix_schedule_sessions_classroom_date_slot",
            "classroom_id",
            "session_date",
            "time_slot_id",
        ),
    )

    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), primary_key=True)
    block_id: Mapped[int] = mapped_column(
        ForeignKey("content_blocks.id"), primary_key=True, index=True
    )
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), index=True)
    session_date: Mapped[datetime.date]


class StudentScheduleAssignment(Base):
    """Final schedule assigned to a student.

    ``ended_at`` marks an assignment the student left after an accepted change
    request. The row is kept because the attendance recorded under it
    references it.
    """

    __tablename__ = "student_schedule_assignment"
    __table_args__ = (
        CheckConstraint("ended_at >= assigned_at", name="ended_after_assigned"),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id"), primary_key=True, index=True
    )
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))


class Attendance(Base):
    """Attendance of an assigned student to a session (RN-15)."""

    __tablename__ = "attendances"
    __table_args__ = (
        ForeignKeyConstraint(
            ["schedule_id", "block_id"],
            ["schedule_sessions.schedule_id", "schedule_sessions.block_id"],
        ),
        ForeignKeyConstraint(
            ["student_id", "schedule_id"],
            [
                "student_schedule_assignment.student_id",
                "student_schedule_assignment.schedule_id",
            ],
        ),
        Index("ix_attendances_schedule_block", "schedule_id", "block_id"),
    )

    student_id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(primary_key=True)
    block_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        db_enum(AttendanceStatus, "attendance_status")
    )
