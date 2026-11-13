-- Estrella analítica. Independiente del operativo en oltp.sql.
-- Esquema analytics: sin claves foráneas hacia public (RN-23).
-- Los ENUM viven en analytics para no depender de public.
-- Los identificadores operacionales se copian en columnas *_key, sin FK.
-- dim_block puede repetir un bloque si cambia de clasificación, para que
-- los hechos pasados conserven la complejidad que tenía.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TYPE analytics.activity_type AS ENUM ('teórica', 'práctica', 'laboratorio');
CREATE TYPE analytics.complexity_level AS ENUM ('bajo', 'medio', 'alto');
CREATE TYPE analytics.weekday AS ENUM (
    'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'
);
CREATE TYPE analytics.change_request_status AS ENUM ('pendiente', 'aceptada', 'rechazada');

CREATE TABLE analytics.dim_time (
    id            integer PRIMARY KEY,
    semester_key  integer NOT NULL UNIQUE,
    period        varchar(40) NOT NULL,
    year          integer NOT NULL,
    start_date    date NOT NULL,
    end_date      date NOT NULL,
    CONSTRAINT ck_dim_time_dates_ordered CHECK (end_date > start_date)
);

CREATE TABLE analytics.dim_classroom (
    id             integer PRIMARY KEY,
    classroom_key  integer NOT NULL UNIQUE,
    name           varchar(40) NOT NULL,
    building       varchar(80) NOT NULL,
    capacity       integer NOT NULL
);

CREATE INDEX ix_analytics_dim_classroom_building
    ON analytics.dim_classroom (building);

CREATE TABLE analytics.dim_time_slot (
    id             integer PRIMARY KEY,
    time_slot_key  integer NOT NULL UNIQUE,
    weekday        analytics.weekday NOT NULL,
    label          varchar(40) NOT NULL,
    start_time     time NOT NULL,
    end_time       time NOT NULL,
    CONSTRAINT ck_dim_time_slot_times_ordered CHECK (end_time > start_time)
);

CREATE TABLE analytics.dim_group (
    id    integer PRIMARY KEY,
    name  varchar(40) NOT NULL UNIQUE
);

CREATE TABLE analytics.dim_block (
    id             integer PRIMARY KEY,
    block_key      integer NOT NULL,
    description    varchar NOT NULL,
    subject_name   varchar(160) NOT NULL,
    activity_type  analytics.activity_type NOT NULL,
    complexity     analytics.complexity_level NOT NULL,
    creator_key    integer NOT NULL,
    creator_name   varchar(160) NOT NULL,
    CONSTRAINT uq_dim_block_block_key_activity_type_complexity_subject_name
        UNIQUE (block_key, activity_type, complexity, subject_name)
);

CREATE INDEX ix_analytics_dim_block_block_key ON analytics.dim_block (block_key);

CREATE TABLE analytics.fact_classroom_occupancy (
    id                integer PRIMARY KEY,
    time_id           integer NOT NULL REFERENCES analytics.dim_time (id),
    classroom_id      integer NOT NULL REFERENCES analytics.dim_classroom (id),
    time_slot_id      integer NOT NULL REFERENCES analytics.dim_time_slot (id),
    occupied_minutes  integer NOT NULL,
    session_count     integer NOT NULL,
    CONSTRAINT uq_fact_classroom_occupancy_time_id_classroom_id_time_slot_id
        UNIQUE (time_id, classroom_id, time_slot_id),
    CONSTRAINT ck_fact_classroom_occupancy_occupied_minutes_non_negative
        CHECK (occupied_minutes >= 0),
    CONSTRAINT ck_fact_classroom_occupancy_session_count_non_negative
        CHECK (session_count >= 0)
);

CREATE INDEX ix_analytics_fact_classroom_occupancy_classroom_id
    ON analytics.fact_classroom_occupancy (classroom_id);
CREATE INDEX ix_analytics_fact_classroom_occupancy_time_slot_id
    ON analytics.fact_classroom_occupancy (time_slot_id);

CREATE TABLE analytics.fact_block_attendance (
    id               integer PRIMARY KEY,
    time_id          integer NOT NULL REFERENCES analytics.dim_time (id),
    group_id         integer NOT NULL REFERENCES analytics.dim_group (id),
    block_id         integer NOT NULL REFERENCES analytics.dim_block (id),
    student_key      integer NOT NULL,
    program_key      integer NOT NULL,
    program_name     varchar(160) NOT NULL,
    present_count    integer NOT NULL,
    absent_count     integer NOT NULL,
    attendance_rate  numeric(5, 4) GENERATED ALWAYS AS (
        round(present_count::numeric / NULLIF(present_count + absent_count, 0), 4)
    ) STORED,
    CONSTRAINT uq_fact_block_attendance_time_id_group_id_student_key_program_key_block_id
        UNIQUE (time_id, group_id, student_key, program_key, block_id),
    CONSTRAINT ck_fact_block_attendance_present_count_non_negative
        CHECK (present_count >= 0),
    CONSTRAINT ck_fact_block_attendance_absent_count_non_negative
        CHECK (absent_count >= 0),
    CONSTRAINT ck_fact_block_attendance_has_attendance_records
        CHECK (present_count + absent_count > 0)
);

CREATE INDEX ix_analytics_fact_block_attendance_group_id
    ON analytics.fact_block_attendance (group_id);
CREATE INDEX ix_analytics_fact_block_attendance_block_id
    ON analytics.fact_block_attendance (block_id);
CREATE INDEX ix_analytics_fact_block_attendance_student_key
    ON analytics.fact_block_attendance (student_key);
CREATE INDEX ix_analytics_fact_block_attendance_program_key
    ON analytics.fact_block_attendance (program_key);

CREATE TABLE analytics.fact_change_request (
    id             integer PRIMARY KEY,
    time_id        integer NOT NULL REFERENCES analytics.dim_time (id),
    group_id       integer NOT NULL REFERENCES analytics.dim_group (id),
    student_key    integer NOT NULL,
    program_key    integer NOT NULL,
    program_name   varchar(160) NOT NULL,
    status         analytics.change_request_status NOT NULL,
    request_count  integer NOT NULL,
    CONSTRAINT uq_fact_change_request_time_id_group_id_student_key_program_key_status
        UNIQUE (time_id, group_id, student_key, program_key, status),
    CONSTRAINT ck_fact_change_request_request_count_positive
        CHECK (request_count > 0)
);

CREATE INDEX ix_analytics_fact_change_request_group_id
    ON analytics.fact_change_request (group_id);
CREATE INDEX ix_analytics_fact_change_request_student_key
    ON analytics.fact_change_request (student_key);
CREATE INDEX ix_analytics_fact_change_request_program_key
    ON analytics.fact_change_request (program_key);
