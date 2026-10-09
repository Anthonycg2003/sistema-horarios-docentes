-- Modelo OLTP (PostgreSQL). Independiente del almacén analítico en db/olap.sql.
-- Una asignatura pertenece a un solo programa y no lleva código ni créditos.
-- El grupo es atributo del estudiante. La franja es catálogo. La sesión exige
-- aula y franja; la fecha de cada clase está en la asistencia. Quien valida
-- un horario es un usuario coordinador con puede_validar en ese programa.
-- Quien lo aprueba es un usuario con rol jefe. Un horario puede acumular
-- varios actos de aprobación, y el sucesor es del mismo programa. La
-- asignación doble es el solape de sesiones, no un segundo horario del mismo
-- programa y semestre. Dos franjas del mismo día
-- no se cruzan, y un aula vigente tampoco. El bloque de la sesión pertenece
-- al programa del horario.

CREATE TABLE usuarios (
    id              UUID PRIMARY KEY,
    identificador   VARCHAR(80) NOT NULL UNIQUE,
    nombre          VARCHAR(160) NOT NULL,
    rol             VARCHAR(32) NOT NULL,
    password_hash   VARCHAR(128) NOT NULL,
    coordinador_id  UUID,
    estudiante_id   UUID,
    CONSTRAINT ck_usuario_rol CHECK (
        rol IN ('administrador', 'coordinador', 'estudiante', 'jefe')
    )
);

CREATE TABLE programas_academicos (
    id              UUID PRIMARY KEY,
    codigo          VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(160) NOT NULL,
    plan_estudios   VARCHAR(120) NOT NULL
);

CREATE TABLE asignaturas (
    id              UUID PRIMARY KEY,
    nombre          VARCHAR(160) NOT NULL,
    programa_id     UUID NOT NULL REFERENCES programas_academicos(id),
    CONSTRAINT uq_asignatura_nombre_programa UNIQUE (nombre, programa_id)
);

CREATE TABLE coordinadores (
    id              UUID PRIMARY KEY,
    usuario_id      UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    especialidad    VARCHAR(120) NOT NULL
);

CREATE TABLE coordinador_programa (
    coordinador_id  UUID NOT NULL REFERENCES coordinadores(id),
    programa_id     UUID NOT NULL REFERENCES programas_academicos(id),
    puede_generar   BOOLEAN NOT NULL DEFAULT TRUE,
    puede_validar   BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (coordinador_id, programa_id)
);

CREATE TABLE estudiantes (
    id              UUID PRIMARY KEY,
    usuario_id      UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    edad            INTEGER NOT NULL,
    grupo           VARCHAR(80) NOT NULL,
    CONSTRAINT ck_estudiante_edad CHECK (edad > 0)
);

CREATE TABLE estudiante_programa (
    estudiante_id   UUID NOT NULL REFERENCES estudiantes(id),
    programa_id     UUID NOT NULL REFERENCES programas_academicos(id),
    PRIMARY KEY (estudiante_id, programa_id)
);

ALTER TABLE usuarios
    ADD CONSTRAINT fk_usuarios_coordinador
        FOREIGN KEY (coordinador_id) REFERENCES coordinadores(id)
        DEFERRABLE INITIALLY DEFERRED,
    ADD CONSTRAINT fk_usuarios_estudiante
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE bloques_contenido (
    id                  UUID PRIMARY KEY,
    titulo              VARCHAR(200) NOT NULL,
    descripcion         TEXT NOT NULL,
    asignatura_id       UUID NOT NULL REFERENCES asignaturas(id),
    tipo_actividad      VARCHAR(20) NOT NULL,
    complejidad         VARCHAR(10) NOT NULL,
    duracion_minutos    INTEGER NOT NULL DEFAULT 90,
    creador_id          UUID NOT NULL REFERENCES coordinadores(id),
    hash_duplicado      VARCHAR(64) NOT NULL,
    CONSTRAINT ck_bloque_tipo CHECK (
        tipo_actividad IN ('teórica', 'práctica', 'laboratorio')
    ),
    CONSTRAINT ck_bloque_complejidad CHECK (
        complejidad IN ('bajo', 'medio', 'alto')
    ),
    CONSTRAINT ck_bloque_duracion CHECK (duracion_minutos > 0),
    CONSTRAINT uq_bloque_contenido UNIQUE (descripcion, asignatura_id, tipo_actividad),
    CONSTRAINT uq_bloque_hash UNIQUE (hash_duplicado)
);

