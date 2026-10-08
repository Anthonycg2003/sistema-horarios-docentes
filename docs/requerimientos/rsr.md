# Especificación de Requisitos de Software (RSR)

**Sistema de gestión para la generación automática de horarios docentes**

| Campo | Valor |
| --- | --- |
| Asignaturas | Bases de Datos II e Ingeniería de Software |
| Curso | 2026-2027 |
| Documento fuente | `docs/enunciado.md` |
| Versión | 1.0 |
| Estado | Borrador derivado del enunciado |

## 1. Introducción

### 1.1 Propósito

Este documento especifica los requisitos del sistema que gestiona la generación automática de horarios docentes en una institución educativa. Sirve como base común para el diseño, la implementación, las pruebas y la evaluación del proyecto.

### 1.2 Alcance

El producto es una aplicación web que administra:

- bloques de contenido y su clasificación;
- programas académicos, planes de estudio y asignaturas;
- coordinadores académicos, jefes de departamento, estudiantes y el administrador;
- la generación automática de horarios a partir de criterios parametrizados;
- la revisión, las observaciones y la aprobación de horarios;
- la asignación de horarios a estudiantes, la asistencia y las solicitudes de cambio;
- la ocupación de aulas y un histórico analítico de varios semestres;
- reportes en tablas y gráficos, con ordenamiento de columnas y exportación a PDF.

Queda fuera del alcance de este RSR la nota individual de cada integrante, los seminarios y las preguntas escritas de la asignatura. Esos aspectos se mencionan solo cuando imponen una restricción sobre el producto o el proceso de desarrollo.

### 1.3 Definiciones

| Término | Definición |
| --- | --- |
| Bloque de contenido | Unidad docente que se imparte dentro de un horario. Pertenece al banco de bloques, tiene asignatura, tipo de actividad y nivel de complejidad. |
| Banco de bloques | Conjunto de bloques registrados en el sistema y disponibles para armar horarios. |
| Tipo de actividad | Clasificación del bloque: teórica, práctica o laboratorio. |
| Nivel de complejidad | Clasificación del bloque: bajo, medio o alto. |
| Programa académico | Oferta formativa con identificador único, nombre, plan de estudios y asignaturas que deben cubrirse en el semestre. |
| Horario | Conjunto ordenado de bloques seleccionados para un programa, generado de forma automática junto con los parámetros usados. |
| Horario final | Horario aprobado por el jefe de departamento. |
| Criterios de equilibrio | Parámetros del horario: proporción de bloques por tipo de actividad, cobertura de asignaturas y cantidad total de bloques. |
| Coordinador creador de bloques | Coordinador que ingresa y clasifica bloques. Puede no ser quien genera el horario. |
| Coordinador generador | Coordinador autorizado que crea el horario automático a partir de bloques seleccionados. |
| Jefe de departamento | Revisor que aprueba un horario o solicita que se confeccione otro bajo sus criterios. |
| Asignación doble | Sesiones que se solapan en el tiempo para el mismo estudiante. Un segundo horario del mismo programa y periodo no es asignación doble. |
| Histórico analítico | Registro acumulado de ocupación de aulas y asistencia por bloque, separado del modelo operacional y orientado a consultas agregadas. |
| Tasa de inasistencia | Proporción de ausencias registradas respecto de las asistencias esperadas de un bloque. |

### 1.4 Referencias

- `docs/enunciado.md` — Gestión para la generación automática de horarios docentes. Bases de Datos II e Ingeniería de Software, curso 2026-2027.

### 1.5 Organización del documento

La sección 2 describe el contexto, los usuarios y las restricciones generales. La sección 3 detalla requisitos funcionales, de datos, de interfaz, de rendimiento y de calidad. La sección 4 recoge las restricciones de la asignatura de Ingeniería de Software. La sección 5 lista supuestos que el enunciado no cierra y que el equipo debe confirmar.

## 2. Descripción general

### 2.1 Perspectiva del producto

Aplicación web multiusuario. Los datos operacionales (programas, personas, bloques, horarios, solicitudes y asistencias del periodo en curso) se gestionan en un modelo relacional. El histórico de ocupación de aulas y de asistencia por bloque, acumulado durante varios semestres, se almacena y organiza de forma independiente para favorecer sumas, promedios y comparaciones por periodo.

La consulta repetida de disponibilidad de horarios y aulas, sobre todo en matrícula, debe responder con tiempos mínimos.

### 2.2 Actores

