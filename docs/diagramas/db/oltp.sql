-- Modelo operativo (public). El histórico está en olap.sql, esquema analytics.
-- Espejo del esquema implementado en backend/app/models y en Alembic.
-- Solo restricciones declarativas. Los disparadores del informe están pendientes
-- (docs/decisiones-modelos-bd.md §5).
-- Ninguna FK usa ON DELETE CASCADE.

CREATE TYPE activity_type AS ENUM ('teórica', 'práctica', 'laboratorio');
CREATE TYPE complexity_level AS ENUM ('bajo', 'medio', 'alto');
CREATE TYPE review_decision AS ENUM ('aprobado', 'nueva confección');
CREATE TYPE attendance_status AS ENUM ('presente', 'ausente');
CREATE TYPE change_request_status AS ENUM ('pendiente', 'aceptada', 'rechazada');
CREATE TYPE user_role AS ENUM ('administrador', 'coordinador', 'jefe', 'estudiante');
CREATE TYPE weekday AS ENUM (
    'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'
);

CREATE TABLE academic_programs (
    id          integer PRIMARY KEY,
    name        varchar(160) NOT NULL,
    study_plan  varchar(120) NOT NULL
);

CREATE TABLE subjects (
    id    integer PRIMARY KEY,
    name  varchar(160) NOT NULL
);

CREATE TABLE program_subject (
    program_id  integer NOT NULL REFERENCES academic_programs (id),
    subject_id  integer NOT NULL REFERENCES subjects (id),
    PRIMARY KEY (program_id, subject_id)
);

CREATE TABLE coordinators (
    id         integer PRIMARY KEY,
    name       varchar(160) NOT NULL,
    specialty  varchar(120) NOT NULL
);

CREATE TABLE department_heads (
    id    integer PRIMARY KEY,
    name  varchar(160) NOT NULL
);

CREATE TABLE students (
    id          integer PRIMARY KEY,
    name        varchar(160) NOT NULL,
    age         integer NOT NULL,
    group_name  varchar(40) NOT NULL,
    CONSTRAINT ck_students_age_positive CHECK (age > 0)
);

CREATE TABLE coordinator_program (
    coordinator_id  integer NOT NULL REFERENCES coordinators (id),
    program_id      integer NOT NULL REFERENCES academic_programs (id),
    can_generate    boolean NOT NULL,
    can_validate    boolean NOT NULL,
    PRIMARY KEY (coordinator_id, program_id),
    CONSTRAINT ck_coordinator_program_grants_capability
        CHECK (can_generate OR can_validate)
);

CREATE TABLE student_program (
    student_id  integer NOT NULL REFERENCES students (id),
    program_id  integer NOT NULL REFERENCES academic_programs (id),
    PRIMARY KEY (student_id, program_id)
);

CREATE TABLE users (
    id                   integer PRIMARY KEY,
    username             varchar(80) NOT NULL UNIQUE,
    password_hash        varchar(255) NOT NULL,
    role                 user_role NOT NULL,
    is_active            boolean NOT NULL DEFAULT true,
    created_at           timestamptz NOT NULL DEFAULT now(),
    coordinator_id       integer UNIQUE REFERENCES coordinators (id),
    department_head_id   integer UNIQUE REFERENCES department_heads (id),
    student_id           integer UNIQUE REFERENCES students (id),
    CONSTRAINT ck_users_role_matches_profile CHECK (
        (role = 'administrador' AND coordinator_id IS NULL
            AND department_head_id IS NULL AND student_id IS NULL)
        OR (role = 'coordinador' AND coordinator_id IS NOT NULL
            AND department_head_id IS NULL AND student_id IS NULL)
        OR (role = 'jefe' AND department_head_id IS NOT NULL
            AND coordinator_id IS NULL AND student_id IS NULL)
        OR (role = 'estudiante' AND student_id IS NOT NULL
            AND coordinator_id IS NULL AND department_head_id IS NULL)
    )
);

CREATE TABLE content_blocks (
    id             integer PRIMARY KEY,
    subject_id     integer NOT NULL REFERENCES subjects (id),
    description    text NOT NULL,
    activity_type  activity_type NOT NULL,
    complexity     complexity_level NOT NULL,
    creator_id     integer NOT NULL REFERENCES coordinators (id)
);

-- RN-03. La collation ICU pliega también las letras acentuadas.
CREATE UNIQUE INDEX uq_content_blocks_subject_activity_description
    ON content_blocks (
        subject_id,
        activity_type,
        md5(lower(btrim(description) COLLATE "und-x-icu"))
    );

CREATE TABLE classrooms (
    id        integer PRIMARY KEY,
    name      varchar(40) NOT NULL,
    building  varchar(80) NOT NULL,
    capacity  integer NOT NULL,
    CONSTRAINT uq_classrooms_building_name UNIQUE (building, name),
    CONSTRAINT ck_classrooms_capacity_positive CHECK (capacity > 0)
);

CREATE TABLE semesters (
    id          integer PRIMARY KEY,
    name        varchar(40) NOT NULL UNIQUE,
    start_date  date NOT NULL UNIQUE,
    end_date    date NOT NULL UNIQUE,
    CONSTRAINT ck_semesters_dates_ordered CHECK (end_date > start_date)
);

CREATE TABLE time_slots (
    id          integer PRIMARY KEY,
    weekday     weekday NOT NULL,
    start_time  time NOT NULL,
    end_time    time NOT NULL,
    CONSTRAINT uq_time_slots_weekday_start_time UNIQUE (weekday, start_time),
    CONSTRAINT uq_time_slots_weekday_end_time UNIQUE (weekday, end_time),
    CONSTRAINT ck_time_slots_times_ordered CHECK (end_time > start_time)
);

