# Hitos del proyecto

Plan de entregas alineado con el [enunciado](./enunciado.md) y GitFlow. Al cerrar un hito, se abre la rama `release/*`, solo correcciones si hace falta, merge a `main` con el tag, y merge de vuelta a `develop`.

---

## Hito 0 — Fundación

**Tag previsto:** `v0.1.0`

### Alcance

Documentación de análisis y diseño, repositorio y convenciones, esqueleto backend (FastAPI en capas, health, settings, BD, Redis, excepciones, Alembic), esqueleto frontend (Vite + React, componentes base, cliente HTTP), Docker Compose con los cuatro servicios y migración inicial con todos los modelos del dominio (sin pantallas de negocio todavía).

---



## Hito 1 — Actores y catálogo

**Tag previsto:** `v0.2.0`

### Alcance

Autenticación y layout de la app; CRUD de programas, asignaturas, coordinadores, estudiantes, aulas y franjas; administración de usuarios; refactor transversal de excepciones; asignación N:M de coordinadores y estudiantes a programas. Cada feature con API, servicio, repositorio, pantalla, tests de integración y tests unitarios del servicio (y del frontend donde aplique).

---



## Hito 2 — Bloques, generación y validación

**Tag previsto:** `v0.3.0`

### Alcance

Banco de bloques con autoría del coordinador y rechazo del duplicado (misma descripción, asignatura y tipo de actividad); generación que guarda proporciones, cobertura y cantidad de bloques; historial de validación del coordinador autorizado (`validado` u `observado`) y de aprobación del jefe (`aprobado` o nueva confección).

---



## Hito 3 — Asignación, asistencia y cambios

**Tag previsto:** `v0.4.0`

### Alcance

Asignar horarios aprobados a estudiantes. Puede haber más de un horario del mismo programa; la asignación doble es el solape de sesiones. Asistencia por sesión, estudiante y fecha. Solicitud de cambio con horario de origen, apoyo opcional y destino si el resultado es un horario nuevo.

---



## Hito 4 — Reportes, exportación, caché e histórico

**Tag previsto:** `v0.5.0`

### Alcance

Seis reportes del enunciado (hub y páginas), exportación PDF, ordenación en tablas, lectura de matrícula en `proyeccion_disponibilidad` y esquema estrella `analitica` (ocupación y asistencia) con ETL.

---



## Hito 5 — Cierre de ingeniería de software

**Tag previsto:** `v1.0.0`

### Alcance

Verificación de linters y suites, tests de componentes frontend pendientes de features anteriores y documentación final de entrega. El cierre entra a `main` solo por `release/v1.0.0`, con el tag, y se mergea de vuelta a `develop`.

---



## Resumen


| Hito | Tag      | Entregables principales                                                                                                              |
| ---- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 0    | `v0.1.0` | Documentación, scaffold backend/frontend, Docker, esquema BD, unit tests de seguridad/fundación                                      |
| 1    | `v0.2.0` | Auth, catálogos CRUD, usuarios, N:M programas; integración + unit tests por servicio                                                 |
| 2    | `v0.3.0` | Bloques, generación CP-SAT, validación del coordinador y aprobación del jefe; UI detalle/sidebar; unit tests de servicios de horario |
| 3    | `v0.4.0` | Asignación N:N, solape de sesiones, asistencia, solicitudes de cambio                                                                |
| 4    | `v0.5.0` | Seis reportes, PDF, ordenación, proyección de matrícula, estrella `analitica`                                                        |
| 5    | `v1.0.0` | Tests UI compartidos, linters/suites en verde, documentación de entrega                                                              |


