"""Enforce the business rules that the design report assigns to triggers.

The non-overlap part of RN-04 and RN-05 becomes exclusion constraints; the
other rules become triggers. A schedule is final exactly when
``review_decision`` is ``aprobado`` (RN-11); the triggers use that predicate
and no extra column is stored.

Revision ID: a8c4e1b07d52
Revises: d4cb330e67e9
Create Date: 2026-11-06 14:10:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a8c4e1b07d52"
down_revision: str | Sequence[str] | None = "d4cb330e67e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UPGRADE_SQL = """
CREATE FUNCTION weekday_isodow(day weekday) RETURNS integer
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE day::text
        WHEN 'lunes' THEN 1
        WHEN 'martes' THEN 2
        WHEN 'miércoles' THEN 3
        WHEN 'jueves' THEN 4
        WHEN 'viernes' THEN 5
        WHEN 'sábado' THEN 6
    END
$$;

CREATE FUNCTION fn_schedules_before_write() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- Missing parents are left to the foreign key. A BEFORE trigger runs
    -- before CHECK, and an early raise would hide the named check.
    IF EXISTS (SELECT 1 FROM coordinators WHERE id = NEW.creator_id)
       AND EXISTS (SELECT 1 FROM academic_programs WHERE id = NEW.program_id)
       AND NOT EXISTS (
           SELECT 1 FROM coordinator_program
           WHERE coordinator_id = NEW.creator_id
             AND program_id = NEW.program_id
             AND can_generate
       ) THEN
        RAISE EXCEPTION
            'RN-06: the generating coordinator is not authorized for this program'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.validator_id IS NOT NULL
       AND EXISTS (SELECT 1 FROM coordinators WHERE id = NEW.validator_id)
       AND EXISTS (SELECT 1 FROM academic_programs WHERE id = NEW.program_id)
       AND NOT EXISTS (
           SELECT 1 FROM coordinator_program
           WHERE coordinator_id = NEW.validator_id
             AND program_id = NEW.program_id
             AND can_validate
       ) THEN
        RAISE EXCEPTION
            'RN-07: the validating coordinator is not authorized for this program'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.previous_schedule_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM schedules previous
        WHERE previous.id = NEW.previous_schedule_id
          AND (
              previous.review_decision IS DISTINCT FROM 'nueva confección'
              OR previous.program_id <> NEW.program_id
              OR previous.semester_id <> NEW.semester_id
          )
    ) THEN
        RAISE EXCEPTION
            'RN-12: a schedule replaces another only when that one decided'
            ' a new draft for the same program and semester'
            USING ERRCODE = 'check_violation';
    END IF;

    IF TG_OP = 'UPDATE'
       AND NEW.review_decision IS DISTINCT FROM 'nueva confección'
       AND EXISTS (
           SELECT 1 FROM schedules successor
           WHERE successor.previous_schedule_id = NEW.id
       ) THEN
        RAISE EXCEPTION
            'RN-12: a replaced schedule must keep the decision nueva confección'
            USING ERRCODE = 'check_violation';
    END IF;

    IF TG_OP = 'UPDATE'
       AND OLD.review_decision = 'aprobado'
       AND NEW.review_decision IS DISTINCT FROM 'aprobado'
       AND EXISTS (
           SELECT 1 FROM student_schedule_assignment
           WHERE schedule_id = NEW.id AND ended_at IS NULL
       ) THEN
        RAISE EXCEPTION
            'RN-13: a schedule with an active assignment must stay final'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.review_decision = 'aprobado' AND EXISTS (
        SELECT 1
        FROM schedule_sessions mine
        JOIN schedule_sessions other
          ON other.schedule_id <> mine.schedule_id
         AND other.classroom_id = mine.classroom_id
         AND other.session_date = mine.session_date
         AND other.time_slot_id = mine.time_slot_id
        JOIN schedules other_schedule
          ON other_schedule.id = other.schedule_id
         AND other_schedule.review_decision = 'aprobado'
        WHERE mine.schedule_id = NEW.id
    ) THEN
        RAISE EXCEPTION
            'RN-10: two final schedules share a classroom, date and time slot'
            USING ERRCODE = 'check_violation';
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.semester_id IS DISTINCT FROM OLD.semester_id
       AND EXISTS (
           SELECT 1
           FROM schedule_sessions session
           JOIN semesters semester ON semester.id = NEW.semester_id
           WHERE session.schedule_id = NEW.id
             AND (
                 session.session_date < semester.start_date
                 OR session.session_date > semester.end_date
             )
       ) THEN
        RAISE EXCEPTION
            'RN-08: a session date must fall within the semester of its schedule'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_schedules_before_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.validator_id IS NOT NULL OR OLD.head_id IS NOT NULL THEN
        RAISE EXCEPTION
            'a validated or reviewed schedule cannot be deleted'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN OLD;