CREATE TABLE schedules (
    id                    integer PRIMARY KEY,
    program_id            integer NOT NULL REFERENCES academic_programs (id),
    semester_id           integer NOT NULL REFERENCES semesters (id),
    creator_id            integer NOT NULL REFERENCES coordinators (id),
    created_at            timestamptz NOT NULL DEFAULT now(),
    theory_ratio          numeric(4, 3) NOT NULL,
    practice_ratio        numeric(4, 3) NOT NULL,
    lab_ratio             numeric(4, 3) NOT NULL,
    subject_coverage      numeric(4, 3) NOT NULL,
    block_count           integer NOT NULL,
    previous_schedule_id  integer UNIQUE REFERENCES schedules (id),
    validator_id          integer REFERENCES coordinators (id),
    validated_at          timestamptz,
    validation_notes      text,
    head_id               integer REFERENCES department_heads (id),
    reviewed_at           timestamptz,
    review_decision       review_decision,
    review_notes          text,
    CONSTRAINT ck_schedules_theory_ratio_range CHECK (theory_ratio BETWEEN 0 AND 1),
    CONSTRAINT ck_schedules_practice_ratio_range CHECK (practice_ratio BETWEEN 0 AND 1),
    CONSTRAINT ck_schedules_lab_ratio_range CHECK (lab_ratio BETWEEN 0 AND 1),
    CONSTRAINT ck_schedules_ratios_sum_one
        CHECK (theory_ratio + practice_ratio + lab_ratio = 1),
    CONSTRAINT ck_schedules_subject_coverage_range CHECK (subject_coverage BETWEEN 0 AND 1),
    CONSTRAINT ck_schedules_block_count_positive CHECK (block_count > 0),
    CONSTRAINT ck_schedules_not_replacing_itself CHECK (previous_schedule_id <> id),
    CONSTRAINT ck_schedules_validation_complete
        CHECK ((validator_id IS NULL) = (validated_at IS NULL)),
    CONSTRAINT ck_schedules_validation_notes_valid
        CHECK (validation_notes IS NULL OR validator_id IS NOT NULL),
    CONSTRAINT ck_schedules_validated_after_creation CHECK (validated_at >= created_at),
    CONSTRAINT ck_schedules_review_complete CHECK (
        (head_id IS NULL AND reviewed_at IS NULL AND review_decision IS NULL)
        OR (head_id IS NOT NULL AND reviewed_at IS NOT NULL AND review_decision IS NOT NULL)
    ),
    CONSTRAINT ck_schedules_review_notes_valid
        CHECK (review_notes IS NULL OR head_id IS NOT NULL),
    CONSTRAINT ck_schedules_reviewed_after_creation CHECK (reviewed_at >= created_at)
);

-- Un horario es final si y solo si review_decision = 'aprobado' (RN-11).

CREATE TABLE schedule_sessions (
    schedule_id   integer NOT NULL REFERENCES schedules (id),
    block_id      integer NOT NULL REFERENCES content_blocks (id),
    classroom_id  integer NOT NULL REFERENCES classrooms (id),
    time_slot_id  integer NOT NULL REFERENCES time_slots (id),
    session_date  date NOT NULL,
    PRIMARY KEY (schedule_id, block_id),
    CONSTRAINT uq_schedule_sessions_schedule_id_time_slot_id_session_date
        UNIQUE (schedule_id, time_slot_id, session_date)
);

CREATE TABLE student_schedule_assignment (
    student_id   integer NOT NULL REFERENCES students (id),
    schedule_id  integer NOT NULL REFERENCES schedules (id),
    assigned_at  timestamptz NOT NULL DEFAULT now(),
    ended_at     timestamptz,
    PRIMARY KEY (student_id, schedule_id),
    CONSTRAINT ck_student_schedule_assignment_ended_after_assigned
        CHECK (ended_at >= assigned_at)
);

CREATE TABLE attendances (
    student_id   integer NOT NULL,
    schedule_id  integer NOT NULL,
    block_id     integer NOT NULL,
    status       attendance_status NOT NULL,
    PRIMARY KEY (student_id, schedule_id, block_id),
    FOREIGN KEY (schedule_id, block_id)
        REFERENCES schedule_sessions (schedule_id, block_id),
    FOREIGN KEY (student_id, schedule_id)
        REFERENCES student_schedule_assignment (student_id, schedule_id)
);

CREATE TABLE change_requests (
    id                        integer PRIMARY KEY,
    student_id                integer NOT NULL REFERENCES students (id),
    reason                    text NOT NULL,
    requested_at              timestamptz NOT NULL DEFAULT now(),
    status                    change_request_status NOT NULL DEFAULT 'pendiente',
    resolved_at               timestamptz,
    origin_schedule_id        integer NOT NULL REFERENCES schedules (id),
    target_schedule_id        integer REFERENCES schedules (id),
    attending_coordinator_id  integer NOT NULL REFERENCES coordinators (id),
    support_coordinator_id    integer REFERENCES coordinators (id),
    CONSTRAINT ck_change_requests_status_consistent CHECK (
        (status = 'pendiente' AND resolved_at IS NULL AND target_schedule_id IS NULL)
        OR (status = 'aceptada' AND resolved_at IS NOT NULL AND target_schedule_id IS NOT NULL)
        OR (status = 'rechazada' AND resolved_at IS NOT NULL AND target_schedule_id IS NULL)
    ),
    CONSTRAINT ck_change_requests_resolved_after_requested
        CHECK (resolved_at >= requested_at),
    CONSTRAINT ck_change_requests_target_differs
        CHECK (target_schedule_id <> origin_schedule_id),
    CONSTRAINT ck_change_requests_support_differs
        CHECK (support_coordinator_id <> attending_coordinator_id)
);
