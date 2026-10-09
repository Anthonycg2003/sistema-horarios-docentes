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

## Estado actual

Inicio del proyecto. El repositorio y las reglas de colaboración ya están configurados. El diseño de datos está en `docs/informes/informe-diseno-base-de-datos.md`. El stack de la aplicación sigue el documento de arquitectura.

## Reglas de colaboración

El repositorio usa GitFlow. La rama por defecto es `develop`.

- `main` es la rama estable. Solo recibe `release/*` y `hotfix/*`. No recibe features directas.
- `develop` es la rama de integración. Recibe `feature/*`, `fix/*` y `docs/*`.
- `feature/*`, `fix/*` y `docs/*` se abren desde `develop` y vuelven a `develop` por pull request.
- `release/vX.Y.Z` se abre desde `develop` al cerrar un hito. Solo admite correcciones. Se mergea a `main`, se etiqueta el merge (`v0.1.0`, `v0.2.0`, …) y se mergea de vuelta a `develop`.
- `hotfix/*` se abre desde `main` y vuelve a `main` y a `develop`.
- Todo cambio entra mediante un pull request. Al menos otro integrante debe revisarlo y aprobarlo.
- `main` y `develop` están protegidas: sin push directo para quien no sea admin y sin force-push.
- No se deben subir contraseñas ni archivos `.env`.
- Se debe incluir un archivo `.env.example` sin información sensible.