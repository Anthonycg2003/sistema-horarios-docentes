"""Integration tests: migration cycle and CHECK behaviour on a real PostgreSQL.

They DROP every table, ENUM and the analytic schema of the target database, so they
only run against the database named by ``TEST_DATABASE_URL``; ``DATABASE_URL`` is never
used. They are skipped when ``TEST_DATABASE_URL`` is not set or the database is
unreachable, and they leave the database at ``head``. The URL reaches Alembic through
``Config.attributes["database_url"]``, which ``alembic/env.py`` prefers over the settings.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from alembic import command
from alembic.config import Config
from app.db.base import Base
from app.models import ANALYTICS_SCHEMA

BACKEND_DIR = Path(__file__).resolve().parents[2]
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set")

EMPTY = {"enums": [], "schemas": [], "tables": []}


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    """Engine for the configured database; skips when it is unreachable."""
    assert TEST_DATABASE_URL is not None
    eng = create_engine(TEST_DATABASE_URL)
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
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = TEST_DATABASE_URL
    return config


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
    " student_key, program_key, program_name, present_count, absent_count)"
    " VALUES (1, 1, 1, 1, 1, 'p', {present}, {absent})"
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
        "INSERT INTO users (username, password_hash, role, student_id)"
        " VALUES ('u', 'h', 'coordinador', 1)",
        "ck_users_role_matches_profile",
        id="user-role-does-not-match-profile",
    ),
    pytest.param(
        "INSERT INTO users (username, password_hash, role) VALUES ('u', 'h', 'jefe')",
        "ck_users_role_matches_profile",
        id="user-without-profile",
    ),
    pytest.param(
        _ATTENDANCE.format(present=0, absent=0),
        "ck_fact_block_attendance_has_attendance_records",
        id="attendance-without-records",
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
            conn.execute(insert, {**ids, "description": "Álgebra lineal"})
            for variant in ("X", " x ", "X" * 10_000 + " ", "álgebra lineal", " ÁLGEBRA LINEAL "):
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.execute(insert, {**ids, "description": variant})
        finally:
            trans.rollback()


@pytest.mark.usefixtures("migrated")
def test_attendance_rate_is_generated_with_postgresql_rounding(engine: Engine) -> None:
    """The stored rate is computed by PostgreSQL and cannot be written directly."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(
                text(
                    f"INSERT INTO {ANALYTICS_SCHEMA}.dim_time (id, semester_key, period, year,"
                    " start_date, end_date) VALUES (1, 1, '2026-1', 2026, '2026-01-01',"
                    " '2026-06-30')"
                )
            )
            conn.execute(
                text(f"INSERT INTO {ANALYTICS_SCHEMA}.dim_group (id, name) VALUES (1, 'g')")
            )
            conn.execute(
                text(
                    f"INSERT INTO {ANALYTICS_SCHEMA}.dim_block (id, block_key, description,"
                    " subject_name, activity_type, complexity, creator_key, creator_name)"
                    " VALUES (1, 1, 'd', 's', 'teórica', 'bajo', 1, 'c')"
                )
            )
            rate = conn.execute(
                text(_ATTENDANCE.format(present=1, absent=31) + " RETURNING attendance_rate")
            ).scalar_one()
            assert str(rate) == "0.0313"
            with pytest.raises(DBAPIError) as excinfo, conn.begin_nested():
                conn.execute(
                    text(
                        f"INSERT INTO {ANALYTICS_SCHEMA}.fact_block_attendance (time_id, group_id,"
                        " block_id, student_key, program_key, program_name, present_count,"
                        " absent_count, attendance_rate) VALUES (1, 1, 1, 2, 1, 'p', 1, 1, 0.9)"
                    )
                )
            assert "attendance_rate" in str(excinfo.value)
        finally:
            trans.rollback()


