# Informe: Diseño de la base de datos

**Asignaturas:** Bases de Datos II e Ingeniería de Software  
**Curso:** 2026-2027

**Equipo:** MERXIRVE

| Integrante | Grupo |
| --- | --- |
| Enrique González González | C311 |
| Ernesto Javier Govea Varona | C311 |
| Olivia Ortiz Arboláez | C311 |
| Anthony Cruz Garcia | C311 |
| Jose Manuel Porras Guerra | C311 |

**Título del proyecto:** Gestión para la generación automática de horarios docentes.

---

## 3. Análisis y reformulación de los requerimientos

El enunciado mezcla actores, datos, reglas y seis consultas. Esta sección los separa en requerimientos funcionales y requerimientos informacionales, y completa lo que el texto deja implícito pero el sistema no puede omitir.

### 3.1 Lectura del problema

La institución arma horarios a partir de un banco de bloques. Cada bloque pertenece a una asignatura, tiene un tipo de actividad (teórica, práctica o laboratorio) y una complejidad (bajo, medio o alto). Un coordinador carga y clasifica bloques; otro, autorizado para el programa, puede generar el horario. El jefe de departamento lo aprueba o pide otra confección. El administrador impide bloques duplicados y la asignación doble. El estudiante consulta sus horarios, registra la asistencia y puede pedir un cambio, incluso con un coordinador de apoyo. Coordinadores y estudiantes consultan ocupación. El histórico de varios semestres se lee por sumas, promedios y comparaciones, fuera del modelo operacional. Durante la matrícula, la disponibilidad de horarios y aulas se consulta muchas veces en poco tiempo.

### 3.2 Actores y lo que cada uno persiste

| Actor | Qué hace | Qué debe quedar registrado |
| --- | --- | --- |
| Administrador | Rechaza duplicados y asignaciones dobles | Identidad y rol; el rechazo es una regla del sistema, no un expediente aparte |
| Coordinador académico | Carga y clasifica sus bloques; consulta horarios del mismo programa y la ocupación; si está autorizado, valida un horario; puede atender un cambio | Autoría del bloque, especialidad, programas autorizados, el acto de validación y, si aplica, el trámite de apoyo |
| Coordinador generador | Selecciona bloques y genera el horario automático | Creador, fecha, programa, semestre, bloques ubicados en sesión y parámetros usados |
| Jefe de departamento | Aprueba o pide otra confección | Revisor, fecha, decisión y observaciones de la aprobación |
| Estudiante | Consulta sus horarios, su asistencia y pide cambios | Identidad, edad, grupo, matrícula, asignación, asistencia y solicitud con su resultado |

Un mismo coordinador puede cargar bloques, generar horarios y validarlos si está autorizado. Validar y aprobar no son el mismo acto: el coordinador valida; el jefe de departamento aprueba. El jefe no es quien carga el banco.

### 3.3 Requerimientos informacionales

Son los datos que el sistema debe conservar para poder operar y responder las consultas. Se reformulan así:

**RI-01. Programa académico.** Identificador, código único, nombre, plan de estudios y la lista de asignaturas que debe cubrir en el semestre. La lista es una relación con la asignatura, no un texto.

**RI-02. Asignatura.** Identificador, nombre y el programa al que pertenece. Una asignatura pertenece a un solo programa: el enunciado pide la lista de asignaturas a cubrir de ese programa y no describe reutilización entre programas. No pide código ni créditos, y el modelo no los inventa.

**RI-03. Coordinador.** Identificador, nombre, especialidad y los programas en los que puede generar o validar. Esas dos capacidades son independientes: generar un horario y revisar uno no son el mismo permiso.

**RI-04. Estudiante.** Identificador, nombre, edad, un grupo y los programas en los que está matriculado. El grupo es uno; la matrícula puede ser varias.

**RI-05. Grupo del estudiante.** No es una entidad y no pertenece a un programa. Es un atributo del estudiante, el que el enunciado pide junto a su identidad. Hace falta para comparar, en el reporte de cambios, la asistencia de quien pidió un cambio con el promedio de quienes comparten ese mismo grupo. La matrícula en varios programas no parte el grupo en uno por programa.

**RI-06. Bloque de contenido.** Título, descripción, asignatura, tipo de actividad, complejidad, duración y coordinador que lo describió. La clasificación la hace ese coordinador. Dos bloques con la misma descripción de contenido, la misma asignatura y el mismo tipo de actividad son el mismo bloque: la complejidad no los distingue.

