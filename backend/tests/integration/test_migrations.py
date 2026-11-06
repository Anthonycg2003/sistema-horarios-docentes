"""Integration tests: migration cycle and CHECK behaviour on a real PostgreSQL.

They are skipped when ``DATABASE_URL`` is not set or the database is unreachable,
and they leave the database at ``head``.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError

from alembic import command
from alembic.config import Config
from app.models import ANALYTICS_SCHEMA

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL is not set")

EMPTY = {"enums": [], "schemas": [], "tables": []}


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    """Engine for the configured database; skips when it is unreachable."""
    assert DATABASE_URL is not None
    eng = create_engine(DATABASE_URL)
    try:
        with eng.connect():
            pass
    except OperationalError:
        eng.dispose()
        pytest.skip("database is not reachable")
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def alembic_config() -> Config:
    """Alembic configuration pointing at backend/alembic.ini."""
    return Config(str(BACKEND_DIR / "alembic.ini"))


@pytest.fixture(scope="module")
def migrated(engine: Engine, alembic_config: Config) -> Iterator[None]:
    """Run the schema at ``head`` for the tests and leave it there afterwards."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    yield
    command.upgrade(alembic_config, "head")


def _leftovers(engine: Engine) -> dict[str, list[str]]:
    """Return the ENUM types, analytic schemas and tables present in the database."""
    with engine.connect() as conn:
        enums = conn.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'")).scalars()
        schemas = conn.execute(
            text("SELECT nspname FROM pg_namespace WHERE nspname = :name"),
            {"name": ANALYTICS_SCHEMA},
        ).scalars()
        tables = conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                " AND tablename <> 'alembic_version'"
            )
        ).scalars()
        return {"enums": list(enums), "schemas": list(schemas), "tables": list(tables)}


def test_upgrade_downgrade_cycle_leaves_no_residue(engine: Engine, alembic_config: Config) -> None:
    """Downgrade removes every table, ENUM and the analytic schema; upgrade restores them."""
    command.downgrade(alembic_config, "base")
    assert _leftovers(engine) == EMPTY
    command.upgrade(alembic_config, "head")
    present = _leftovers(engine)
    assert present["schemas"] == [ANALYTICS_SCHEMA]
    assert present["enums"] and present["tables"]
    command.downgrade(alembic_config, "base")
    assert _leftovers(engine) == EMPTY
    command.upgrade(alembic_config, "head")


def test_models_and_migration_stay_in_sync(alembic_config: Config, migrated: None) -> None:
    """``alembic check`` finds no difference between the models and the database."""
    command.check(alembic_config)


_SCHEDULE = (
    "INSERT INTO schedules (program_id, semester_id, creator_id, theory_ratio, practice_ratio,"
    " lab_ratio, subject_coverage, block_count{extra_cols})"
    " VALUES (1, 1, 1, {ratios}, 1, 1{extra_vals})"
)
_ATTENDANCE = (
    f"INSERT INTO {ANALYTICS_SCHEMA}.fact_block_attendance (time_id, group_id, block_id,"
    " student_key, program_key, program_name, present_count, absent_count, attendance_rate)"
    " VALUES (1, 1, 1, 1, 1, 'p', {present}, {absent}, {rate})"
)
_REQUEST = (
    "INSERT INTO change_requests (student_id, reason, status, origin_schedule_id,"
    " attending_coordinator_id{extra_cols}) VALUES (1, 'r', '{status}', 1, 1{extra_vals})"
)

INVALID_INSERTS = [
    pytest.param(
        _SCHEDULE.format(ratios="0.5, 0.5, 0.5", extra_cols="", extra_vals=""),
        "ck_schedules_ratios_sum_one",
        id="ratios-do-not-sum-one",
    ),
    pytest.param(
        _SCHEDULE.format(ratios="0.5, 0.3, 0.2", extra_cols=", head_id", extra_vals=", 1"),
        "ck_schedules_review_complete",
        id="incomplete-review",
    ),
    pytest.param(
        _SCHEDULE.format(ratios="0.5, 0.3, 0.2", extra_cols=", validator_id", extra_vals=", 1"),
        "ck_schedules_validation_complete",
        id="incomplete-validation",
    ),
    pytest.param(
        _REQUEST.format(status="aceptada", extra_cols="", extra_vals=""),
        "ck_change_requests_status_consistent",
        id="accepted-request-without-target",
    ),
    pytest.param(
        _REQUEST.format(status="pendiente", extra_cols=", resolved_at", extra_vals=", now()"),
        "ck_change_requests_status_consistent",
        id="pending-request-with-resolution",
    ),
    pytest.param(
        "INSERT INTO classrooms (building, name, capacity) VALUES ('A', 'A1', 0)",
        "ck_classrooms_capacity_positive",
        id="classroom-capacity-zero",
    ),
    pytest.param(
        _ATTENDANCE.format(present=0, absent=0, rate="0.9"),
        "ck_fact_block_attendance_has_attendance_records",
        id="attendance-without-records",
    ),
    pytest.param(
        _ATTENDANCE.format(present=3, absent=1, rate="0.9"),
        "ck_fact_block_attendance_attendance_rate_matches_counts",
        id="attendance-rate-not-derived",
    ),
]


@pytest.mark.usefixtures("migrated")
@pytest.mark.parametrize(("statement", "constraint"), INVALID_INSERTS)
def test_check_constraints_reject_invalid_rows(
    engine: Engine, statement: str, constraint: str
) -> None:
    """Invalid rows fail on the named CHECK, which PostgreSQL evaluates before foreign keys."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            with pytest.raises(IntegrityError) as excinfo:
                conn.execute(text(statement))
            assert excinfo.value.orig.diag.constraint_name == constraint  # type: ignore[union-attr]
        finally:
            trans.rollback()


@pytest.mark.usefixtures("migrated")
def test_content_block_duplicates_ignore_case_and_outer_spaces(engine: Engine) -> None:
    """RN-03: very long descriptions are accepted and case/space variants collide."""
    insert = text(
        "INSERT INTO content_blocks (subject_id, description, activity_type, complexity,"
        " creator_id) VALUES (:subject, :description, 'teórica', 'bajo', :creator)"
    )
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            subject = conn.execute(
                text("INSERT INTO subjects (name) VALUES ('s') RETURNING id")
            ).scalar_one()
            creator = conn.execute(
                text("INSERT INTO coordinators (name, specialty) VALUES ('c', 's') RETURNING id")
            ).scalar_one()
            ids = {"subject": subject, "creator": creator}
            conn.execute(insert, {**ids, "description": "x" * 10_000})
            conn.execute(insert, {**ids, "description": "x"})
            for variant in ("X", " x ", "X" * 10_000 + " "):
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.execute(insert, {**ids, "description": variant})
        finally:
            trans.rollback()
