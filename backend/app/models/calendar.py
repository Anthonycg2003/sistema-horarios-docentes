"""Semesters, classrooms and weekly time slots."""

import datetime

from sqlalchemy import CheckConstraint, String, UniqueConstraint, literal_column
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Weekday, db_enum


class Semester(Base):
    """Teaching period. Every schedule belongs to one semester.

    Inclusive date ranges of two semesters do not overlap (RN-05).
    """

    __tablename__ = "semesters"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="dates_ordered"),
        ExcludeConstraint(
            (literal_column("daterange(start_date, end_date, '[]')"), "&&"),
            using="gist",
            name="ex_semesters_no_overlap",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    start_date: Mapped[datetime.date] = mapped_column(unique=True)
    end_date: Mapped[datetime.date] = mapped_column(unique=True)


class Classroom(Base):
    """Classroom of a building."""

    __tablename__ = "classrooms"
    __table_args__ = (
        UniqueConstraint("building", "name"),
        CheckConstraint("capacity > 0", name="capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    building: Mapped[str] = mapped_column(String(80))
    capacity: Mapped[int]


class TimeSlot(Base):
    """Weekly time slot. Slots of the same day do not overlap (RN-04)."""

    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("weekday", "start_time"),
        UniqueConstraint("weekday", "end_time"),
        CheckConstraint("end_time > start_time", name="times_ordered"),
        ExcludeConstraint(
            ("weekday", "="),
            (
                literal_column(
                    "tsrange((DATE '2000-01-01' + start_time), (DATE '2000-01-01' + end_time))"
                ),
                "&&",
            ),
            using="gist",
            name="ex_time_slots_no_overlap",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[Weekday] = mapped_column(db_enum(Weekday, "weekday"))
    start_time: Mapped[datetime.time]
    end_time: Mapped[datetime.time]