| Actor | Responsabilidad en el sistema |
| --- | --- |
| Administrador | Impide bloques duplicados e impide la asignación doble de horarios a estudiantes. |
| Coordinador académico | Ingresa bloques propios, los clasifica, consulta horarios de coordinadores del mismo programa, consulta reportes de ocupación, valida un horario si está autorizado y puede atender una solicitud de cambio aunque no sea el coordinador asignado al estudiante. |
| Coordinador generador | Genera horarios automáticos a partir de bloques seleccionados. Es un coordinador autorizado para el programa; no tiene que ser quien cargó los bloques. |
| Jefe de departamento | Revisa el horario generado, lo aprueba o indica que se confeccione otro según sus criterios. Registra fecha de validación y observaciones. |
| Estudiante | Consulta los horarios que le fueron asignados, por programa académico. Consulta reportes de ocupación. Solicita de forma virtual un cambio de horario y puede pedir el apoyo de un coordinador adicional. |

Un mismo coordinador puede cumplir las funciones de carga de bloques y de generación si está autorizado para ese programa.

### 2.3 Funciones principales

1. Administrar el banco de bloques y evitar duplicados.
2. Administrar programas académicos, asignaturas y la autorización de coordinadores.
3. Generar horarios de forma automática y guardar los parámetros usados.
4. Revisar, observar y aprobar horarios, o pedir una nueva confección.
5. Asignar horarios a estudiantes sin asignación doble.
6. Registrar la asistencia de cada sesión impartida.
7. Tramitar solicitudes de cambio de horario, incluido el apoyo de otro coordinador, y guardar el resultado del cambio manual.
8. Consultar ocupación y disponibilidad de horarios y aulas.
9. Conservar el histórico analítico de varios semestres.
10. Producir los seis reportes del enunciado, ordenar sus columnas y exportarlos a PDF.

### 2.4 Características de los usuarios

Los usuarios acceden mediante la aplicación web. El coordinador y el jefe de departamento trabajan con la confección y el control de calidad de los horarios. El estudiante consulta y solicita cambios. El administrador vela por la integridad de bloques y asignaciones. No se asume conocimiento técnico del modelo de datos.

### 2.5 Restricciones generales

- La solución es una aplicación web y debe poder usarse en más de una plataforma.
- El histórico analítico no forma parte del mismo esquema operacional: prioriza análisis masivos frente a operaciones registro a registro.
- Cada programa, coordinador y estudiante tiene un identificador único.
- La parametrización de un horario se almacena junto con el horario generado.
- La solicitud de cambio, su trámite y el resultado del cambio manual quedan registrados.
- Toda la información mostrada en resultados puede exportarse a PDF, para cualquier tipo de usuario.
- Cada columna de los resultados puede ordenarse según el interés del usuario.

### 2.6 Supuestos y dependencias

Los supuestos abiertos están en la sección 5. El sistema depende de que la institución defina periodos académicos, aulas, edificios y franjas horarias, porque el enunciado exige analizar ocupación por franja, edificio y periodo aunque no detalla la captura de esa infraestructura.

## 3. Requisitos específicos

### 3.1 Requisitos de datos

**RD-01. Programa académico.** El sistema almacena identificador único, nombre, plan de estudios y la lista de asignaturas que deben cubrirse durante el semestre.

**RD-02. Coordinador académico.** El sistema almacena identificador único, nombre, especialidad y los programas académicos para los cuales está autorizado a generar o validar horarios.

**RD-03. Estudiante.** El sistema almacena identificador único, nombre, edad, grupo y los programas académicos en los que está matriculado.

**RD-04. Bloque de contenido.** El sistema almacena el bloque en el banco, el coordinador que lo describió, la asignatura, el tipo de actividad (teórica, práctica o laboratorio) y el nivel de complejidad (bajo, medio o alto).

**RD-05. Horario generado.** El sistema almacena el programa, el coordinador generador, la fecha de creación, los bloques incluidos y los parámetros de generación: proporción de bloques por tipo de actividad, cobertura de asignaturas y cantidad total de bloques.

**RD-06. Validación.** El sistema almacena el revisor, la fecha, las observaciones y la decisión: validado u observado. El revisor es un usuario coordinador con permiso de validar ese programa. Un horario puede acumular más de un acto.

**RD-07. Asignación.** El sistema almacena qué horario le corresponde a cada estudiante y el programa académico asociado.

**RD-08. Asistencia.** El sistema almacena cada asistencia registrada ante un horario impartido, de modo que pueda calcularse la tasa de asistencia y la de inasistencia por bloque.

**RD-09. Solicitud de cambio.** El sistema almacena la solicitud virtual del estudiante, el coordinador de apoyo cuando se pide, el proceso del trámite y el resultado del cambio manual.

