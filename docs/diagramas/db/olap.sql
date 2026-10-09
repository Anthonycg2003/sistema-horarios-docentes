-- Almacén analítico independiente del OLTP.
-- Esquema estrella en un schema distinto. No hay clave foránea hacia la operación.
-- dim_tiempo es una sola dimensión, compartida por los dos hechos.
-- La ocupación es por aula y franja (con día). El hecho de asistencia conserva
-- estudiante, grupo, programa y bloque (complejidad y creador). El promedio
-- del grupo sale de ese hecho. La solicitud de cambio permanece en el OLTP.

CREATE SCHEMA IF NOT EXISTS analitica;

CREATE TABLE analitica.dim_tiempo (
    id          SERIAL PRIMARY KEY,
    periodo     VARCHAR(20) NOT NULL UNIQUE,
    anio        INTEGER NOT NULL,
    semestre    SMALLINT NOT NULL
);

CREATE TABLE analitica.dim_aula (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL,
    edificio    VARCHAR(80) NOT NULL,
    CONSTRAINT uq_dim_aula UNIQUE (nombre, edificio)
);

CREATE TABLE analitica.dim_franja (
    id          SERIAL PRIMARY KEY,
    dia         VARCHAR(12) NOT NULL,
    etiqueta    VARCHAR(40) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin    TIME NOT NULL,
    CONSTRAINT ck_franja_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT uq_dim_franja UNIQUE (dia, hora_inicio, hora_fin)
);

CREATE TABLE analitica.dim_grupo (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE analitica.dim_bloque (
    id              SERIAL PRIMARY KEY,
    titulo          VARCHAR(200) NOT NULL,
    asignatura      VARCHAR(160) NOT NULL,
    complejidad     VARCHAR(10) NOT NULL,
    creador         VARCHAR(160) NOT NULL,
    CONSTRAINT ck_dim_bloque_complejidad CHECK (
        complejidad IN ('bajo', 'medio', 'alto')
    ),
    CONSTRAINT uq_dim_bloque UNIQUE (titulo, asignatura, complejidad, creador)
);

CREATE TABLE analitica.fact_ocupacion_aula (
    id                      BIGSERIAL PRIMARY KEY,
    tiempo_id               INTEGER NOT NULL REFERENCES analitica.dim_tiempo(id),
    aula_id                 INTEGER NOT NULL REFERENCES analitica.dim_aula(id),
    franja_id               INTEGER NOT NULL REFERENCES analitica.dim_franja(id),
    minutos_ocupados        NUMERIC(12,2) NOT NULL,
    sesiones                INTEGER NOT NULL,
    CONSTRAINT uq_ocupacion UNIQUE (tiempo_id, aula_id, franja_id)
);

CREATE TABLE analitica.fact_asistencia_bloque (
    id                          BIGSERIAL PRIMARY KEY,
    tiempo_id                   INTEGER NOT NULL REFERENCES analitica.dim_tiempo(id),
    grupo_id                    INTEGER NOT NULL REFERENCES analitica.dim_grupo(id),
    bloque_id                   INTEGER NOT NULL REFERENCES analitica.dim_bloque(id),
    estudiante_identificador    VARCHAR(80) NOT NULL,
    programa                    VARCHAR(160) NOT NULL,
    presentes                   INTEGER NOT NULL,
    ausentes                    INTEGER NOT NULL,
    tasa_asistencia             NUMERIC(5,4) NOT NULL,
    CONSTRAINT uq_asistencia_analitica UNIQUE (
        tiempo_id, grupo_id, estudiante_identificador, programa, bloque_id
    )
);

CREATE INDEX idx_fact_ocupacion_periodo ON analitica.fact_ocupacion_aula (tiempo_id);
CREATE INDEX idx_fact_asistencia_periodo ON analitica.fact_asistencia_bloque (tiempo_id);
CREATE INDEX idx_fact_asistencia_grupo ON analitica.fact_asistencia_bloque (grupo_id);