**RI-07. Horario.** Programa, semestre, creador, fecha de creación, estado, indicador de generación automática y el resultado de si se cumplieron los criterios de equilibrio. El estado distingue al menos borrador, en revisión, aprobado y sustituido. Solo el aprobado es horario final.

**RI-08. Parámetros de generación.** Se guardan junto al horario, no en un catálogo suelto: proporción teórica, práctica y de laboratorio, cobertura mínima de asignaturas, cantidad total de bloques y la estrategia usada. Si el jefe pide otra confección, los criterios de esa nueva generación quedan en el horario nuevo; el motivo queda en la aprobación.

**RI-09. Franja y sesión.** La franja es catálogo: día, hora de inicio y hora de fin. Existe aparte de cualquier horario, porque el enunciado pide analizar y consultar disponibilidad por franja. La sesión es la ubicación de un bloque dentro de un horario: una franja de ese catálogo y un aula. El aula es obligatoria. La sesión no guarda la fecha de calendario: el mismo hueco semanal se imparte muchas veces durante el semestre, y cada impartición queda en la asistencia. Sin sesión no hay asistencia ni ocupación real.

**RI-10. Aula.** Identificador, nombre, edificio y capacidad. El edificio sale del aula y la franja del catálogo. El enunciado no pide un tipo de aula, y el modelo no lo agrega.

**RI-11. Asignación.** Qué horario corresponde a cada estudiante. El enunciado habla de sus horarios en plural, también dentro de un programa, así que un estudiante puede tener más de un horario del mismo programa y semestre. La asignación doble es otra cosa: sesiones que se solapan en el tiempo.

**RI-12. Validación.** Coordinador autorizado a validar ese programa, horario, fecha, decisión (validado u observado) y observaciones. Un horario puede acumular más de un acto de validación. Esta es la demanda de horarios validados por un revisor.

**RI-13. Asistencia.** Por cada sesión del horario, cada fecha en que esa sesión se imparte y cada estudiante esperado: presente o ausente. La fecha es la de esa clase, no un atributo de la sesión. De ahí salen la tasa de asistencia y la de inasistencia. Hasta que exista otra calificación, el «rendimiento» de los reportes es esa tasa.

**RI-14. Solicitud de cambio.** Estudiante, horario de origen, horario de destino si el cambio se concreta, coordinador asignado, coordinador de apoyo si se pidió, motivo, estado, fecha de solicitud, fecha de resolución y resultado (aceptado, rechazado o nuevo horario asignado).

**RI-15. Histórico analítico.** Ocupación de aulas y asistencia por bloque, acumuladas durante varios semestres, en un almacén distinto del operacional. La ocupación se consulta por periodo, edificio y franja. La asistencia se consulta por periodo, bloque, estudiante y grupo, para poder promediar el grupo sin volver a la asistencia operacional.

**RI-16. Usuario de acceso.** Toda persona que entra al sistema tiene identificador único, nombre, rol y credencial. El rol especializa al usuario en administrador, coordinador académico, estudiante o jefe de departamento.

**RI-17. Aprobación.** Jefe de departamento, horario, fecha, decisión (aprobado o nueva confección) y observaciones. El horario final es el que el jefe aprueba. Si pide otra confección, los criterios pasan al horario nuevo y el motivo queda en esta aprobación. Un horario puede acumular más de un acto de aprobación.

### 3.4 Requerimientos funcionales reformulados

Se agrupan por el proceso, no por el orden en que aparecen en el enunciado.

**Banco y oferta**

1. Un coordinador ingresa un bloque al banco.
2. Solo ese coordinador clasifica el bloque por asignatura, tipo de actividad y complejidad.
3. El sistema rechaza un bloque duplicado según RI-06.
4. Se mantienen programas, asignaturas a cubrir y la autorización de cada coordinador (generar, validar, o ambas).

**Generación y calidad**

5. Un coordinador autorizado para el programa selecciona bloques y genera un horario automático.
6. La generación aplica y guarda los parámetros de RI-08, el creador y la fecha.
7. Quien cargó los bloques y quien generó el horario pueden ser personas distintas.
8. Un coordinador ve los horarios de otros coordinadores del mismo programa, y no genera ni valida en un programa para el que no está autorizado.
9. Un coordinador con autorización para validar ese programa registra fecha, observaciones y decisión (validado u observado). El jefe, en un acto distinto, registra observaciones y fecha, aprueba el horario o pide otro bajo criterios que pasan a la nueva generación.
10. Los reportes de bloques más impartidos y de equilibrio usan solo horarios finales.

