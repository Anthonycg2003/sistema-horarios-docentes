"""Unit tests for the ORM metadata: schemas, enums and key constraints."""

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import configure_mappers

import app.models as models
from app.db.base import Base

ANALYTIC_TABLES = {
    "dim_time",
    "dim_classroom",
    "dim_time_slot",
    "dim_group",
    "dim_block",
    "fact_classroom_occupancy",
    "fact_block_attendance",
    "fact_change_request",
}


def _unique_column_sets(table_name: str) -> set[frozenset[str]]:
    """Return the column sets declared unique on a table, including its PK."""
    table = Base.metadata.tables[table_name]
    sets = {frozenset(c.name for c in table.primary_key.columns)}
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            sets.add(frozenset(c.name for c in constraint.columns))
    for column in table.columns:
        if column.unique:
            sets.add(frozenset({column.name}))
    return sets


def test_mappers_configure() -> None:
    """All models map without configuration errors."""
    configure_mappers()


def test_analytic_tables_live_in_their_own_schema() -> None:
    """The star schema tables are in the analytic schema and only there."""
    analytic = {
        t.name for t in Base.metadata.tables.values() if t.schema == models.ANALYTICS_SCHEMA
    }
    assert analytic == ANALYTIC_TABLES


def test_operational_tables_live_in_public() -> None:
    """Every non-analytic table uses the default schema."""
    others = [t for t in Base.metadata.tables.values() if t.name not in ANALYTIC_TABLES]
    assert others and all(t.schema is None for t in others)


def test_analytic_schema_has_no_foreign_keys_to_operational() -> None:
    """RN-23: the analytic schema does not reference operational tables."""
    for table in Base.metadata.tables.values():
        if table.schema != models.ANALYTICS_SCHEMA:
            continue
        for fk in table.foreign_keys:
            assert fk.column.table.schema == models.ANALYTICS_SCHEMA


@pytest.mark.parametrize(
    ("enum_cls", "values"),
    [
        (models.ActivityType, ["teórica", "práctica", "laboratorio"]),
        (models.ComplexityLevel, ["bajo", "medio", "alto"]),
        (models.ReviewDecision, ["aprobado", "nueva confección"]),
        (models.AttendanceStatus, ["presente", "ausente"]),
        (models.ChangeRequestStatus, ["pendiente", "aceptada", "rechazada"]),
        (
            models.Weekday,
            ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
        ),
    ],
)
def test_enum_values_match_design(enum_cls: type, values: list[str]) -> None:
    """Enum values are the Spanish domain values of the design report."""
    assert [member.value for member in enum_cls] == values


def test_enum_columns_store_values() -> None:
    """Database ENUM labels are the member values, not the member names."""
    column = Base.metadata.tables["content_blocks"].c.activity_type
    assert column.type.enums == ["teórica", "práctica", "laboratorio"]


@pytest.mark.parametrize(
    ("table_name", "columns"),
    [
        ("time_slots", {"weekday", "start_time"}),
        ("time_slots", {"weekday", "end_time"}),
        ("semesters", {"start_date"}),
        ("semesters", {"end_date"}),
        ("schedules", {"previous_schedule_id"}),
        ("schedule_sessions", {"schedule_id", "block_id"}),
        ("schedule_sessions", {"schedule_id", "time_slot_id", "session_date"}),
        ("attendances", {"student_id", "schedule_id", "block_id"}),
    ],
)
def test_design_keys_are_unique(table_name: str, columns: set[str]) -> None:
    """The keys of the 3NF decomposition are declared unique."""
    assert frozenset(columns) in _unique_column_sets(table_name)


def test_attendance_references_session_and_assignment() -> None:
    """RN-15: attendance points to the session and to the student assignment."""
    targets = {
        (fk.referred_table.name, tuple(c.name for c in fk.columns))
        for fk in Base.metadata.tables["attendances"].foreign_key_constraints
    }
    assert targets == {
        ("schedule_sessions", ("schedule_id", "block_id")),
        ("student_schedule_assignment", ("student_id", "schedule_id")),
    }
