# Sistema de Gestión y Generación Automática de Horarios Docentes

## Problema que resuelve

El proyecto propone una aplicación web para gestionar bloques de contenido, programas académicos, coordinadores, estudiantes y aulas, y generar horarios docentes automáticamente según criterios de disponibilidad, tipo de actividad, complejidad, cobertura de asignaturas y distribución de bloques. También permitirá gestionar validaciones, asistencia, solicitudes de cambio de horario y reportes.

## Integrantes

- Enrique González González — C311
- Ernesto Javier Govea Varona — C311
- Olivia Ortiz Arboláez — C311
- Anthony Cruz Garcia — C311
- Jose Manuel Porras Guerra — C311

## Alcance inicial

- Gestión de usuarios, roles y permisos.
- Gestión de programas académicos, asignaturas y bloques de contenido.
- Registro de aulas, horarios y disponibilidad.
- Generación automática de horarios con criterios configurables.
- Revisión, validación y aprobación de horarios.
- Consulta de horarios por coordinadores y estudiantes.
- Registro de asistencia y solicitudes de cambio de horario.
- Reportes con tablas, gráficos, ordenamiento y exportación a PDF.

## Stack tecnológico

Decisión del equipo registrada en la [issue #2](https://github.com/Anthonycg2003/sistema-horarios-docentes/issues/2). 

| Componente | Tecnología |
| --- | --- |
| Backend | Python + FastAPI |
| Validación de la API | Pydantic |
| Acceso a datos | SQLAlchemy |
| Base de datos | PostgreSQL |
| Caché | Redis |
| Frontend | React |
| Pruebas del backend | pytest |
| Pruebas del frontend | Vitest y Testing Library |

La API y la interfaz van separadas. Los endpoints y las reglas de negocio (generación, validación, duplicados y cambios de horario) se documentan con docstrings. Redis guarda la disponibilidad de aulas y horarios para responder rápido en el pico de matrícula.


## Estado actual

El repositorio, las reglas de colaboración y el stack están definidos. Falta el diseño detallado de la solución y el esqueleto de la API y de la interfaz.

## Reglas de colaboración

- La rama `main` debe mantenerse protegida.
- Cada tarea debe desarrollarse en una rama propia.
- Todo cambio debe entrar mediante un Pull Request.
- Al menos otro integrante debe revisar y aprobar el código.
- No se deben subir contraseñas ni archivos `.env`.
- Se debe incluir un archivo `.env.example` sin información sensible.