**RD-10. Infraestructura de impartición.** El sistema conserva aula, edificio, franja horaria y periodo de cada sesión, porque los análisis de ocupación se hacen por franja horaria, edificio y periodo.

**RD-11. Separación del histórico.** La ocupación de aulas y la asistencia por bloque, acumuladas a lo largo de varios semestres, se almacenan y organizan fuera del modelo relacional operacional. Esa organización favorece sumas, promedios y comparaciones por periodo por encima del acceso registro a registro.

**RD-12. Aprobación.** El sistema almacena el jefe revisor, la fecha, las observaciones y la decisión: aprobado o nueva confección. Si la decisión es nueva confección, la aprobación apunta al horario sucesor y los criterios de esa generación quedan en el horario nuevo. Un horario puede acumular más de un acto. El horario final es el aprobado.

### 3.2 Reglas de negocio

**RN-01.** Solo el coordinador que describió un bloque puede clasificarlo por asignatura, tipo de actividad y complejidad.

**RN-02.** El administrador impide que existan bloques duplicados en el banco.

**RN-03.** Un coordinador solo genera o valida horarios de los programas para los que está autorizado.

**RN-04.** Un coordinador puede consultar horarios de otros coordinadores que atienden el mismo programa académico.

**RN-05.** El coordinador que agrega bloques y el que genera el horario pueden ser personas distintas.

**RN-06.** La generación automática usa los bloques seleccionados y los criterios de proporción por tipo de actividad, cobertura de asignaturas y cantidad total de bloques.

**RN-07.** Esos criterios quedan guardados junto al horario.

**RN-08.** El jefe de departamento revisa el horario generado. Puede aprobarlo o indicar la confección de otro bajo sus criterios.

**RN-09.** El administrador impide la asignación doble de horarios a un estudiante.

**RN-10.** El estudiante consulta todos sus horarios recibidos, organizados por programa académico.

**RN-11.** Coordinadores y estudiantes consultan los reportes de ocupación.

**RN-12.** El estudiante puede solicitar un cambio de horario de forma virtual y pedir el apoyo de un coordinador académico adicional al que tiene asignado.

**RN-13.** El proceso de la solicitud y el resultado del cambio manual quedan registrados.

**RN-14.** La asistencia de cada sesión impartida se conserva.

**RN-15.** Los reportes de bloques más impartidos y las comparaciones de equilibrio se calculan sobre horarios finales, es decir, aprobados.

### 3.3 Requisitos funcionales

#### Gestión de bloques y programas

**RF-01.** El coordinador académico puede ingresar un bloque de contenido al banco.

**RF-02.** El coordinador puede clasificar los bloques que él describió, asignándoles asignatura, tipo de actividad y nivel de complejidad.

**RF-03.** El administrador puede detectar e impedir el alta o la permanencia de un bloque duplicado.

**RF-04.** El sistema mantiene los programas académicos con su plan de estudios y las asignaturas a cubrir en el semestre.

**RF-05.** El sistema mantiene la autorización de cada coordinador sobre los programas en los que puede generar o validar horarios.

#### Generación, revisión y asignación

**RF-06.** El coordinador generador, autorizado para el programa, puede seleccionar bloques y generar un horario de forma automática.

**RF-07.** Al generar el horario, el sistema aplica y almacena la proporción de bloques por tipo de actividad, la cobertura de asignaturas y la cantidad total de bloques.

**RF-08.** El sistema registra el nombre del creador y la fecha de creación del horario.

**RF-09.** El coordinador puede ver los horarios de otros coordinadores del mismo programa académico.

**RF-10.** Un coordinador autorizado a validar el programa puede registrar observaciones, la fecha y la decisión: validado u observado.

**RF-11.** El jefe de departamento puede aprobar el horario o indicar la confección de otro bajo los criterios que él defina. Esos criterios quedan en el horario nuevo. La fecha, las observaciones y la decisión quedan en la aprobación.

**RF-12.** El sistema asigna el horario aprobado a los estudiantes matriculados en el programa.

**RF-13.** El administrador, mediante las reglas del sistema, impide que un estudiante reciba una asignación doble.

#### Consulta del estudiante, asistencia y cambios

**RF-14.** El estudiante puede acceder a los horarios que le fueron asignados.

**RF-15.** El estudiante puede consultar todos sus horarios agrupados por programa académico.

**RF-16.** El sistema registra cada asistencia correspondiente a una sesión de un horario impartido.

**RF-17.** El estudiante puede solicitar de forma virtual un cambio de horario.

**RF-18.** El estudiante puede pedir que un coordinador académico adicional al asignado atienda esa solicitud.