**Asignación, asistencia y cambio**

11. El horario aprobado se asigna a los estudiantes matriculados en el programa.
12. El sistema impide la asignación doble definida en RI-11.
13. El estudiante consulta solo sus horarios, agrupados por programa.
14. Cada impartición de una sesión deja una asistencia por estudiante en esa fecha.
15. El estudiante solicita un cambio de forma virtual y puede pedir un coordinador de apoyo.
16. El trámite y el resultado del cambio manual quedan registrados.

**Consulta intensiva e histórico**

17. Coordinadores y estudiantes consultan ocupación y disponibilidad de horarios y aulas.
18. Esa disponibilidad, repetida en la matrícula, no se resuelve recorriendo el detalle de escritura ni mezclándola con el histórico de varios semestres.
19. El histórico de varios semestres permite sumas, promedios y comparaciones por franja, edificio y periodo, sin usar el OLTP como camino principal.

**Demandas de información del enunciado**

20. Listar los horarios generados de un programa, con creador, fecha y parámetros.
21. Listar los bloques más impartidos en los horarios finales de un programa, por complejidad y asignatura.
22. Listar los horarios validados por un revisor, con fecha y observaciones. El revisor es el coordinador que validó, no el jefe que aprobó.
23. Reportar el desempeño en un horario: bloques por complejidad y comparación de tasas de asistencia.
24. Comparar horarios de distintos programas: distribución por asignatura y complejidad, y si se cumplió el equilibrio.
25. Por programa, correlacionar complejidad y rendimiento medio; devolver los 10 bloques con mayor inasistencia, su creador y su programa; comparar la asistencia de quienes pidieron cambio con el promedio de su grupo en esos programas.
26. Cualquier usuario autenticado exporta a PDF el resultado que está viendo.
27. Puede ordenar cada columna de ese resultado.

### 3.5 Lo que esta reformulación añade al enunciado

| Hueco del enunciado | Decisión de diseño |
| --- | --- |
| No define qué es un bloque duplicado | Misma descripción, asignatura y tipo de actividad. La complejidad no crea otro bloque |
| No dice si una asignatura se comparte entre programas | No se comparte. Cada asignatura pertenece a un programa |
| No define la asignación doble | Sesiones que se solapan en el tiempo. Un segundo horario del mismo programa no es asignación doble: el enunciado habla de los horarios del estudiante en plural |
| Pide «rendimiento» y a la vez habla de asistencia | El rendimiento de los reportes es la tasa de asistencia |
| No dice qué es un horario final | El aprobado por el jefe de departamento |
| Exige análisis por aula, edificio, franja y periodo sin modelarlos | Aula, edificio y franja son catálogo operacional; la sesión los usa. El agregado vive en el analítico |
| Exige respuesta rápida en matrícula | La disponibilidad se sirve aparte del recorrido transaccional (caché), sin mezclarla con el histórico |
| El histórico crece y se lee en agregado | Esquema estrella en un esquema distinto del OLTP |
| Pide exportar a PDF y ordenar cada columna | No hay entidad ni atributo nuevo. El orden es el de las columnas que ya devuelve cada consulta. El PDF lo genera la aplicación con ese resultado y no se guarda |

## 4. Modelo Conceptual Relacional-Extendido (MERX)

El diseño tiene dos modelos que no se mezclan.

- El **MERX operacional** describe la operación del periodo en curso: personas, oferta, bloques, horarios, sesiones, asistencia y cambios. La figura está en `docs/diagramas/db/merx.drawio` (notación de Chen).
- El **modelo analítico** es un esquema estrella. No es una extensión del MERX operacional: el enunciado pide que el histórico se organice aparte.

### 4.1 Convenciones del MERX

| Símbolo | Significado |
| --- | --- |
| Rectángulo | Entidad |
| Rectángulo de doble borde | Entidad débil |
| Rombo | Relación |
| Rombo de borde grueso | Relación identificativa |
| Óvalo naranja subrayado | Atributo clave |
| Óvalo verde | Atributo |
| Óvalo discontinuo | Atributo derivado |
| Óvalo compuesto | Atributo compuesto |
| Triángulo con *d* | Especialización disjunta |
| *t* | Especialización total |
| Línea gruesa | Participación total |
| Línea fina | Participación parcial |