END;
$$;

CREATE FUNCTION fn_coordinator_program_before_write() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    dropping_generate boolean;
    dropping_validate boolean;
BEGIN
    IF TG_OP = 'DELETE' THEN
        dropping_generate := TRUE;
        dropping_validate := TRUE;
    ELSE
        dropping_generate := NOT NEW.can_generate
            OR NEW.coordinator_id IS DISTINCT FROM OLD.coordinator_id
            OR NEW.program_id IS DISTINCT FROM OLD.program_id;
        dropping_validate := NOT NEW.can_validate
            OR NEW.coordinator_id IS DISTINCT FROM OLD.coordinator_id
            OR NEW.program_id IS DISTINCT FROM OLD.program_id;
    END IF;

    IF dropping_generate AND EXISTS (
        SELECT 1 FROM schedules
        WHERE creator_id = OLD.coordinator_id AND program_id = OLD.program_id
    ) THEN
        RAISE EXCEPTION
            'RN-06: the generating coordinator must keep authorization'
            USING ERRCODE = 'check_violation';
    END IF;

    IF dropping_validate AND EXISTS (
        SELECT 1 FROM schedules
        WHERE validator_id = OLD.coordinator_id AND program_id = OLD.program_id
    ) THEN
        RAISE EXCEPTION
            'RN-07: the validating coordinator must keep authorization'
            USING ERRCODE = 'check_violation';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_sessions_before_write() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    semester_start date;
    semester_end date;
    slot_day weekday;
    schedule_is_final boolean;
BEGIN
    SELECT semester.start_date, semester.end_date,
           schedule.review_decision = 'aprobado'
      INTO semester_start, semester_end, schedule_is_final
      FROM schedules schedule
      JOIN semesters semester ON semester.id = schedule.semester_id
     WHERE schedule.id = NEW.schedule_id;
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    SELECT weekday INTO slot_day FROM time_slots WHERE id = NEW.time_slot_id;
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF NEW.session_date < semester_start OR NEW.session_date > semester_end THEN
        RAISE EXCEPTION
            'RN-08: a session date must fall within the semester of its schedule'
            USING ERRCODE = 'check_violation';
    END IF;

    IF weekday_isodow(slot_day)
       IS DISTINCT FROM EXTRACT(ISODOW FROM NEW.session_date)::integer THEN
        RAISE EXCEPTION
            'RN-08: a session date must fall on the weekday of its time slot'
            USING ERRCODE = 'check_violation';
    END IF;

    IF schedule_is_final AND EXISTS (
        SELECT 1
        FROM schedule_sessions other
        JOIN schedules other_schedule
          ON other_schedule.id = other.schedule_id
         AND other_schedule.review_decision = 'aprobado'
        WHERE other.schedule_id <> NEW.schedule_id
          AND other.classroom_id = NEW.classroom_id
          AND other.session_date = NEW.session_date
          AND other.time_slot_id = NEW.time_slot_id
    ) THEN
        RAISE EXCEPTION
            'RN-10: two final schedules share a classroom, date and time slot'
            USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM student_schedule_assignment mine
        JOIN student_schedule_assignment other
          ON other.student_id = mine.student_id
         AND other.ended_at IS NULL
         AND other.schedule_id <> NEW.schedule_id
        JOIN schedule_sessions theirs
          ON theirs.schedule_id = other.schedule_id
         AND theirs.session_date = NEW.session_date
         AND theirs.time_slot_id = NEW.time_slot_id
        WHERE mine.schedule_id = NEW.schedule_id
          AND mine.ended_at IS NULL
    ) THEN
        RAISE EXCEPTION
            'RN-14: the student would have two sessions on the same date and time slot'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_sessions_before_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM schedules
        WHERE id = OLD.schedule_id
          AND (validator_id IS NOT NULL OR head_id IS NOT NULL)
    ) THEN
        RAISE EXCEPTION
            'a session of a validated or reviewed schedule cannot be deleted'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN OLD;
END;
$$;

