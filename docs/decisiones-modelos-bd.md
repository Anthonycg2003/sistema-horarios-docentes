# Decisiones sobre los modelos de la base de datos

Decisiones tomadas al implementar la issue #15 (modelos SQLAlchemy y migración inicial). La fuente del diseño es el informe `docs/evaluaciones/documentos/informe-diseno-base-de-datos/` (secciones 4, 5 y 6). Este archivo recoge dónde se siguió el informe al pie de la letra, dónde se completó y dónde se desvió, con el motivo. Las marcadas con **[revisar]** conviene discutirlas en equipo.

## 1. Fuente de verdad

- La issue cita `docs/data-model.md`, que no existe. Se usó el informe de diseño (sección 4.5, descomposición en 3FN, 16 esquemas) como fuente.
- `docs/architecture.md` §6 y `docs/diagramas/db/oltp.sql` / `olap.sql` describen un diseño anterior (tabla `usuarios`, varios actos de aprobación por horario, asignaturas por programa, fecha en la asistencia). **No se siguieron.** Contradicen el informe corregido (issue #20). **[revisar]** Habría que actualizar `architecture.md` §6 y los `.sql` o marcarlos como obsoletos.

## 2. Nombres

- Tablas y columnas en inglés, `snake_case`, tablas en plural (`docs/conventions.md` §4). Las tablas asociativas usan los nombres que fija la convención: `coordinator_program`, `student_program`, `student_schedule_assignment`.
- Correspondencia con el informe:

| Informe | Tabla | Notas |
|---|---|---|
| Programa | `academic_programs` | `name`, `study_plan` |
| Asignatura | `subjects` | |
| Coordinador | `coordinators` | `specialty` |
| Autorización | `coordinator_program` | `can_generate`, `can_validate` |
| Estudiante | `students` | `group_name` (ver 3.4) |
| Matrícula | `student_program` | |
| Jefe | `department_heads` | |
| Bloque | `content_blocks` | `creator_id` = #CCrea |
| Semestre | `semesters` | |
| Horario | `schedules` | `creator_id` = #CGen, `validator_id` = #CVal, `head_id` = #J, `previous_schedule_id` = #HAnt |
| Aula | `classrooms` | |
| Franja | `time_slots` | |
| Sesión | `schedule_sessions` | `session_date` = Fecha |
| Asignación | `student_schedule_assignment` | |
| Asistencia | `attendances` | |
| Solicitud | `change_requests` | `origin_schedule_id`, `target_schedule_id`, `attending_coordinator_id`, `support_coordinator_id` |

- Los valores de dominio se guardan en español (`teórica`, `nueva confección`, `miércoles`…). Los miembros de los enums de Python están en inglés (`ActivityType.THEORETICAL`).
- Todas las restricciones tienen nombre determinista (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`) mediante una `naming_convention` en `app/db/base.py`, así las migraciones futuras pueden referenciarlas.

## 3. Desviaciones y añadidos respecto al informe

### 3.1 `student_schedule_assignment.ended_at` (añadido) **[revisar]**

El informe tiene dos reglas que chocan:

- RN-15: la asistencia tiene FK `(#E, #H) → Asignación`, y la asistencia no se borra (sección 5.3).
- RN-20: al aceptar un cambio, "el estudiante deja el horario de origen".

Si dejar el horario fuera borrar la fila de asignación, la FK lo impediría en cuanto el estudiante tuviera una asistencia registrada, o habría que borrar asistencias, lo que incumple el enunciado ("garantizar el almacenamiento de cada asistencia"). Decisión: la asignación no se borra. Se marca con `ended_at` (nulo = vigente) y se añade `assigned_at`. RN-13, RN-14 y las consultas de "mis horarios" deben considerar solo asignaciones con `ended_at IS NULL`. Esto no altera las dependencias funcionales: los dos atributos dependen de la llave (#E, #H).

Si el estudiante vuelve a un horario que ya dejó (A → B → A), la PK `(student_id, schedule_id)` impide insertar otra fila. Se reactiva la fila existente: `ended_at = NULL` y nuevo `assigned_at`. La asistencia ya registrada bajo ese par sigue válida, y el historial completo de movimientos queda en `change_requests`.

### 3.2 `classrooms.name` (añadido)

El informe define Aula(#Au, Edificio, Capacidad). Sin un nombre o código, el usuario no puede distinguir dos aulas del mismo edificio, y `dim_aula` del modelo analítico ya pedía "nombre, edificio". Se añade `name` con `UNIQUE (building, name)`. Es otra llave candidata, así que la tabla sigue en 3FN.

### 3.3 `semesters.name` (añadido)

Se añade un nombre único ("2026-2027 S1") para mostrarlo en la interfaz y como etiqueta del periodo en `dim_time`. Es otra llave candidata, así que la tabla sigue en 3FN.

### 3.4 `students.group_name`

`group` es palabra reservada en SQL. Se usa `group_name`.

### 3.5 Esquema `Llave(#C, #Sol, #B, #H)` no se crea

En el informe ese esquema solo se añade para que la descomposición cumpla la PLJ en la demostración teórica. No guarda información de negocio y no se materializa como tabla.

### 3.6 Fechas como `TIMESTAMPTZ`

`created_at`, `validated_at`, `reviewed_at`, `requested_at`, `resolved_at`, `assigned_at` y `ended_at` son `TIMESTAMPTZ` (convención §4). `created_at`, `requested_at` y `assigned_at` toman `now()` por defecto. `session_date` y las fechas del semestre son `DATE`, y las horas de la franja son `TIME`.

### 3.7 Parámetros de generación

`theory_ratio`, `practice_ratio`, `lab_ratio` y `subject_coverage` son `NUMERIC(4,3)`, con CHECK en [0, 1]. Además, `theory_ratio + practice_ratio + lab_ratio = 1` exacto. La aplicación debe normalizar (p. ej. 0.334 / 0.333 / 0.333). `block_count > 0`.

### 3.8 Observaciones sin validación o revisión

Además de los CHECK del informe ("#CVal y FValidacion nulos a la vez", "#J, FRevision y Decision nulos a la vez"), las observaciones (`validation_notes`, `review_notes`) solo pueden tener valor si existe la validación o la revisión correspondiente. Pueden ser nulas aunque exista la validación.

## 4. Restricciones implementadas en esta migración

Solo las declarativas: PK, FK, `UNIQUE`, `CHECK`, `NOT NULL` y los tipos `ENUM`.

| Regla | Implementación |
|---|---|
| Dominios (sección 5.1) | ENUM nativos + CHECK |
| RN-01 | `ck_coordinator_program_grants_capability` |
| RN-03 | `UNIQUE INDEX (subject_id, activity_type, md5(lower(btrim(description))))`: compara la descripción sin espacios en los extremos ni distinción de mayúsculas, y evita el límite de ~2,7 KB de las filas de un índice btree |
| RN-04 (parte UNIQUE) | `UNIQUE (weekday, start_time)`, `UNIQUE (weekday, end_time)`, `end_time > start_time` |
| RN-05 (parte UNIQUE) | `UNIQUE start_date`, `UNIQUE end_date`, `end_date > start_date` |
| RN-07 / RN-11 (fechas) | `validated_at >= created_at`, `reviewed_at >= created_at` |
| RN-09 | `UNIQUE (schedule_id, time_slot_id, session_date)` |
| RN-12 (parte UNIQUE) | `UNIQUE previous_schedule_id`, `previous_schedule_id <> id` |
| RN-15 | FK `(schedule_id, block_id) → schedule_sessions`, FK `(student_id, schedule_id) → student_schedule_assignment` |
| RN-17 | `ck_change_requests_status_consistent`, `resolved_at >= requested_at` |
| RN-18 (parte CHECK) | `target_schedule_id <> origin_schedule_id` |
| RN-19 | `support_coordinator_id <> attending_coordinator_id` |
| RN-23 | Esquema `analitic` sin FK hacia `public` |

Las FK no tienen `ON DELETE CASCADE`. El borrado queda restringido, como pide la sección 5.3 ("Asistencia y Sesión no se borran en cascada").

## 5. Pendiente para otras issues **[revisar]**

- **Disparadores**: RN-04 y RN-05 (no solapamiento), RN-06, RN-07 (autorización), RN-08, RN-10, RN-11 (horario final), RN-12, RN-13, RN-14, RN-16, RN-18 y RN-20. El informe los marca como disparadores, y la issue #15 solo pide FK/UNIQUE/CHECK/NOT NULL. Se proponen en una migración aparte. RN-04 y RN-05 podrían ser restricciones `EXCLUDE USING gist` en lugar de disparadores (RN-04 necesita la extensión `btree_gist`).
- **RNF-01**: la vista materializada de disponibilidad por semestre, aula y franja es diseño físico y va en otra migración.
- **Usuarios y roles** (RNF-03): el informe los deja fuera del modelo conceptual. La tabla de cuentas y su vínculo con coordinador, estudiante o jefe va con la issue de autenticación.
- **ETL** del histórico: no forma parte de esta issue.

## 6. Esquema analítico (`analitic`)

- Nombre del esquema: `analitic`, tal como lo pide el criterio de aceptación de la issue #15. `architecture.md` lo llama `analitica`. **[revisar]** Si se prefiere `analytics` o `analitica`, basta con cambiar `ANALYTICS_SCHEMA` en `app/models/analytics.py` y en la migración.
- Tablas: `dim_time`, `dim_classroom`, `dim_time_slot`, `dim_group`, `dim_block`, `fact_classroom_occupancy`, `fact_block_attendance` y `fact_change_request`, según la figura del informe (sección 6).
- Los tipos ENUM del histórico se crean dentro de `analitic` (`analitic.complexity_level`, etc.) para que el esquema no dependa de ningún objeto de `public` (RN-23).
- Los identificadores operacionales se guardan como columnas degeneradas `*_key` (`semester_key`, `block_key`, `student_key`, `program_key`…) **sin FK**. Así la carga puede ser idempotente (upsert por clave de origen) sin acoplar los esquemas.
- `dim_block` admite varias filas por bloque (`UNIQUE (block_key, activity_type, complexity, subject_name)`). Si un bloque cambia de clasificación, los hechos pasados conservan la complejidad que tenía (SCD tipo 2 simplificado). Incluye también `activity_type`, que el informe no lista, porque un bloque solo se identifica con descripción, asignatura y tipo (RN-03).
- Medidas: `occupied_minutes` y `session_count` en ocupación; `present_count`, `absent_count` y `attendance_rate` (`NUMERIC(5,4)` en [0, 1]) en asistencia, donde la tasa es derivada y dos CHECK la atan a los contadores (`present_count + absent_count > 0` y `attendance_rate = round(present_count / NULLIF(present_count + absent_count, 0), 4)`; el NULLIF evita una división por cero que ocultaría el primer CHECK); `request_count` en solicitudes. La demanda 6 del enunciado se responde con `dim_block`, `fact_block_attendance` y `fact_change_request`, agrupando por `program_key` y `group_id`.

## 7. Entorno

- La migración se probó contra PostgreSQL 18 local. Docker Compose usa la 16, y la migración no usa nada exclusivo de la 18.
- `DATABASE_URL` en el `.env.example` raíz usa `postgresql://`, que SQLAlchemy resuelve con `psycopg2`, que no está instalado. El backend usa `psycopg` (v3), así que dentro de Docker debería ser `postgresql+psycopg://`. **[revisar]** No se cambió en esta rama porque es configuración de la issue de Docker.