### 4.2 Especialización de usuario

`USUARIO` (id, identificador, nombre, password_hash) se especializa de forma **total y disjunta** en:

- `ADMINISTRADOR`
- `COORDINADOR ACADÉMICO` (especialidad)
- `ESTUDIANTE` (edad, grupo)
- `JEFE DE DEPARTAMENTO`

No hay usuarios sin rol, y un usuario tiene un solo rol. El coordinador carga bloques y, si está autorizado, genera o valida. El jefe aprueba. El administrador no posee atributos propios: su función es hacer cumplir las reglas de duplicado y de asignación.

### 4.3 Entidades fuertes

| Entidad | Clave | Otros atributos |
| --- | --- | --- |
| PROGRAMA ACADÉMICO | código | nombre, plan de estudios |
| ASIGNATURA | id | nombre |
| FRANJA HORARIA | id | día, hora de inicio, hora de fin |
| BLOQUE DE CONTENIDO | id | título, descripción, tipo de actividad, complejidad, duración; `hash_duplicado` es derivado |
| HORARIO | id | fecha de creación, estado, semestre, generado automáticamente; `equilibrio_cumplido` es derivado; `parámetros` es compuesto. El motivo de una nueva confección vive en la aprobación |
| VALIDACIÓN | id | fecha, decisión, observaciones. Cada fila es un acto |
| APROBACIÓN | id | fecha, decisión, observaciones. Si la decisión es nueva confección, apunta al horario sucesor |
| AULA | id | nombre, edificio, capacidad |
| ASISTENCIA | id | estado, fecha |
| SOLICITUD DE CAMBIO | id | motivo, estado, fecha de solicitud, fecha de resolución, resultado |

El atributo compuesto `parámetros` de HORARIO agrupa proporción teórica, proporción práctica, proporción de laboratorio, cobertura mínima, cantidad de bloques y estrategia. Viaja con el horario porque el enunciado exige guardar la parametrización junto a la generación.

### 4.4 Franja y sesión

`FRANJA HORARIA` es entidad fuerte. El día y el intervalo horario forman un catálogo reusable: la misma franja entra en muchos horarios y es el eje del análisis por franja. No nace con un horario.

`SESIÓN` es la ubicación de un bloque en un horario. Referencia una franja y un aula, las dos obligatorias. No guarda fecha. El horario semanal se repite; cada clase, con su fecha, se registra en la asistencia. No es entidad débil: su hora no es clave parcial del horario, porque esa hora ya está en la franja. No existe una sesión sin el horario que la contiene.

### 4.5 Relaciones, cardinalidad y participación

La participación que se fija aquí es la del negocio, y es la que dibujan las figuras.

| Relación | Entre | Cardinalidad | Participación | Atributos de la relación |
| --- | --- | --- | --- | --- |
| AUTORIZA | Coordinador — Programa | N:N | Parcial en ambos | puede generar, puede validar |
| MATRICULA | Estudiante — Programa | N:N | Total en estudiante, parcial en programa | — |
| CUBRE | Programa — Asignatura | 1:N | Parcial en programa, total en asignatura | — |
| CREA | Coordinador — Bloque | 1:N | Parcial en coordinador, total en bloque | — |
| ABORDA | Bloque — Asignatura | N:1 | Total en bloque, parcial en asignatura | — |
| DE | Programa — Horario | 1:N | Parcial en programa, total en horario | — |
| GENERA | Coordinador — Horario | 1:N | Parcial en coordinador, total en horario | — |
| EMITE | Coordinador — Validación | 1:N | Parcial en coordinador, total en validación | — |
| RECAE | Validación — Horario | N:1 | Total en validación, parcial en horario | — |
| DICTA | Jefe — Aprobación | 1:N | Parcial en jefe, total en aprobación | — |
| RESUELVE | Aprobación — Horario | N:1 | Total en aprobación, parcial en horario | — |
| SUSTITUYE | Aprobación — Horario | N:1 | Parcial en ambos | — |
| ASIGNADO | Estudiante — Horario | N:N | Parcial en ambos | — |
| INCLUYE | Horario — Sesión | 1:N | Parcial en horario, total en sesión | — |
| IMPARTE | Bloque — Sesión | 1:N | Parcial en bloque, total en sesión | — |
| OCUPA | Sesión — Franja | N:1 | Total en sesión, parcial en franja | — |
| USA | Sesión — Aula | N:1 | Total en sesión, parcial en aula | — |
| REGISTRA | Estudiante — Asistencia | 1:N | Parcial en estudiante, total en asistencia | — |
| OCURRE | Asistencia — Sesión | N:1 | Total en asistencia, parcial en sesión | — |
| SOLICITA | Estudiante — Solicitud | 1:N | Parcial en estudiante, total en solicitud | — |
| ATIENDE | Coordinador — Solicitud | 1:N | Parcial en coordinador, total en solicitud | — |
| APOYA | Coordinador — Solicitud | 1:N | Parcial en ambos | — |
| ORIGEN | Solicitud — Horario | N:1 | Total en solicitud, parcial en horario | — |
| DESTINO | Solicitud — Horario | N:1 | Parcial en ambos | — |