CREATE TABLE aulas (
    id          UUID PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL UNIQUE,
    edificio    VARCHAR(80) NOT NULL,
    capacidad   INTEGER NOT NULL,
    CONSTRAINT ck_aula_capacidad CHECK (capacidad > 0)
);

CREATE TABLE franjas_horarias (
    id              UUID PRIMARY KEY,
    dia             VARCHAR(12) NOT NULL,
    hora_inicio     TIME NOT NULL,
    hora_fin        TIME NOT NULL,
    CONSTRAINT ck_franja_dia CHECK (
        dia IN ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado')
    ),
    CONSTRAINT ck_franja_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT uq_franja UNIQUE (dia, hora_inicio, hora_fin)
);

CREATE TABLE horarios (
    id                          UUID PRIMARY KEY,
    programa_id                 UUID NOT NULL REFERENCES programas_academicos(id),
    creador_id                  UUID NOT NULL REFERENCES coordinadores(id),
    fecha_creacion              TIMESTAMPTZ NOT NULL,
    estado                      VARCHAR(20) NOT NULL,
    semestre                    VARCHAR(20) NOT NULL,
    generado_automaticamente    BOOLEAN NOT NULL DEFAULT TRUE,
    proporcion_teorica          NUMERIC(4,3) NOT NULL,
    proporcion_practica         NUMERIC(4,3) NOT NULL,
    proporcion_laboratorio      NUMERIC(4,3) NOT NULL,
    cobertura_minima            NUMERIC(4,3) NOT NULL,
    cantidad_total_bloques      INTEGER NOT NULL,
    estrategia                  VARCHAR(40) NOT NULL,
    equilibrio_cumplido         BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_horario_estado CHECK (
        estado IN ('borrador', 'en revisión', 'aprobado', 'sustituido')
    ),
    CONSTRAINT ck_horario_parametros CHECK (
        proporcion_teorica BETWEEN 0 AND 1
        AND proporcion_practica BETWEEN 0 AND 1
        AND proporcion_laboratorio BETWEEN 0 AND 1
        AND cobertura_minima BETWEEN 0 AND 1
        AND proporcion_teorica + proporcion_practica + proporcion_laboratorio = 1
        AND cantidad_total_bloques > 0
    )
);

CREATE TABLE sesiones_horario (
    id              UUID PRIMARY KEY,
    horario_id      UUID NOT NULL REFERENCES horarios(id) ON DELETE CASCADE,
    bloque_id       UUID NOT NULL REFERENCES bloques_contenido(id),
    aula_id         UUID NOT NULL REFERENCES aulas(id),
    franja_id       UUID NOT NULL REFERENCES franjas_horarias(id),
    CONSTRAINT uq_sesion_aula_franja UNIQUE (horario_id, aula_id, franja_id)
);

CREATE TABLE proyeccion_disponibilidad (
    aula_id     UUID NOT NULL REFERENCES aulas(id),
    franja_id   UUID NOT NULL REFERENCES franjas_horarias(id),
    horario_id  UUID NOT NULL REFERENCES horarios(id),
    PRIMARY KEY (aula_id, franja_id)
);

CREATE TABLE asignacion_estudiante_horario (
    estudiante_id   UUID NOT NULL REFERENCES estudiantes(id),
    horario_id      UUID NOT NULL REFERENCES horarios(id),
    PRIMARY KEY (estudiante_id, horario_id)
);

