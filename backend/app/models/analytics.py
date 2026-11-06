"""Historical star schema, kept apart from the operational model (RN-23).

The tables live in their own schema, have no foreign keys towards the
operational tables and are denormalized on purpose: they are loaded at the
end of each semester and queried in aggregate. Operational identifiers are
kept as plain degenerate columns (``*_key``) so the load process can be
idempotent without coupling the schemas.
"""

import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    ActivityType,
    ChangeRequestStatus,
    ComplexityLevel,
    Weekday,
    db_enum,
)

ANALYTICS_SCHEMA = "analitic"


class DimTime(Base):
    """Time dimension. Its grain is the semester."""

    __tablename__ = "dim_time"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="dates_ordered"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_key: Mapped[int] = mapped_column(unique=True)
    period: Mapped[str] = mapped_column(String(40))
    year: Mapped[int]
    start_date: Mapped[datetime.date]
    end_date: Mapped[datetime.date]


class DimClassroom(Base):
    """Classroom dimension, with its building."""

    __tablename__ = "dim_classroom"
    __table_args__ = {"schema": ANALYTICS_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_key: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(40))
    building: Mapped[str] = mapped_column(String(80), index=True)
    capacity: Mapped[int]


class DimTimeSlot(Base):
    """Weekly time slot dimension."""

    __tablename__ = "dim_time_slot"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="times_ordered"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    time_slot_key: Mapped[int] = mapped_column(unique=True)
    weekday: Mapped[Weekday] = mapped_column(db_enum(Weekday, "weekday", ANALYTICS_SCHEMA))
    label: Mapped[str] = mapped_column(String(40))
    start_time: Mapped[datetime.time]
    end_time: Mapped[datetime.time]


class DimGroup(Base):
    """Student group dimension."""

    __tablename__ = "dim_group"
    __table_args__ = {"schema": ANALYTICS_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)


class DimBlock(Base):
    """Content block dimension, with its subject, complexity and creator copied in.

    A new row is added when a block changes its classification, so past facts
    keep the complexity the block had when they happened.
    """

    __tablename__ = "dim_block"
    __table_args__ = (
        UniqueConstraint("block_key", "activity_type", "complexity", "subject_name"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    block_key: Mapped[int] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(String)
    subject_name: Mapped[str] = mapped_column(String(160))
    activity_type: Mapped[ActivityType] = mapped_column(
        db_enum(ActivityType, "activity_type", ANALYTICS_SCHEMA)
    )
    complexity: Mapped[ComplexityLevel] = mapped_column(
        db_enum(ComplexityLevel, "complexity_level", ANALYTICS_SCHEMA)
    )
    creator_key: Mapped[int]
    creator_name: Mapped[str] = mapped_column(String(160))


class FactClassroomOccupancy(Base):
    """Classroom occupancy per semester, classroom and time slot."""

    __tablename__ = "fact_classroom_occupancy"
    __table_args__ = (
        UniqueConstraint("time_id", "classroom_id", "time_slot_id"),
        CheckConstraint("occupied_minutes >= 0", name="occupied_minutes_non_negative"),
        CheckConstraint("session_count >= 0", name="session_count_non_negative"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey(f"{ANALYTICS_SCHEMA}.dim_time.id"))
    classroom_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ANALYTICS_SCHEMA}.dim_classroom.id"), index=True
    )
    time_slot_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ANALYTICS_SCHEMA}.dim_time_slot.id"), index=True
    )
    occupied_minutes: Mapped[int]
    session_count: Mapped[int]


class FactBlockAttendance(Base):
    """Attendance per semester, group, student, program and block."""

    __tablename__ = "fact_block_attendance"
    __table_args__ = (
        UniqueConstraint("time_id", "group_id", "student_key", "program_key", "block_id"),
        CheckConstraint("present_count >= 0", name="present_count_non_negative"),
        CheckConstraint("absent_count >= 0", name="absent_count_non_negative"),
        CheckConstraint("attendance_rate BETWEEN 0 AND 1", name="attendance_rate_range"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey(f"{ANALYTICS_SCHEMA}.dim_time.id"))
    group_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ANALYTICS_SCHEMA}.dim_group.id"), index=True
    )
    block_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ANALYTICS_SCHEMA}.dim_block.id"), index=True
    )
    student_key: Mapped[int] = mapped_column(index=True)
    program_key: Mapped[int] = mapped_column(index=True)
    program_name: Mapped[str] = mapped_column(String(160))
    present_count: Mapped[int]
    absent_count: Mapped[int]
    attendance_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4))


class FactChangeRequest(Base):
    """Number of change requests per semester, group, student, program and status."""

    __tablename__ = "fact_change_request"
    __table_args__ = (
        UniqueConstraint("time_id", "group_id", "student_key", "program_key", "status"),
        CheckConstraint("request_count > 0", name="request_count_positive"),
        {"schema": ANALYTICS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey(f"{ANALYTICS_SCHEMA}.dim_time.id"))
    group_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ANALYTICS_SCHEMA}.dim_group.id"), index=True
    )
    student_key: Mapped[int] = mapped_column(index=True)
    program_key: Mapped[int] = mapped_column(index=True)
    program_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[ChangeRequestStatus] = mapped_column(
        db_enum(ChangeRequestStatus, "change_request_status", ANALYTICS_SCHEMA)
    )
    request_count: Mapped[int]