Lectura de las decisiones que más condicionan el esquema:

- `CREA` y `GENERA` son relaciones distintas. El autor del bloque no tiene que ser el creador del horario.
- `VALIDACIÓN` es entidad. `EMITE` la une al coordinador y `RECAE` al horario. Cada acto tiene su propio identificador, así que el mismo par puede repetirse. La consulta de horarios validados por un revisor lee esta entidad.
- `APROBACIÓN` es entidad. `DICTA` la une al jefe y `RESUELVE` al horario revisado. La decisión es aprobado o nueva confección. `SUSTITUYE` apunta al horario nuevo solo en el segundo caso. Solo la decisión aprobado vuelve horario final.
- `CUBRE` es 1:N. La asignatura no existe fuera de su programa. No tiene código ni créditos: el enunciado no los pide.
- El grupo no es relación. Es atributo de `ESTUDIANTE`. No hay `PERTENECE` ni `TIENE`.
- `ASIGNADO` es N:N. Un estudiante puede tener varios horarios del mismo programa y semestre. Lo que se prohíbe es el solape de sus sesiones.
- `OCUPA` y `USA` son obligatorias del lado de la sesión. Sin franja no hay hueco semanal; sin aula no hay ocupación ni disponibilidad.
- `APOYA` es opcional: el estudiante puede pedir el cambio sin un segundo coordinador.
- `DESTINO` es opcional: la solicitud existe antes de que el cambio manual asigne otro horario, y puede terminar rechazada.

### 4.6 Paso al relacional operacional

Cada entidad fuerte es una relación. La especialización disjunta se representa con `usuarios` más las tablas de los subtipos que tienen atributos o relaciones propias (`coordinadores`, `estudiantes`). El administrador y el jefe se distinguen por el rol. Las relaciones N:N (`autoriza`, `matricula`, `asignado`) son tablas asociativas. `CUBRE` es 1:N: `asignaturas.programa_id` es obligatoria, y la asignatura no lleva código ni créditos. `estudiantes.grupo` es obligatorio y no es clave foránea: no hay tabla de grupos. `FRANJA HORARIA` es `franjas_horarias`, única por `(día, hora de inicio, hora de fin)`. `SESIÓN` se traduce como `sesiones_horario` con clave subrogada y claves foráneas obligatorias al horario, al bloque, al aula y a la franja. Un aula no se ocupa dos veces en la misma franja del mismo horario. `ASISTE` guarda la fecha de la clase. `VALIDA` y `APRUEBA` son entidades asociativas (`validaciones_horario`, `aprobaciones_horario`, `asistencias`). `validaciones_horario.revisor_id` apunta a `usuarios` y un disparador exige que sea coordinador con `puede_validar` en el programa del horario. `aprobaciones_horario.revisor_id` apunta a `usuarios` y un disparador exige que sea jefe.

El esquema está en `docs/diagramas/db/oltp.sql`.

### 4.7 Modelo analítico (fuera del MERX operacional)

```text
dim_tiempo (periodo, año, semestre)
dim_aula (nombre, edificio)
dim_franja (día, etiqueta, hora inicio, hora fin)
        \          |          /
         fact_ocupacion_aula
         (minutos ocupados, sesiones)

dim_tiempo   dim_grupo (código)   dim_bloque (título, asignatura, complejidad, creador)
     \              |                    /
      fact_asistencia_bloque
      (identificador del estudiante, programa, presentes, ausentes, tasa)
```

