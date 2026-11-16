# Gestión para la generación automática de horarios docentes

**Bases de Datos II - Ingeniería de Software**  
**Curso: 2026 - 2027**

El presente documento describe una problemática para ser resuelta durante el semestre. Este documento es adjunto a las Orientaciones Metodológicas.

## Características generales

El proyecto tributa a la evaluación de las asignaturas Bases de Datos II e Ingeniería de Software, donde cada una controlará aspectos no necesariamente coincidentes.

El desarrollo de la solución será llevado a cabo por un equipo de estudiantes de hasta 5 integrantes, aunque la cantidad exacta de miembros se confirmará durante las primeras clases presenciales.

La nota de cada miembro del equipo será individual y no necesariamente la misma para ambas asignaturas, teniendo en cuenta:

- Labor de curso.
- Trabajo del equipo.
- Requisitos particulares de la asignatura de Bases de Datos (ver archivo adjunto).
- Requisitos particulares de la asignatura de Ingeniería de Software (al final del documento).

## Descripción del problema

Se desea confeccionar una aplicación web que dé como solución un sistema para gestionar la generación automática de horarios docentes dentro de una institución educativa. La solución tendrá que administrar los bloques de contenido a impartir, los programas académicos para los cuales se utilizan y la asignatura y tipo de actividad que abordan, los coordinadores académicos encargados de crear y validar los horarios, y los estudiantes que recibirán dichos horarios. Además, se requiere que los horarios se adapten a ciertos criterios preestablecidos, como el nivel de complejidad, el tipo de actividad y la distribución de las asignaturas cubiertas durante el semestre.

Cada coordinador académico al interactuar con el sistema podrá ingresar bloques de contenido al banco existente. Además, tiene la capacidad de, sobre aquellos bloques descritos por él, clasificarlos por asignatura y por tipo de actividad (teórica, práctica o laboratorio), otorgarle el nivel de complejidad (bajo, medio o alto) y generar horarios de forma automática a partir de los bloques seleccionados. También, cada coordinador tiene la opción de ver horarios de otros coordinadores que atienden el mismo programa académico.

El administrador del sistema se encargará de evitar la existencia de bloques duplicados, así como impedir la asignación doble de horarios a los estudiantes.

Los estudiantes podrán acceder a los horarios que le son asignados y el sistema debe garantizar el almacenamiento de cada asistencia registrada ante un horario impartido. Los reportes de ocupación pueden ser consultados por los coordinadores y los estudiantes, y los estudiantes pueden solicitar de forma virtual un cambio de horario, pudiendo pedir el apoyo de un coordinador académico adicional al que tienen asignado para que atienda dicha solicitud. Todo este proceso se registra en la base de datos como también el resultado del cambio manual.

No siempre aquellos coordinadores que agregan bloques son los que crean el horario, esta labor es desempeñada por un coordinador específico basándose en criterios como la proporción de bloques por tipo de actividad, la cobertura de las asignaturas y la cantidad total de bloques, cuya parametrización es almacenada junto al horario generado. Por su parte, el jefe de departamento es quien revisa y aprueba el horario generado, aunque también puede indicar la confección de otro bajo sus criterios.

Cada programa académico tendrá un identificador único, su nombre, el plan de estudios al que corresponde y la lista de asignaturas a cubrir a lo largo del semestre. De cada coordinador académico se almacenará su identificador único, nombre, especialidad, y los programas académicos para los cuales está autorizado a generar o validar horarios.

Cada estudiante tendrá un identificador único, su nombre, edad, grupo al que pertenece y los programas académicos en los que está matriculado. Estos pueden consultar todos sus horarios por programa académico recibido.

El sistema debe además conservar un histórico extenso de la ocupación de aulas y la asistencia registrada por bloque a lo largo de varios semestres, permitiendo análisis agregados de tendencias de uso por franja horaria, edificio y periodo. Dado que este histórico crece de forma sostenida semestre a semestre y se consulta principalmente de forma agregada (sumas, promedios y comparaciones por periodo) más que registro por registro, dicho histórico debe almacenarse y organizarse de forma independiente al resto del modelo relacional, priorizando la velocidad de estos análisis masivos sobre la de las operaciones individuales.

Dado que la disponibilidad de horarios y aulas es una información que estudiantes y coordinadores consultan de manera repetida durante los períodos de matrícula, el sistema debe mantener tiempos de respuesta mínimos ante esa demanda concentrada en cortos intervalos de tiempo.

Para asegurar la transparencia y el control de calidad, el sistema admitirá la generación de reportes detallados sobre la creación de horarios, los bloques más impartidos, la distribución de complejidades y el desempeño de los estudiantes según los diferentes niveles de complejidad.

## Funcionalidades

Tomando en cuenta la información almacenada en la base de datos, el sistema debe de proveer resultados (tablas y gráficos) para cada una de las demandas descritas a continuación:

1. Obtener el listado de horarios generados automáticamente para un programa académico específico, indicando el nombre del creador, la fecha de creación y los parámetros utilizados.
2. Obtener los bloques de contenido más impartidos en los horarios finales de un programa académico, clasificados por nivel de complejidad y asignatura.
3. Listar los horarios que fueron validados por un revisor determinado, indicando la fecha de validación y las observaciones hechas durante el proceso.
4. Generar un reporte sobre el desempeño de los estudiantes en un horario, clasificando los bloques por complejidad y comparando las tasas de asistencia.
5. Comparar los horarios generados para diferentes programas académicos, verificando la distribución de bloques por asignatura y nivel de complejidad y si los criterios de equilibrio fueron cumplidos.
6. Determinar, para cada programa académico, la correlación entre el nivel de complejidad de los bloques y el rendimiento promedio de los estudiantes. La consulta debe identificar los 10 bloques con la tasa de inasistencia más alta, el coordinador que los creó y el programa académico al que pertenecen. Además, debe comparar el desempeño de los estudiantes que solicitaron un cambio de horario con el promedio general de asistencia de sus respectivos grupos para esos mismos programas académicos.

Además, la posibilidad de exportar la información mostrada a ficheros con formato PDF tiene que ser una funcionalidad provista por el sistema para todo tipo de usuario. Así como poder ordenar cada columna de los resultados acorde a los intereses del usuario final.

## Requisitos particulares de la asignatura Ingeniería de Software

Además de la implementación de la aplicación web, las evaluaciones consistirán también de seminarios y preguntas escritas, los cuales se orientarán y se explicarán en su momento durante el semestre.

Con respecto al desarrollo de la solución, los requerimientos utilizados para calificar el trabajo serán:

1. Trabajar con un control de versiones (GitHub, TFS, etc.).
2. Realizar la planificación con alguna herramienta CASE (GitHub, Jira, Gantt, etc.).
3. Sistema multiplataforma.
4. Cumplir con todos los requerimientos funcionales planteados en el problema.
5. Tener buenas prácticas de programación, incluidos los comentarios en todo el código (docstring).
6. Implementar al menos dos patrones.
7. Implementar una arquitectura que permita a la aplicación ser desacoplada, extensible en funcionalidades y mantenible.
8. Implementar pruebas unitarias, tanto para el back-end como para el front-end.

No obstante, para considerar al equipo (estudiantes) aprobado en la asignatura es indispensable cumplir con los primeros seis puntos descritos.