@pytest.mark.usefixtures("migrated")
def test_enum_labels_in_database_match_the_models(engine: Engine) -> None:
    """``alembic check`` ignores ENUM labels, so compare them with ``pg_enum`` directly."""
    query = text(
        "SELECT e.enumlabel FROM pg_enum e"
        " JOIN pg_type t ON t.oid = e.enumtypid"
        " JOIN pg_namespace n ON n.oid = t.typnamespace"
        " WHERE t.typname = :name AND n.nspname = :schema ORDER BY e.enumsortorder"
    )
    enums = {
        (column.type.name, column.type.schema or "public"): list(column.type.enums)
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, sa.Enum)
    }
    assert enums
    with engine.connect() as conn:
        for (name, schema), labels in enums.items():
            found = conn.execute(query, {"name": name, "schema": schema}).scalars().all()
            assert found == labels, f"{schema}.{name}"


def test_time_slots_and_semesters_do_not_overlap(engine: Engine, migrated: None) -> None:
    """RN-04 and RN-05: ranges that cross are rejected; ranges that only touch are not."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(
                text(
                    "INSERT INTO time_slots (weekday, start_time, end_time)"
                    " VALUES ('lunes', '08:00', '10:00'), ('lunes', '10:00', '12:00')"
                )
            )
            with pytest.raises(IntegrityError) as excinfo, conn.begin_nested():
                conn.execute(
                    text(
                        "INSERT INTO time_slots (weekday, start_time, end_time)"
                        " VALUES ('lunes', '09:00', '11:00')"
                    )
                )
            assert excinfo.value.orig.diag.constraint_name == "ex_time_slots_no_overlap"  # type: ignore[union-attr]
            conn.execute(
                text(
                    "INSERT INTO semesters (name, start_date, end_date)"
                    " VALUES ('S1', '2026-01-01', '2026-06-30'),"
                    " ('S2', '2026-07-01', '2026-12-15')"
                )
            )
            with pytest.raises(IntegrityError) as excinfo, conn.begin_nested():
                conn.execute(
                    text(
                        "INSERT INTO semesters (name, start_date, end_date)"
                        " VALUES ('S3', '2026-06-01', '2026-08-01')"
                    )
                )
            assert excinfo.value.orig.diag.constraint_name == "ex_semesters_no_overlap"  # type: ignore[union-attr]
        finally:
            trans.rollback()


def test_accepting_a_change_request_moves_the_student(engine: Engine, migrated: None) -> None:
    """RN-06, RN-13 and RN-20: acceptance closes the origin and opens the target."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            program = conn.execute(
                text("INSERT INTO academic_programs (name, study_plan) VALUES ('P', '2026') RETURNING id")
            ).scalar_one()
            coordinator = conn.execute(
                text("INSERT INTO coordinators (name, specialty) VALUES ('C', 'S') RETURNING id")
            ).scalar_one()
            blocked = conn.execute(
                text("INSERT INTO coordinators (name, specialty) VALUES ('D', 'S') RETURNING id")
            ).scalar_one()
            head = conn.execute(
                text("INSERT INTO department_heads (name) VALUES ('J') RETURNING id")
            ).scalar_one()
            student = conn.execute(
                text("INSERT INTO students (name, age, group_name) VALUES ('E', 20, 'A') RETURNING id")
            ).scalar_one()
            subject = conn.execute(text("INSERT INTO subjects (name) VALUES ('Mat') RETURNING id")).scalar_one()
            conn.execute(
                text(
                    "INSERT INTO coordinator_program (coordinator_id, program_id, can_generate, can_validate)"
                    " VALUES (:coordinator, :program, true, true), (:blocked, :program, false, true)"
                ),
                {"coordinator": coordinator, "blocked": blocked, "program": program},
            )
            conn.execute(
                text(
                    "INSERT INTO student_program (student_id, program_id) VALUES (:student, :program)"
                ),
                {"student": student, "program": program},
            )
            semester = conn.execute(
                text(
                    "INSERT INTO semesters (name, start_date, end_date)"
                    " VALUES ('2026-1', '2026-01-01', '2026-06-30') RETURNING id"
                )
            ).scalar_one()
            morning, afternoon = conn.execute(
                text(
                    "INSERT INTO time_slots (weekday, start_time, end_time) VALUES"
                    " ('lunes', '08:00', '10:00'), ('lunes', '10:00', '12:00') RETURNING id"
                )
            ).scalars()
            classroom = conn.execute(
                text("INSERT INTO classrooms (name, building, capacity) VALUES ('1', 'A', 30) RETURNING id")
            ).scalar_one()
            block = conn.execute(
                text(
                    "INSERT INTO content_blocks (subject_id, description, activity_type, complexity, creator_id)"
                    " VALUES (:subject, 'intro', 'teórica', 'bajo', :coordinator) RETURNING id"
                ),
                {"subject": subject, "coordinator": coordinator},
            ).scalar_one()
            with pytest.raises(IntegrityError) as excinfo, conn.begin_nested():
                conn.execute(
                    text(
                        "INSERT INTO schedules (program_id, semester_id, creator_id, theory_ratio,"
                        " practice_ratio, lab_ratio, subject_coverage, block_count)"
                        " VALUES (:program, :semester, :blocked, 0.5, 0.3, 0.2, 1, 1)"
                    ),
                    {"program": program, "semester": semester, "blocked": blocked},
                )
            assert "RN-06" in str(excinfo.value)
            origin, target = conn.execute(
                text(
                    "INSERT INTO schedules (program_id, semester_id, creator_id, theory_ratio,"
                    " practice_ratio, lab_ratio, subject_coverage, block_count, created_at, head_id,"
                    " reviewed_at, review_decision)"
                    " VALUES (:program, :semester, :coordinator, 0.5, 0.3, 0.2, 1, 1,"
                    " '2026-01-01 00:00+00', :head, '2026-01-02 00:00+00', 'aprobado'),"
                    " (:program, :semester, :coordinator, 0.5, 0.3, 0.2, 1, 1,"
                    " '2026-01-01 00:00+00', :head, '2026-01-02 00:00+00', 'aprobado')"
                    " RETURNING id"
                ),
                {
                    "program": program,
                    "semester": semester,
                    "coordinator": coordinator,
                    "head": head,
                },
            ).scalars()
            conn.execute(
                text(
                    "INSERT INTO schedule_sessions"
                    " (schedule_id, block_id, classroom_id, time_slot_id, session_date)"
                    " VALUES (:origin, :block, :classroom, :morning, '2026-01-05'),"
                    " (:target, :block, :classroom, :afternoon, '2026-01-05')"
                ),
                {
                    "origin": origin,
                    "target": target,
                    "block": block,
                    "classroom": classroom,
                    "morning": morning,
                    "afternoon": afternoon,
                },
            )
            conn.execute(
                text(
                    "INSERT INTO student_schedule_assignment (student_id, schedule_id, assigned_at)"
                    " VALUES (:student, :origin, '2026-02-01 00:00+00')"
                ),
                {"student": student, "origin": origin},
            )
            conn.execute(
                text(
                    "INSERT INTO change_requests (student_id, reason, requested_at, status, resolved_at,"
                    " origin_schedule_id, target_schedule_id, attending_coordinator_id)"
                    " VALUES (:student, 'cambio', '2026-02-01 00:00+00', 'aceptada',"
                    " '2026-02-02 00:00+00', :origin, :target, :coordinator)"
                ),
                {
                    "student": student,
                    "origin": origin,
                    "target": target,
                    "coordinator": coordinator,
                },
            )
            rows = conn.execute(
                text(
                    "SELECT schedule_id, ended_at IS NULL FROM student_schedule_assignment"
                    " WHERE student_id = :student"
                ),
                {"student": student},
            ).all()
            assert set(rows) == {(origin, False), (target, True)}
            with pytest.raises(IntegrityError) as excinfo, conn.begin_nested():
                conn.execute(text("DELETE FROM schedules WHERE id = :origin"), {"origin": origin})
            assert "cannot be deleted" in str(excinfo.value)
        finally:
            trans.rollback()


@pytest.mark.usefixtures("migrated")
def test_check_constraints_in_database_match_the_models(engine: Engine) -> None:
    """``alembic check`` ignores CHECK constraints; compare their names with ``pg_constraint``."""
    expected = {
        str(constraint.name)
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, sa.CheckConstraint)
    }
    assert expected
    with engine.connect() as conn:
        found = set(
            conn.execute(
                text(
                    "SELECT c.conname FROM pg_constraint c"
                    " JOIN pg_namespace n ON n.oid = c.connamespace"
                    " WHERE c.contype = 'c' AND n.nspname IN ('public', :analytic)"
                ),
                {"analytic": ANALYTICS_SCHEMA},
            ).scalars()
        )
    assert found == expected