**RF-19.** El coordinador de apoyo puede atender la solicitud de cambio.

**RF-20.** El sistema registra el trámite y el resultado del cambio manual de horario.

#### Ocupación, disponibilidad e histórico

**RF-21.** Coordinadores y estudiantes pueden consultar reportes de ocupación.

**RF-22.** Estudiantes y coordinadores pueden consultar la disponibilidad de horarios y de aulas, con prioridad de respuesta en los periodos de matrícula.

**RF-23.** El sistema conserva el histórico de ocupación de aulas y de asistencia por bloque durante varios semestres.

**RF-24.** El sistema permite análisis agregados de tendencias de uso por franja horaria, edificio y periodo, mediante sumas, promedios y comparaciones.

#### Reportes exigidos por el enunciado

Los resultados se presentan en tablas y gráficos cuando la demanda lo requiere.

**RF-25.** Obtener el listado de horarios generados automáticamente para un programa académico, con el nombre del creador, la fecha de creación y los parámetros utilizados.

**RF-26.** Obtener los bloques de contenido más impartidos en los horarios finales de un programa académico, clasificados por nivel de complejidad y asignatura.

**RF-27.** Listar los horarios validados por un revisor determinado, con la fecha de validación y las observaciones del proceso. El revisor es el coordinador que validó, no el jefe que aprobó.

**RF-28.** Generar un reporte del desempeño de los estudiantes en un horario, clasificando los bloques por complejidad y comparando las tasas de asistencia.

**RF-29.** Comparar los horarios generados para diferentes programas académicos: distribución de bloques por asignatura y nivel de complejidad, e indicar si se cumplieron los criterios de equilibrio.

**RF-30.** Para cada programa académico, determinar la correlación entre el nivel de complejidad de los bloques y el rendimiento promedio de los estudiantes.

**RF-31.** Dentro de RF-30, identificar los 10 bloques con la tasa de inasistencia más alta, el coordinador que los creó y el programa académico al que pertenecen.

**RF-32.** Dentro de RF-30, comparar el desempeño de los estudiantes que solicitaron un cambio de horario con el promedio general de asistencia de sus respectivos grupos, para esos mismos programas académicos.

#### Presentación y exportación

**RF-33.** Cualquier usuario autenticado puede exportar a PDF la información mostrada en los resultados.

**RF-34.** El usuario puede ordenar cada columna de los resultados.

### 3.4 Requisitos de interfaz

**RI-01.** La interfaz es web y distingue las tareas según el rol: administrador, coordinador, jefe de departamento y estudiante.

**RI-02.** Los reportes RF-25 a RF-32 muestran tablas. Donde el enunciado pide gráficos (distribución, comparación de tasas, correlación y tendencias), la misma vista incluye el gráfico correspondiente.

**RI-03.** Cada tabla de resultados permite ordenar por cualquiera de sus columnas.

**RI-04.** Cada vista de resultados ofrece la exportación a PDF de la información mostrada.

### 3.5 Requisitos de rendimiento

**RNF-01.** Las consultas repetidas de disponibilidad de horarios y aulas, concentradas en intervalos cortos durante la matrícula, mantienen tiempos de respuesta mínimos frente al resto de operaciones de escritura.

**RNF-02.** Las consultas agregadas del histórico (sumas, promedios y comparaciones por periodo, franja y edificio) se resuelven sobre el almacén analítico, sin recorrer el detalle operacional como camino principal.

### 3.6 Atributos de calidad

**RNF-03. Integridad.** No se aceptan bloques duplicados ni asignaciones dobles de horario a un estudiante.

**RNF-04. Trazabilidad.** Creación de horarios, parámetros, validaciones, observaciones, asistencias, solicitudes de cambio y resultados de cambios manuales quedan persistidos.

**RNF-05. Separación analítica.** El crecimiento sostenido del histórico no degrada el modelo operacional. El histórico se organiza de forma independiente.

**RNF-06. Control de acceso.** Un coordinador solo genera o valida en programas autorizados, y solo clasifica bloques descritos por él. El estudiante solo ve sus horarios y sus solicitudes.

**RNF-07. Portabilidad.** El sistema se utiliza desde navegador en distintas plataformas.

**RNF-08. Mantenibilidad y extensión.** La arquitectura mantiene separadas la presentación, la lógica de generación y validación, y el acceso a los almacenes operacional y analítico, de modo que se puedan añadir reportes o criterios sin reescribir el resto.

### 3.7 Matriz de trazabilidad con el enunciado