CREATE TABLE validaciones_horario (
    id              UUID PRIMARY KEY,
    horario_id      UUID NOT NULL REFERENCES horarios(id),
    revisor_id      UUID NOT NULL REFERENCES usuarios(id),
    fecha           TIMESTAMPTZ NOT NULL,
    decision        VARCHAR(12) NOT NULL,
    observaciones   TEXT,
    CONSTRAINT ck_validacion_decision CHECK (decision IN ('validado', 'observado'))
);

CREATE TABLE aprobaciones_horario (
    id              UUID PRIMARY KEY,
    horario_id      UUID NOT NULL REFERENCES horarios(id),
    revisor_id      UUID NOT NULL REFERENCES usuarios(id),
    fecha           TIMESTAMPTZ NOT NULL,
    decision            VARCHAR(24) NOT NULL,
    observaciones       TEXT,
    horario_sucesor_id  UUID REFERENCES horarios(id),
    CONSTRAINT ck_aprobacion_decision CHECK (decision IN ('aprobado', 'nueva confección')),
    CONSTRAINT ck_aprobacion_sucesor CHECK (
        horario_sucesor_id IS DISTINCT FROM horario_id
        AND (
            (decision = 'aprobado' AND horario_sucesor_id IS NULL)
            OR (decision = 'nueva confección' AND horario_sucesor_id IS NOT NULL)
        )
    )
);

CREATE TABLE asistencias (
    id              UUID PRIMARY KEY,
    sesion_id       UUID NOT NULL REFERENCES sesiones_horario(id),
    estudiante_id   UUID NOT NULL REFERENCES estudiantes(id),
    estado          VARCHAR(12) NOT NULL,
    fecha           DATE NOT NULL,
    CONSTRAINT ck_asistencia_estado CHECK (estado IN ('presente', 'ausente')),
    CONSTRAINT uq_asistencia UNIQUE (sesion_id, estudiante_id, fecha)
);

CREATE TABLE solicitudes_cambio (
    id                          UUID PRIMARY KEY,
    estudiante_id               UUID NOT NULL REFERENCES estudiantes(id),
    horario_origen_id           UUID NOT NULL REFERENCES horarios(id),
    horario_destino_id          UUID REFERENCES horarios(id),
    coordinador_asignado_id     UUID NOT NULL REFERENCES coordinadores(id),
    coordinador_apoyo_id        UUID REFERENCES coordinadores(id),
    motivo                      TEXT NOT NULL,
    estado                      VARCHAR(16) NOT NULL,
    fecha_solicitud             TIMESTAMPTZ NOT NULL,
    fecha_resolucion            TIMESTAMPTZ,
    resultado                   VARCHAR(32),
    CONSTRAINT ck_solicitud_coherente CHECK (
        (
            estado = 'pendiente'
            AND resultado IS NULL
            AND fecha_resolucion IS NULL
            AND horario_destino_id IS NULL
        )
        OR (
            estado = 'resuelta'
            AND fecha_resolucion IS NOT NULL
            AND (
                (resultado IN ('aceptado', 'rechazado') AND horario_destino_id IS NULL)
                OR (resultado = 'nuevo horario asignado' AND horario_destino_id IS NOT NULL)
            )
        )
    )
);

