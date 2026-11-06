"""Domain enums.

Member names are in English; values are the Spanish domain values stored in
the database, as defined in the database design report.
"""

import enum

from sqlalchemy import Enum


class ActivityType(enum.StrEnum):
    """Type of activity a content block covers."""

    THEORETICAL = "teórica"
    PRACTICAL = "práctica"
    LABORATORY = "laboratorio"


class ComplexityLevel(enum.StrEnum):
    """Complexity level of a content block."""

    LOW = "bajo"
    MEDIUM = "medio"
    HIGH = "alto"


class ReviewDecision(enum.StrEnum):
    """Decision of the department head when reviewing a schedule."""

    APPROVED = "aprobado"
    NEW_DRAFT = "nueva confección"


class AttendanceStatus(enum.StrEnum):
    """Attendance of a student to a session."""

    PRESENT = "presente"
    ABSENT = "ausente"


class ChangeRequestStatus(enum.StrEnum):
    """State of a schedule change request."""

    PENDING = "pendiente"
    ACCEPTED = "aceptada"
    REJECTED = "rechazada"


class Weekday(enum.StrEnum):
    """Teaching day of the week of a time slot."""

    MONDAY = "lunes"
    TUESDAY = "martes"
    WEDNESDAY = "miércoles"
    THURSDAY = "jueves"
    FRIDAY = "viernes"
    SATURDAY = "sábado"


def db_enum(enum_cls: type[enum.Enum], name: str, schema: str | None = None) -> Enum:
    """Build a native PostgreSQL ENUM column type that stores the member values.

    Args:
        enum_cls: Python enum whose values become the database labels.
        name: Name of the ENUM type in the database.
        schema: Schema that owns the type. ``None`` uses the default schema.

    Returns:
        The SQLAlchemy ``Enum`` type.
    """
    return Enum(
        enum_cls,
        name=name,
        schema=schema,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