CREATE FUNCTION fn_semesters_before_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM schedule_sessions session
        JOIN schedules schedule ON schedule.id = session.schedule_id
        WHERE schedule.semester_id = NEW.id
          AND (
              session.session_date < NEW.start_date
              OR session.session_date > NEW.end_date
          )
    ) THEN
        RAISE EXCEPTION
            'RN-08: a session date must fall within the semester of its schedule'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_assignments_before_write() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL THEN
        RETURN NEW;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM schedules WHERE id = NEW.schedule_id)
       OR NOT EXISTS (SELECT 1 FROM students WHERE id = NEW.student_id) THEN
        RETURN NEW;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM schedules
        WHERE id = NEW.schedule_id AND review_decision = 'aprobado'
    ) THEN
        RAISE EXCEPTION
            'RN-13: only a final schedule can be assigned'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM student_program enrollment
        JOIN schedules schedule ON schedule.program_id = enrollment.program_id
        WHERE enrollment.student_id = NEW.student_id
          AND schedule.id = NEW.schedule_id
    ) THEN
        RAISE EXCEPTION
            'RN-13: the student is not enrolled in the program of the schedule'
            USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM schedule_sessions mine
        JOIN student_schedule_assignment other
          ON other.student_id = NEW.student_id
         AND other.ended_at IS NULL
         AND other.schedule_id <> NEW.schedule_id
        JOIN schedule_sessions theirs
          ON theirs.schedule_id = other.schedule_id
         AND theirs.session_date = mine.session_date
         AND theirs.time_slot_id = mine.time_slot_id
        WHERE mine.schedule_id = NEW.schedule_id
    ) THEN
        RAISE EXCEPTION
            'RN-14: the student would have two sessions on the same date and time slot'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_change_requests_before_write() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT'
       OR NEW.student_id IS DISTINCT FROM OLD.student_id
       OR NEW.origin_schedule_id IS DISTINCT FROM OLD.origin_schedule_id THEN
        IF EXISTS (SELECT 1 FROM students WHERE id = NEW.student_id)
           AND EXISTS (SELECT 1 FROM schedules WHERE id = NEW.origin_schedule_id)
           AND NOT EXISTS (
               SELECT 1 FROM student_schedule_assignment
               WHERE student_id = NEW.student_id
                 AND schedule_id = NEW.origin_schedule_id
                 AND ended_at IS NULL
           ) THEN
            RAISE EXCEPTION
                'RN-16: the origin schedule is not assigned to the student'
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    IF NEW.target_schedule_id IS NOT NULL
       AND EXISTS (SELECT 1 FROM schedules WHERE id = NEW.target_schedule_id)
       AND EXISTS (SELECT 1 FROM schedules WHERE id = NEW.origin_schedule_id)
       AND NOT EXISTS (
           SELECT 1
           FROM schedules target
           JOIN schedules origin ON origin.id = NEW.origin_schedule_id
           WHERE target.id = NEW.target_schedule_id
             AND target.review_decision = 'aprobado'
             AND target.program_id = origin.program_id
             AND target.semester_id = origin.semester_id
       ) THEN
        RAISE EXCEPTION
            'RN-18: the target must be a final schedule of the same program and semester'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_change_requests_after_accept() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    current_end timestamptz;
BEGIN
    IF NEW.status IS DISTINCT FROM 'aceptada'
       OR (TG_OP = 'UPDATE' AND OLD.status = 'aceptada') THEN
        RETURN NEW;
    END IF;

    UPDATE student_schedule_assignment
       SET ended_at = NEW.resolved_at
     WHERE student_id = NEW.student_id
       AND schedule_id = NEW.origin_schedule_id
       AND ended_at IS NULL;
    IF NOT FOUND THEN
        RAISE EXCEPTION
            'RN-20: the student is not actively assigned to the origin schedule'
            USING ERRCODE = 'check_violation';
    END IF;

    SELECT ended_at INTO current_end
      FROM student_schedule_assignment
     WHERE student_id = NEW.student_id
       AND schedule_id = NEW.target_schedule_id;
    IF FOUND THEN
        IF current_end IS NULL THEN
            RAISE EXCEPTION
                'RN-20: the student is already assigned to the target schedule'
                USING ERRCODE = 'check_violation';
        END IF;
        UPDATE student_schedule_assignment
           SET ended_at = NULL, assigned_at = NEW.resolved_at
         WHERE student_id = NEW.student_id
           AND schedule_id = NEW.target_schedule_id;
    ELSE
        INSERT INTO student_schedule_assignment (student_id, schedule_id, assigned_at)
        VALUES (NEW.student_id, NEW.target_schedule_id, NEW.resolved_at);
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION fn_attendances_before_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'an attendance record cannot be deleted'
        USING ERRCODE = 'check_violation';
END;
$$;

CREATE TRIGGER trg_schedules_before_write
BEFORE INSERT OR UPDATE ON schedules
FOR EACH ROW EXECUTE FUNCTION fn_schedules_before_write();

CREATE TRIGGER trg_schedules_before_delete
BEFORE DELETE ON schedules
FOR EACH ROW EXECUTE FUNCTION fn_schedules_before_delete();

CREATE TRIGGER trg_coordinator_program_before_write
BEFORE UPDATE OR DELETE ON coordinator_program
FOR EACH ROW EXECUTE FUNCTION fn_coordinator_program_before_write();