-- Especialización total y disjunta. Se difiere al fin de la transacción para
-- poder insertar el usuario y su subtipo en cualquier orden dentro de ella.
CREATE OR REPLACE FUNCTION ck_usuario_especializacion() RETURNS trigger AS $$
BEGIN
    IF NEW.rol = 'coordinador' THEN
        IF NEW.estudiante_id IS NOT NULL OR NEW.coordinador_id IS NULL THEN
            RAISE EXCEPTION 'un coordinador apunta solo a su fila de coordinadores';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM coordinadores c
            WHERE c.id = NEW.coordinador_id AND c.usuario_id = NEW.id
        ) THEN
            RAISE EXCEPTION 'la fila de coordinador no corresponde a este usuario';
        END IF;
    ELSIF NEW.rol = 'estudiante' THEN
        IF NEW.coordinador_id IS NOT NULL OR NEW.estudiante_id IS NULL THEN
            RAISE EXCEPTION 'un estudiante apunta solo a su fila de estudiantes';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM estudiantes e
            WHERE e.id = NEW.estudiante_id AND e.usuario_id = NEW.id
        ) THEN
            RAISE EXCEPTION 'la fila de estudiante no corresponde a este usuario';
        END IF;
    ELSIF NEW.rol IN ('administrador', 'jefe') THEN
        IF NEW.coordinador_id IS NOT NULL OR NEW.estudiante_id IS NOT NULL THEN
            RAISE EXCEPTION 'administrador y jefe no tienen subtipo';
        END IF;
    ELSE
        RAISE EXCEPTION 'rol de usuario no admitido';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_usuario_especializacion
    AFTER INSERT OR UPDATE ON usuarios
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION ck_usuario_especializacion();

CREATE OR REPLACE FUNCTION ck_coordinador_usuario() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM usuarios u
        WHERE u.id = NEW.usuario_id
          AND u.rol = 'coordinador'
          AND u.coordinador_id = NEW.id
    ) THEN
        RAISE EXCEPTION 'el usuario no queda especializado como este coordinador';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_coordinador_usuario
    AFTER INSERT OR UPDATE ON coordinadores
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION ck_coordinador_usuario();

CREATE OR REPLACE FUNCTION ck_estudiante_usuario() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM usuarios u
        WHERE u.id = NEW.usuario_id
          AND u.rol = 'estudiante'
          AND u.estudiante_id = NEW.id
    ) THEN
        RAISE EXCEPTION 'el usuario no queda especializado como este estudiante';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_estudiante_usuario
    AFTER INSERT OR UPDATE ON estudiantes
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION ck_estudiante_usuario();

CREATE OR REPLACE FUNCTION ck_creador_autorizado() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM coordinador_programa cp
        WHERE cp.coordinador_id = NEW.creador_id
          AND cp.programa_id = NEW.programa_id
          AND cp.puede_generar
    ) THEN
        RAISE EXCEPTION 'el creador no está autorizado a generar en ese programa';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_horario_creador_autorizado
    BEFORE INSERT OR UPDATE OF creador_id, programa_id ON horarios
    FOR EACH ROW
    EXECUTE FUNCTION ck_creador_autorizado();

CREATE OR REPLACE FUNCTION ck_revisor_puede_validar() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM horarios h
        JOIN usuarios u
          ON u.id = NEW.revisor_id
         AND u.rol = 'coordinador'
        JOIN coordinador_programa cp
          ON cp.coordinador_id = u.coordinador_id
         AND cp.programa_id = h.programa_id
         AND cp.puede_validar
        WHERE h.id = NEW.horario_id
    ) THEN
        RAISE EXCEPTION 'quien valida el horario es un coordinador autorizado a validar ese programa';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validacion_revisor_autorizado
    BEFORE INSERT OR UPDATE OF revisor_id, horario_id ON validaciones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_revisor_puede_validar();

CREATE OR REPLACE FUNCTION ck_aprobador_es_jefe() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM usuarios u
        WHERE u.id = NEW.revisor_id AND u.rol = 'jefe'
    ) THEN
        RAISE EXCEPTION 'quien aprueba el horario es el jefe de departamento';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aprobacion_revisor_jefe
    BEFORE INSERT OR UPDATE OF revisor_id ON aprobaciones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_aprobador_es_jefe();