`fact_ocupacion_aula` es única por (tiempo, aula, franja). El edificio sale del aula y el día sale de la franja. `fact_asistencia_bloque` guarda el identificador del estudiante, su grupo y el programa, copiados en la carga. Complejidad y creador están en `dim_bloque`. El grupo analítico es el mismo atributo del estudiante: no es un grupo propiedad de un programa. La carga es un proceso aparte: no hay clave foránea entre los dos modelos. La disponibilidad de matrícula no entra en esta estrella: la sirve `proyeccion_disponibilidad`.

## 5. Restricciones de integridad

Se distinguen las que el esquema hace cumplir y las dos que solo puede vigilar la aplicación: quién clasifica un bloque y qué horarios entran en ciertos reportes.

### 5.1 Restricciones de entidad y de dominio

| Restricción | Dónde |
| --- | --- |
| Todo programa, asignatura, franja, usuario, bloque, aula, horario, sesión, validación, aprobación, asistencia y solicitud tiene identificador | Clave primaria |
| El código de programa no se repite. El nombre del aula no se repite. La franja no se repite en `(día, hora de inicio, hora de fin)`. El nombre de la asignatura no se repite dentro de su programa | `UNIQUE` |
| El identificador de acceso del usuario no se repite | `UNIQUE` |
| Nombre, plan de estudios, especialidad, edad, grupo del estudiante, título del bloque, motivo de la solicitud y las medidas de los hechos no quedan vacíos | `NOT NULL` |
| La duración del bloque tiene valor por defecto (90) | `DEFAULT` |
| Las proporciones y la cobertura se guardan con tres decimales; las tasas del analítico, con cuatro | `NUMERIC` |
| Tipo de actividad ∈ {teórica, práctica, laboratorio} | `CHECK` |
| Complejidad ∈ {bajo, medio, alto} | `CHECK` |
| Rol ∈ {administrador, coordinador, estudiante, jefe} | `CHECK` |
| Estado del horario ∈ {borrador, en revisión, aprobado, sustituido} | `CHECK` |
| Decisión de validación ∈ {validado, observado} | `CHECK` |
| Decisión de aprobación ∈ {aprobado, nueva confección} | `CHECK` |
| Estado de asistencia ∈ {presente, ausente} | `CHECK` |
| Estado de la solicitud ∈ {pendiente, resuelta}. El resultado y el destino quedan atados a ese estado | `CHECK` |
| Resultado del cambio ∈ {aceptado, rechazado, nuevo horario asignado}, si existe | `CHECK` que admite nulo |
| Edad positiva; capacidad del aula positiva; duración positiva; cantidad de bloques positiva; proporciones en [0, 1] | `CHECK` |
| La suma de las tres proporciones es 1 | `CHECK` |
| Hora de fin posterior a hora de inicio en la franja | `CHECK` |

### 5.2 Restricciones referenciales

En el OLTP, cada clave foránea declarada impide apuntar a un padre inexistente:

- la autorización y la matrícula apuntan a programa, coordinador o estudiante existentes;
- la asignatura apunta al programa al que pertenece;
- el grupo del estudiante es un valor, no una clave foránea;
- el bloque apunta a una asignatura y a su coordinador creador;
- el horario apunta a un programa y a su coordinador generador;
- la asignación apunta al estudiante y al horario, sin copiar programa ni semestre: un estudiante puede tener más de un horario del mismo programa;
- la sesión apunta a un horario, a un bloque, a un aula y a una franja, todas obligatorias; si se elimina el horario, sus sesiones se eliminan con él (`ON DELETE CASCADE`);
- la validación apunta a un usuario; un disparador exige que sea coordinador con `puede_validar` en el programa del horario;
- la aprobación apunta a un usuario; un disparador exige que su rol sea jefe;
- la asistencia apunta a una sesión, a un estudiante y a la fecha de esa clase, sin una segunda columna de horario;
- la solicitud apunta a estudiante, horario de origen y coordinador asignado;
- el horario destino y el coordinador de apoyo pueden ser nulos;
- `usuarios.coordinador_id` y `usuarios.estudiante_id` son claves foráneas diferidas hacia el subtipo.

En el analítico, la ocupación apunta a tiempo, aula y franja. El edificio sale del aula. La asistencia apunta a tiempo y grupo, dimensiones de ese mismo esquema. No hay clave foránea hacia el OLTP.

### 5.3 Restricciones de negocio que el diseño establece