| Origen en el enunciado | Requisitos |
| --- | --- |
| Ingreso y clasificación de bloques por el coordinador | RF-01, RF-02, RD-04, RN-01 |
| Evitar bloques duplicados | RF-03, RN-02, RNF-03 |
| Impedir asignación doble | RF-13, RN-09, RNF-03 |
| Generación automática y parámetros almacenados | RF-06, RF-07, RF-08, RD-05, RN-05, RN-06, RN-07 |
| Ver horarios de otros coordinadores del mismo programa | RF-09, RN-03, RN-04 |
| Coordinador autorizado valida el horario | RF-10, RD-06 |
| Jefe de departamento aprueba o pide otro horario | RF-11, RD-12, RN-08 |
| Estudiante consulta horarios por programa | RF-14, RF-15, RN-10 |
| Asistencia de cada horario impartido | RF-16, RD-08, RN-14 |
| Reportes de ocupación para coordinadores y estudiantes | RF-21, RN-11 |
| Solicitud virtual de cambio y coordinador adicional | RF-17, RF-18, RF-19, RF-20, RD-09, RN-12, RN-13 |
| Datos de programa, coordinador y estudiante | RD-01, RD-02, RD-03 |
| Histórico independiente y análisis agregados | RD-11, RF-23, RF-24, RNF-02, RNF-05 |
| Disponibilidad con tiempos de respuesta mínimos | RF-22, RNF-01 |
| Reportes 1 a 6 | RF-25 a RF-32 |
| PDF para todo usuario y orden de columnas | RF-33, RF-34, RI-03, RI-04 |


## 4. Restricciones de Ingeniería de Software

El enunciado exige, para el desarrollo de la solución:

1. Trabajar con un control de versiones.
2. Planificar con alguna herramienta CASE.
3. Sistema multiplataforma.
4. Cumplir los requerimientos funcionales del problema.
5. Buenas prácticas de programación, incluidos comentarios en todo el código.
6. Implementar al menos dos patrones.
7. Arquitectura desacoplada, extensible y mantenible.
8. Pruebas unitarias de back-end y de front-end.

Los seis primeros son indispensables para aprobar la asignatura. No cambian el modelo de datos fijado en el informe de diseño.

## 5. Supuestos

El enunciado no fija estos puntos.

1. **Duplicado de bloque.** Se considera duplicado un bloque con la misma descripción de contenido, la misma asignatura y el mismo tipo de actividad ya presente en el banco. La complejidad no distingue dos bloques de contenido.
2. **Asignación doble.** Queda prohibido asignar al estudiante sesiones que se solapan en el tiempo, dentro de un horario o entre los suyos. Un segundo horario del mismo programa y semestre no es asignación doble.
3. **Rendimiento del estudiante.** El enunciado pide correlacionar complejidad y rendimiento, y a la vez habla de asistencia e inasistencia. Hasta que exista otra fuente de calificación, el rendimiento usado en RF-28, RF-30, RF-31 y RF-32 es la tasa de asistencia.
4. **Horario final.** Es el horario aprobado por el jefe de departamento. Los borradores y los horarios sustituidos no entran en RF-26.
5. **Cambio manual.** Lo ejecuta un coordinador autorizado o el jefe de departamento, y su resultado (aceptado, rechazado o nuevo horario asignado) queda en el registro de la solicitud.
6. **Aulas y edificios.** Existen como datos de la institución porque RF-24 los exige, aunque el enunciado no describe su formulario de alta.

## 6. Criterios de aceptación globales

El producto se considera acorde a este RSR cuando:

1. Un coordinador carga y clasifica solo sus bloques, y el sistema rechaza un duplicado.
2. Un coordinador autorizado genera un horario automático y el sistema guarda creador, fecha y parámetros.
3. Otro coordinador del mismo programa puede ver ese horario; uno de otro programa no puede generarlo ni validarlo.
4. Un coordinador autorizado valida con observaciones, y el jefe aprueba o pide otro horario. Los dos actos quedan fechados y un horario puede acumular más de uno de cada tipo.
5. Un estudiante ve solo sus horarios por programa, puede tener más de un horario del mismo programa si sus sesiones no se solapan, y puede pedir un cambio con un coordinador de apoyo.
6. Cada sesión impartida deja asistencia registrada.
7. Los reportes RF-25 a RF-32 devuelven los datos indicados, se ordenan por columna, se grafican cuando hay distribución o comparación, y se exportan a PDF con cualquier rol.
8. Las consultas agregadas de ocupación por franja, edificio y periodo salen del histórico independiente, y la disponibilidad de horarios y aulas sigue respondiendo bajo consulta repetida.