CREATE OR REPLACE FUNCTION sesiones_se_solapan(
    dia_a VARCHAR, inicio_a TIME, fin_a TIME,
    dia_b VARCHAR, inicio_b TIME, fin_b TIME
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN dia_a = dia_b AND inicio_a < fin_b AND inicio_b < fin_a;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION ck_asignacion_sin_solape() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM asignacion_estudiante_horario a
        JOIN sesiones_horario propia ON propia.horario_id = NEW.horario_id
        JOIN franjas_horarias franja_propia ON franja_propia.id = propia.franja_id
        JOIN sesiones_horario ajena ON ajena.horario_id = a.horario_id
        JOIN franjas_horarias franja_ajena ON franja_ajena.id = ajena.franja_id
        WHERE a.estudiante_id = NEW.estudiante_id
          AND a.horario_id <> NEW.horario_id
          AND sesiones_se_solapan(
                franja_propia.dia, franja_propia.hora_inicio, franja_propia.hora_fin,
                franja_ajena.dia, franja_ajena.hora_inicio, franja_ajena.hora_fin
          )
    ) THEN
        RAISE EXCEPTION 'el estudiante ya tiene una sesión en esa franja';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_asignacion_sin_solape
    BEFORE INSERT OR UPDATE ON asignacion_estudiante_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_asignacion_sin_solape();

CREATE OR REPLACE FUNCTION ck_sesion_sin_solape() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sesiones_horario s
        JOIN franjas_horarias franja_s ON franja_s.id = s.franja_id
        JOIN franjas_horarias franja_nueva ON franja_nueva.id = NEW.franja_id
        WHERE s.horario_id = NEW.horario_id
          AND s.id <> NEW.id
          AND sesiones_se_solapan(
                franja_s.dia, franja_s.hora_inicio, franja_s.hora_fin,
                franja_nueva.dia, franja_nueva.hora_inicio, franja_nueva.hora_fin
          )
    ) THEN
        RAISE EXCEPTION 'dos sesiones del mismo horario se solapan';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM asignacion_estudiante_horario propia
        JOIN asignacion_estudiante_horario ajena
          ON ajena.estudiante_id = propia.estudiante_id
         AND ajena.horario_id <> NEW.horario_id
        JOIN sesiones_horario s ON s.horario_id = ajena.horario_id
        JOIN franjas_horarias franja_s ON franja_s.id = s.franja_id
        JOIN franjas_horarias franja_nueva ON franja_nueva.id = NEW.franja_id
        WHERE propia.horario_id = NEW.horario_id
          AND sesiones_se_solapan(
                franja_s.dia, franja_s.hora_inicio, franja_s.hora_fin,
                franja_nueva.dia, franja_nueva.hora_inicio, franja_nueva.hora_fin
          )
    ) THEN
        RAISE EXCEPTION 'la sesión solapa otro horario ya asignado al estudiante';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sesion_sin_solape
    BEFORE INSERT OR UPDATE OF horario_id, franja_id
    ON sesiones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_sesion_sin_solape();

CREATE OR REPLACE FUNCTION ck_asistencia_de_asignado() RETURNS trigger AS $$
DECLARE
    horario UUID;
BEGIN
    SELECT s.horario_id INTO horario
    FROM sesiones_horario s
    WHERE s.id = NEW.sesion_id;

    IF horario IS NULL OR NOT EXISTS (
        SELECT 1 FROM asignacion_estudiante_horario a
        WHERE a.estudiante_id = NEW.estudiante_id
          AND a.horario_id = horario
    ) THEN
        RAISE EXCEPTION 'solo asiste un estudiante asignado a ese horario';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_asistencia_de_asignado
    BEFORE INSERT OR UPDATE OF sesion_id, estudiante_id ON asistencias
    FOR EACH ROW
    EXECUTE FUNCTION ck_asistencia_de_asignado();

CREATE OR REPLACE FUNCTION ck_bloque_hash() RETURNS trigger AS $$
BEGIN
    NEW.hash_duplicado := md5(
        NEW.descripcion || NEW.asignatura_id::text || NEW.tipo_actividad
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bloque_hash
    BEFORE INSERT OR UPDATE OF descripcion, asignatura_id, tipo_actividad
    ON bloques_contenido
    FOR EACH ROW
    EXECUTE FUNCTION ck_bloque_hash();

CREATE OR REPLACE FUNCTION ck_asignacion_matricula() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM horarios h
        JOIN estudiante_programa ep
          ON ep.programa_id = h.programa_id
         AND ep.estudiante_id = NEW.estudiante_id
        WHERE h.id = NEW.horario_id
    ) THEN
        RAISE EXCEPTION 'el estudiante no está matriculado en el programa del horario';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_asignacion_matricula
    BEFORE INSERT OR UPDATE ON asignacion_estudiante_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_asignacion_matricula();