| Id | Regla | Cómo se sostiene |
| --- | --- | --- |
| IC-01 | Un usuario tiene un solo rol y todo usuario tiene rol | `CHECK` de rol y constraint trigger diferido: el coordinador y el estudiante apuntan a su subtipo, y el administrador y el jefe no tienen subtipo |
| IC-02 | Solo hay una autorización por par coordinador-programa | Clave de `coordinador_programa` |
| IC-03 | Un estudiante no se matricula dos veces en el mismo programa | Clave de `estudiante_programa` |
| IC-04 | Una asignatura pertenece a un solo programa | `asignaturas.programa_id` obligatoria. No hay tabla N:N |
| IC-05 | Un estudiante tiene un único grupo, y ese grupo no es una entidad del programa | `estudiantes.grupo` obligatorio. No hay tabla de grupos ni clave foránea |
| IC-06 | Todo bloque tiene creador y asignatura | `NOT NULL` en ambas claves foráneas |
| IC-07 | Todo horario tiene programa, creador, fecha, semestre y parámetros | `NOT NULL` |
| IC-08 | Una sesión no sobrevive sin su horario, ni existe sin aula y sin franja | Claves foráneas obligatorias y `ON DELETE CASCADE` desde el horario. La franja permanece: es catálogo |
| IC-09 | Un estudiante no tiene dos registros de asistencia de la misma sesión en la misma fecha | `UNIQUE (sesion_id, estudiante_id, fecha)` |
| IC-10 | El mismo par estudiante-horario no se asigna dos veces | Clave de `asignacion_estudiante_horario` |
| IC-11 | La solicitud siempre tiene origen, motivo, estado y coordinador que la atiende | `NOT NULL` |
| IC-12 | El apoyo y el horario destino son opcionales | Claves foráneas nulas |
| IC-13 | El histórico no comparte tablas con la operación | Esquema `analitica` separado, sin clave foránea cruzada |
| IC-14 | Dos bloques con la misma descripción, asignatura y tipo de actividad no coexisten | `UNIQUE (descripcion, asignatura_id, tipo_actividad)` y `hash_duplicado` único. La descripción es obligatoria |
| IC-15 | Un estudiante puede tener más de un horario del mismo programa y semestre | La asignación es N:N. No se copia el programa ni el semestre, y no hay unicidad sobre ese trío |
| IC-16 | La asignación doble es el solape: un estudiante no recibe sesiones que se crucen en el tiempo | Disparadores al asignar y al grabar la sesión. Comparan intervalos del mismo día dentro de un horario y entre los horarios de ese estudiante |
| IC-17 | Solo un coordinador con `puede_generar` crea el horario de ese programa. Solo un coordinador con `puede_validar` lo valida. Quien lo aprueba es el jefe | Disparador sobre `horarios.creador_id`. Disparador de `validaciones_horario` que exige coordinador con `puede_validar` en ese programa. Disparador de `aprobaciones_horario` que exige `usuarios.rol = jefe` |
| IC-18 | Solo el creador del bloque lo clasifica | Regla de la operación de actualización. La base no la expresa |
| IC-19 | Los reportes de «más impartidos» y de equilibrio usan horarios con estado aprobado | Filtro de las consultas. No es una restricción de tabla |
| IC-20 | El rendimiento de los reportes es la tasa de asistencia | Definición de las medidas, no una segunda calificación |

### 5.4 Lo que el SQL cierra y lo que sigue en la aplicación

El script `docs/diagramas/db/oltp.sql` cierra las reglas que antes quedaban solo escritas:

1. **IC-15.** `asignacion_estudiante_horario` solo relaciona estudiante y horario. No copia `programa_id` ni `semestre`, y no declara unicidad sobre ese trío: el estudiante puede cursar más de un horario del mismo programa.
2. **IC-16.** Un disparador al asignar y otro al grabar la sesión rechazan intervalos del mismo día que se cruzan, dentro del horario y entre horarios del mismo estudiante. Esa es la asignación doble.
3. **IC-14.** La descripción es obligatoria. `UNIQUE (descripcion, asignatura_id, tipo_actividad)` impide el duplicado. `hash_duplicado` es la misma clave resumida y también es único.
4. **Dominios.** Rol, tipo de actividad, complejidad, estados, decisión, resultado, proporciones, edad, capacidad, duración y el orden de las horas tienen `CHECK`.
5. **IC-17.** El creador del horario tiene que tener `puede_generar` en ese programa. El revisor de `validaciones_horario` tiene que ser coordinador con `puede_validar` en ese programa. El revisor de `aprobaciones_horario` tiene que ser jefe. Si la decisión es nueva confección, `horario_sucesor_id` es obligatorio y el estado del revisado pasa a sustituido. Los valores de los parámetros del horario nuevo los copia la aplicación; el motivo queda en la aprobación.
6. **IC-01.** `coordinador_id` y `estudiante_id` son claves foráneas diferidas. Un constraint trigger, también diferido, exige que el rol coincida con un solo subtipo y que ese subtipo apunte de vuelta al usuario.
7. **Asistencia.** Se quitó `horario_id`. El horario se obtiene por la sesión. La fila guarda la fecha de esa clase y es única por `(sesion_id, estudiante_id, fecha)`. Otro disparador exige que el estudiante esté asignado a ese horario.
8. **Franja y sesión.** `franjas_horarias` es única por `(dia, hora_inicio, hora_fin)`. Las horas son `TIME`. `sesiones_horario` apunta con claves foráneas obligatorias a horario, bloque, aula y franja. `UNIQUE (horario_id, aula_id, franja_id)` impide dos clases en la misma aula y franja del mismo horario. La sesión no tiene fecha ni clave parcial de reloj.
9. **Hechos.** La ocupación es única por `(tiempo, aula, franja)`. La asistencia es única por `(tiempo, grupo, estudiante, programa, bloque)` e incluye `dim_grupo`. La asignatura va en `dim_bloque`. El programa va copiado en el hecho, no dentro del grupo. Edificio, franja, periodo y código de grupo no se repiten en sus dimensiones.

Siguen fuera de la base, porque una clave no las expresa:

- **IC-18.** Solo el creador del bloque actualiza su clasificación. Lo vigila la operación de actualización.
- **IC-19.** Los reportes de bloques más impartidos y de equilibrio filtran el estado aprobado. Lo vigila la consulta.

## 6. Valoración de la corrección del diseño

El diseño es correcto en su estructura y responde al problema. Cubre los actores, separa la autoría del bloque de la generación del horario, guarda los parámetros junto al horario, modela la validación del coordinador, la aprobación del jefe, la asignación, la asistencia y el cambio con coordinador de apoyo, y saca el histórico del camino transaccional. Esa separación es la decisión de diseño que el enunciado exige de forma explícita.

### 6.1 Lo que el modelo representa bien

- Cada requerimiento informacional de la sección 3 tiene entidad, atributo o relación. Los seis reportes del enunciado se pueden armar con horario, creador, parámetros, validación, bloque, complejidad, asignatura, asistencia y grupo.
- La especialización deja claro que administrador, coordinador, estudiante y jefe no son el mismo papel.
- `CREA`, `GENERA`, `VALIDA` y `APRUEBA` no se colapsan en un solo «responsable del horario». La consulta de revisores lee `VALIDA`. El horario final sale de `APRUEBA`.
- La sesión ubica el bloque en una franja del catálogo y en un aula. La fecha de cada impartición está en la asistencia, porque el hueco semanal se repite. La asistencia no duplica el horario.
- Las relaciones N:N reales (autorización, matrícula y asignación) no se meten como listas dentro de una columna. La asignatura no es N:N: pertenece a un programa. El grupo tampoco es N:N ni entidad: es un atributo del estudiante.
- Los atributos derivados (`hash_duplicado`, `equilibrio_cumplido`, tasas del analítico) están marcados como derivados. Guardarlos es una decisión de consulta, no una confusión con un dato fuente. El duplicado, además, tiene unicidad sobre las columnas fuente.
- El OLTP, quitando esos derivados, está en tercera forma normal.
- El esquema estrella responde sumas, promedios y comparaciones por periodo. El hecho de asistencia conserva estudiante, grupo y programa, así que el promedio del grupo en ese programa sale de ahí.

### 6.2 Conclusión

El MERX operacional, leído con la participación de la sección 4.5, y el esquema estrella separado son un diseño correcto para el sistema de horarios docentes: completo respecto a los requerimientos reformulados, sin mezclar la operación con el histórico, y normalizado en la parte transaccional.

El DDL de `docs/diagramas/db/oltp.sql` y `docs/diagramas/db/olap.sql` cierra el solape de sesiones, el duplicado de bloque, la validación del coordinador, la aprobación del jefe y los dominios. No cierra la asignación con una unicidad por estudiante, programa y semestre: el enunciado no la pide. Quedan en la aplicación la clasificación exclusiva del creador del bloque, el filtro de horarios aprobados en los reportes, la copia de criterios al horario nuevo y la exportación a PDF con el orden de columnas.