CREATE TRIGGER trg_sessions_before_write
BEFORE INSERT OR UPDATE ON schedule_sessions
FOR EACH ROW EXECUTE FUNCTION fn_sessions_before_write();

CREATE TRIGGER trg_sessions_before_delete
BEFORE DELETE ON schedule_sessions
FOR EACH ROW EXECUTE FUNCTION fn_sessions_before_delete();

CREATE TRIGGER trg_semesters_before_update
BEFORE UPDATE ON semesters
FOR EACH ROW EXECUTE FUNCTION fn_semesters_before_update();

CREATE TRIGGER trg_assignments_before_write
BEFORE INSERT OR UPDATE ON student_schedule_assignment
FOR EACH ROW EXECUTE FUNCTION fn_assignments_before_write();

CREATE TRIGGER trg_change_requests_before_write
BEFORE INSERT OR UPDATE ON change_requests
FOR EACH ROW EXECUTE FUNCTION fn_change_requests_before_write();

CREATE TRIGGER trg_change_requests_after_accept
AFTER INSERT OR UPDATE ON change_requests
FOR EACH ROW EXECUTE FUNCTION fn_change_requests_after_accept();

CREATE TRIGGER trg_attendances_before_delete
BEFORE DELETE ON attendances
FOR EACH ROW EXECUTE FUNCTION fn_attendances_before_delete();
"""

_DOWNGRADE_SQL = """
DROP TRIGGER IF EXISTS trg_attendances_before_delete ON attendances;
DROP TRIGGER IF EXISTS trg_change_requests_after_accept ON change_requests;
DROP TRIGGER IF EXISTS trg_change_requests_before_write ON change_requests;
DROP TRIGGER IF EXISTS trg_assignments_before_write ON student_schedule_assignment;
DROP TRIGGER IF EXISTS trg_semesters_before_update ON semesters;
DROP TRIGGER IF EXISTS trg_sessions_before_delete ON schedule_sessions;
DROP TRIGGER IF EXISTS trg_sessions_before_write ON schedule_sessions;
DROP TRIGGER IF EXISTS trg_coordinator_program_before_write ON coordinator_program;
DROP TRIGGER IF EXISTS trg_schedules_before_delete ON schedules;
DROP TRIGGER IF EXISTS trg_schedules_before_write ON schedules;

DROP FUNCTION IF EXISTS fn_attendances_before_delete();
DROP FUNCTION IF EXISTS fn_change_requests_after_accept();
DROP FUNCTION IF EXISTS fn_change_requests_before_write();
DROP FUNCTION IF EXISTS fn_assignments_before_write();
DROP FUNCTION IF EXISTS fn_semesters_before_update();
DROP FUNCTION IF EXISTS fn_sessions_before_delete();
DROP FUNCTION IF EXISTS fn_sessions_before_write();
DROP FUNCTION IF EXISTS fn_coordinator_program_before_write();
DROP FUNCTION IF EXISTS fn_schedules_before_delete();
DROP FUNCTION IF EXISTS fn_schedules_before_write();
DROP FUNCTION IF EXISTS weekday_isodow(weekday);
"""


def _statements(script: str) -> list[str]:
    """Split a script on semicolons, keeping each ``$$`` function body intact.

    Args:
        script: SQL script. Function bodies use dollar quoting.

    Returns:
        The non-empty statements, each still ending with a semicolon.
    """
    chunks: list[str] = []
    buf: list[str] = []
    dollar = False
    for line in script.splitlines(keepends=True):
        buf.append(line)
        stripped = line.strip()
        if stripped.count("$$") % 2 == 1:
            dollar = not dollar
        if not dollar and stripped.endswith(";"):
            statement = "".join(buf).strip()
            if statement:
                chunks.append(statement)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        chunks.append(tail)
    return chunks


def upgrade() -> None:
    """Install the exclusion constraints and the business-rule triggers."""
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        "ALTER TABLE semesters ADD CONSTRAINT ex_semesters_no_overlap "
        "EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)"
    )
    op.execute(
        "ALTER TABLE time_slots ADD CONSTRAINT ex_time_slots_no_overlap "
        "EXCLUDE USING gist ("
        "weekday WITH =, "
        "tsrange((DATE '2000-01-01' + start_time), (DATE '2000-01-01' + end_time)) WITH &&"
        ")"
    )
    for statement in _statements(_UPGRADE_SQL):
        op.execute(statement)


def downgrade() -> None:
    """Remove the triggers and the exclusion constraints."""
    for statement in _statements(_DOWNGRADE_SQL):
        op.execute(statement)
    op.execute("ALTER TABLE time_slots DROP CONSTRAINT IF EXISTS ex_time_slots_no_overlap")
    op.execute("ALTER TABLE semesters DROP CONSTRAINT IF EXISTS ex_semesters_no_overlap")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