CREATE OR REPLACE FUNCTION ck_aula_entre_horarios() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sesiones_horario s
        JOIN horarios ajeno ON ajeno.id = s.horario_id
        JOIN horarios propio ON propio.id = NEW.horario_id
        JOIN franjas_horarias franja_ajena ON franja_ajena.id = s.franja_id
        JOIN franjas_horarias franja_nueva ON franja_nueva.id = NEW.franja_id
        WHERE s.aula_id = NEW.aula_id
          AND s.horario_id <> NEW.horario_id
          AND s.id IS DISTINCT FROM NEW.id
          AND ajeno.estado <> 'sustituido'
          AND propio.estado <> 'sustituido'
          AND sesiones_se_solapan(
                franja_ajena.dia, franja_ajena.hora_inicio, franja_ajena.hora_fin,
                franja_nueva.dia, franja_nueva.hora_inicio, franja_nueva.hora_fin
          )
    ) THEN
        RAISE EXCEPTION 'el aula ya está ocupada en esa franja por otro horario vigente';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aula_entre_horarios
    BEFORE INSERT OR UPDATE OF aula_id, franja_id, horario_id
    ON sesiones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_aula_entre_horarios();

CREATE OR REPLACE FUNCTION ck_horario_estado_aula() RETURNS trigger AS $$
BEGIN
    IF NEW.estado <> 'sustituido' AND NEW.estado IS DISTINCT FROM OLD.estado THEN
        IF EXISTS (
            SELECT 1
            FROM sesiones_horario propia
            JOIN franjas_horarias franja_propia ON franja_propia.id = propia.franja_id
            JOIN sesiones_horario ajena
              ON ajena.aula_id = propia.aula_id
             AND ajena.horario_id <> NEW.id
            JOIN franjas_horarias franja_ajena ON franja_ajena.id = ajena.franja_id
            JOIN horarios h ON h.id = ajena.horario_id
            WHERE propia.horario_id = NEW.id
              AND h.estado <> 'sustituido'
              AND sesiones_se_solapan(
                    franja_propia.dia, franja_propia.hora_inicio, franja_propia.hora_fin,
                    franja_ajena.dia, franja_ajena.hora_inicio, franja_ajena.hora_fin
              )
        ) THEN
            RAISE EXCEPTION 'al dejar el horario vigente, un aula queda ocupada en la misma franja';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_horario_estado_aula
    BEFORE UPDATE OF estado ON horarios
    FOR EACH ROW
    EXECUTE FUNCTION ck_horario_estado_aula();

