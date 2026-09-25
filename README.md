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

Decisión del equipo registrada en la [issue #2](https://github.com/Anthonycg2003/sistema-horarios-docentes/issues/2). Django quedó descartado.

| Componente | Tecnología |
| --- | --- |
| Backend | Python + FastAPI |
| Validación de la API | Pydantic |
| Acceso a datos | SQL a la vista; SQLAlchemy solo si hace falta para el CRUD |
| Base de datos | PostgreSQL |
| Caché | Redis |
| Frontend | React |
| Pruebas del backend | pytest |
| Pruebas del frontend | Vitest y Testing Library |

La API y la interfaz van separadas. Los endpoints y las reglas de negocio (generación, validación, duplicados y cambios de horario) se documentan con docstrings. Redis guarda la disponibilidad de aulas y horarios para responder rápido en el pico de matrícula.

### Ventajas

- PostgreSQL es relacional y transaccional: cubre integridad, joins, histórico y lo que pide Bases de Datos II.
- La separación entre API e interfaz encaja con Ingeniería de Software: el sistema queda extensible y mantenible.
- pytest y Vitest con Testing Library cubren las pruebas de backend y frontend que exige el proyecto.
- Los docstrings son el estilo nativo de Python, así que la documentación de endpoints y reglas queda en el mismo lenguaje del backend.
- Pydantic valida entradas y salidas de la API (roles, parámetros de generación y reportes).
- El algoritmo de horarios, que es el núcleo del sistema, se prototipa más rápido en Python: equilibrio por tipo de actividad, cobertura de asignaturas, complejidad y parametrización.
- FastAPI no oculta el SQL. Los reportes y el histórico (agregados por franja, edificio y periodo, y el top 10 de inasistencia) se escriben con consultas visibles.
- React encaja con la interfaz: listados, orden de columnas, gráficos, exportación a PDF, roles y solicitudes de cambio de horario.
- El navegador pide JSON a la API y Redis atiende las consultas repetidas de disponibilidad. El servidor no mantiene un circuito por usuario.

### Desventajas

- El equipo mantiene dos ecosistemas: Python en la API y JavaScript en la interfaz.
- FastAPI es asíncrono. La generación de horarios puede consumir mucha CPU y hay que ejecutarla aparte del ciclo de peticiones para no bloquear la API.
- Redis es un servicio más que operar, y hay que definir cuándo se invalida la caché de disponibilidad.
- Dejar el SQL a la vista da control para los reportes, pero exige más cuidado que un ORM que oculte las consultas.

### Riesgos

- El algoritmo de horarios puede crecer en complejidad antes de que la API y la interfaz estén estables.
- Si la caché de disponibilidad no se invalida al cambiar un horario, un aula o una asistencia, las consultas del pico de matrícula pueden devolver datos viejos.
- El equipo no parte con el mismo dominio de Python y de React; la revisión de pull requests tiene que cubrir ambos lados.
- Django no se vuelve a evaluar. La decisión ya está cerrada.

## Estado actual

El repositorio, las reglas de colaboración y el stack están definidos. Falta el diseño detallado de la solución y el esqueleto de la API y de la interfaz.

## Reglas de colaboración

- La rama `main` debe mantenerse protegida.
- Cada tarea debe desarrollarse en una rama propia.
- Todo cambio debe entrar mediante un Pull Request.
- Al menos otro integrante debe revisar y aprobar el código.
- No se deben subir contraseñas ni archivos `.env`.
- Se debe incluir un archivo `.env.example` sin información sensible.