CREATE OR REPLACE FUNCTION ck_horario_estado_por_aprobacion() RETURNS trigger AS $$
BEGIN
    IF NEW.estado = 'aprobado' AND NOT EXISTS (
        SELECT 1 FROM aprobaciones_horario a
        WHERE a.horario_id = NEW.id AND a.decision = 'aprobado'
    ) THEN
        RAISE EXCEPTION 'el estado aprobado solo lo escribe una aprobación';
    END IF;
    IF NEW.estado = 'sustituido' AND NOT EXISTS (
        SELECT 1 FROM aprobaciones_horario a
        WHERE a.horario_id = NEW.id
          AND a.decision = 'nueva confección'
          AND a.horario_sucesor_id IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'el estado sustituido exige una aprobación con horario sucesor';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_horario_estado_por_aprobacion
    BEFORE INSERT OR UPDATE OF estado ON horarios
    FOR EACH ROW
    EXECUTE FUNCTION ck_horario_estado_por_aprobacion();

CREATE OR REPLACE FUNCTION ck_aprobacion_admite() RETURNS trigger AS $$
DECLARE
    programa UUID;
BEGIN
    IF TG_OP = 'UPDATE' AND (
        OLD.decision IS DISTINCT FROM NEW.decision
        OR OLD.horario_id IS DISTINCT FROM NEW.horario_id
        OR OLD.horario_sucesor_id IS DISTINCT FROM NEW.horario_sucesor_id
        OR OLD.revisor_id IS DISTINCT FROM NEW.revisor_id
    ) THEN
        RAISE EXCEPTION 'la aprobación no se reescribe: otra confección es un horario nuevo';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        RETURN NEW;
    END IF;

    SELECT programa_id INTO programa
    FROM horarios
    WHERE id = NEW.horario_id;

    IF NEW.decision = 'nueva confección' AND NOT EXISTS (
        SELECT 1 FROM horarios s
        WHERE s.id = NEW.horario_sucesor_id
          AND s.programa_id = programa
          AND s.estado <> 'sustituido'
    ) THEN
        RAISE EXCEPTION 'el sucesor es otro horario del mismo programa y no está sustituido';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aprobacion_admite
    BEFORE INSERT OR UPDATE ON aprobaciones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_aprobacion_admite();

CREATE OR REPLACE FUNCTION ck_aprobacion_escribe_estado() RETURNS trigger AS $$
BEGIN
    IF NEW.decision = 'aprobado' THEN
        UPDATE horarios SET estado = 'aprobado' WHERE id = NEW.horario_id;
    ELSE
        UPDATE horarios SET estado = 'sustituido' WHERE id = NEW.horario_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aprobacion_escribe_estado
    AFTER INSERT ON aprobaciones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_aprobacion_escribe_estado();

CREATE OR REPLACE FUNCTION refrescar_disponibilidad() RETURNS void AS $$
BEGIN
    DELETE FROM proyeccion_disponibilidad;
    INSERT INTO proyeccion_disponibilidad (aula_id, franja_id, horario_id)
    SELECT s.aula_id, s.franja_id, s.horario_id
    FROM sesiones_horario s
    JOIN horarios h ON h.id = s.horario_id
    WHERE h.estado <> 'sustituido';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_refrescar_disponibilidad() RETURNS trigger AS $$
BEGIN
    PERFORM refrescar_disponibilidad();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sesion_refresca_disponibilidad
    AFTER INSERT OR UPDATE OR DELETE ON sesiones_horario
    FOR EACH STATEMENT
    EXECUTE FUNCTION trg_refrescar_disponibilidad();

CREATE TRIGGER trg_horario_refresca_disponibilidad
    AFTER UPDATE OF estado ON horarios
    FOR EACH STATEMENT
    EXECUTE FUNCTION trg_refrescar_disponibilidad();

CREATE OR REPLACE FUNCTION ck_franja_sin_solape() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM franjas_horarias f
        WHERE f.id <> NEW.id
          AND sesiones_se_solapan(
                f.dia, f.hora_inicio, f.hora_fin,
                NEW.dia, NEW.hora_inicio, NEW.hora_fin
          )
    ) THEN
        RAISE EXCEPTION 'dos franjas del mismo día no pueden solaparse';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_franja_sin_solape
    BEFORE INSERT OR UPDATE OF dia, hora_inicio, hora_fin ON franjas_horarias
    FOR EACH ROW
    EXECUTE FUNCTION ck_franja_sin_solape();

CREATE OR REPLACE FUNCTION ck_sesion_mismo_programa() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM horarios h
        JOIN bloques_contenido b ON b.id = NEW.bloque_id
        JOIN asignaturas a ON a.id = b.asignatura_id
        WHERE h.id = NEW.horario_id
          AND a.programa_id = h.programa_id
    ) THEN
        RAISE EXCEPTION 'el bloque no pertenece al programa del horario';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sesion_mismo_programa
    BEFORE INSERT OR UPDATE OF horario_id, bloque_id ON sesiones_horario
    FOR EACH ROW
    EXECUTE FUNCTION ck_sesion_mismo_programa();

CREATE OR REPLACE FUNCTION recalcular_equilibrio(horario UUID) RETURNS void AS $$
DECLARE
    total INTEGER;
    n_teo INTEGER;
    n_pra INTEGER;
    n_lab INTEGER;
    n_asig INTEGER;
    n_prog INTEGER;
    meta_teo NUMERIC(4,3);
    meta_pra NUMERIC(4,3);
    meta_lab NUMERIC(4,3);
    meta_cob NUMERIC(4,3);
    meta_cant INTEGER;
    ok BOOLEAN;
BEGIN
    SELECT proporcion_teorica, proporcion_practica, proporcion_laboratorio,
           cobertura_minima, cantidad_total_bloques
      INTO meta_teo, meta_pra, meta_lab, meta_cob, meta_cant
      FROM horarios
     WHERE id = horario;
    IF NOT FOUND THEN
        RETURN;
    END IF;

    SELECT COUNT(*),
           COUNT(*) FILTER (WHERE b.tipo_actividad = 'teórica'),
           COUNT(*) FILTER (WHERE b.tipo_actividad = 'práctica'),
           COUNT(*) FILTER (WHERE b.tipo_actividad = 'laboratorio'),
           COUNT(DISTINCT b.asignatura_id)
      INTO total, n_teo, n_pra, n_lab, n_asig
      FROM sesiones_horario s
      JOIN bloques_contenido b ON b.id = s.bloque_id
     WHERE s.horario_id = horario;

    SELECT COUNT(*) INTO n_prog
      FROM asignaturas
     WHERE programa_id = (SELECT programa_id FROM horarios WHERE id = horario);

    ok := total > 0
      AND n_prog > 0
      AND total = meta_cant
      AND ROUND(n_teo::numeric / total, 3) = meta_teo
      AND ROUND(n_pra::numeric / total, 3) = meta_pra
      AND ROUND(n_lab::numeric / total, 3) = meta_lab
      AND ROUND(n_asig::numeric / n_prog, 3) >= meta_cob;

    UPDATE horarios
       SET equilibrio_cumplido = ok
     WHERE id = horario
       AND equilibrio_cumplido IS DISTINCT FROM ok;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_sesion_recalcula_equilibrio() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM recalcular_equilibrio(OLD.horario_id);
    ELSE
        PERFORM recalcular_equilibrio(NEW.horario_id);
        IF TG_OP = 'UPDATE' AND OLD.horario_id IS DISTINCT FROM NEW.horario_id THEN
            PERFORM recalcular_equilibrio(OLD.horario_id);
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sesion_recalcula_equilibrio
    AFTER INSERT OR UPDATE OR DELETE ON sesiones_horario
    FOR EACH ROW
    EXECUTE FUNCTION trg_sesion_recalcula_equilibrio();

CREATE OR REPLACE FUNCTION trg_horario_recalcula_equilibrio() RETURNS trigger AS $$
BEGIN
    PERFORM recalcular_equilibrio(NEW.id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_horario_recalcula_equilibrio
    AFTER UPDATE OF proporcion_teorica, proporcion_practica, proporcion_laboratorio,
                    cobertura_minima, cantidad_total_bloques
    ON horarios
    FOR EACH ROW
    EXECUTE FUNCTION trg_horario_recalcula_equilibrio();

CREATE OR REPLACE FUNCTION ck_solicitud_asigna_destino() RETURNS trigger AS $$
BEGIN
    IF NEW.resultado = 'nuevo horario asignado' THEN
        INSERT INTO asignacion_estudiante_horario (estudiante_id, horario_id)
        VALUES (NEW.estudiante_id, NEW.horario_destino_id)
        ON CONFLICT DO NOTHING;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_solicitud_asigna_destino
    AFTER INSERT OR UPDATE OF resultado, horario_destino_id, estudiante_id
    ON solicitudes_cambio
    FOR EACH ROW
    EXECUTE FUNCTION ck_solicitud_asigna_destino();
