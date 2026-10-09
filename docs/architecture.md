# Arquitectura del sistema

Propuesta de arquitectura, patrones y decisiones de diseño del sistema de horarios docentes.

## Tabla de contenido

1. Visión general
2. Diagrama de capas
3. Flujo de una petición
4. Capas del backend
5. Patrones de diseño
6. Modelo de datos
7. Caché con Redis
8. Autenticación y autorización
9. Frontend
10. Generación con OR-Tools
11. Histórico y ETL
12. Decisiones arquitectónicas
13. Consideraciones de seguridad

---

## 1. Visión general

La propuesta organiza el sistema en capas, con separación estricta entre presentación, API, lógica de negocio, acceso a datos y persistencia. El backend expondría una API REST en JSON; el frontend sería una SPA que la consume.

### Principios

- Desacoplamiento: cada capa conoce solo a la inmediatamente inferior.
- Responsabilidad Única: routers manejan HTTP, servicios la lógica, repositorios SQL.
- Explicit over implicit: sin auto-registro de routers ni magia oculta.
- Degradación elegante: si Redis falla, la aplicación sigue funcionando.
- Testing desde el día 1: cada vertical se cierra con sus tests.

---

## 2. Diagrama de capas

Estructura prevista de la solución.

    ┌──────────────────────────────────────────────────────────────────┐
    │                      Frontend (React + TS)                       │
    │ Login │ Dashboard │ Horarios │ Reportes │ Asistencia │ Histórico │
    └────────────────────────────┬─────────────────────────────────────┘
                                 │  HTTP/JSON (JWT en Authorization)
                                 ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                    Backend (FastAPI + Uvicorn)                   │
    │                                                                  │
    │  ┌─────────────────────────────────────────────────────────────┐ │
    │  │ Routers: /auth /users /programs /subjects /coordinators...  │ │
    │  │          /content-blocks /schedules /assignments            │ │
    │  │          /attendances /change-requests /reports /historical │ │
    │  └──────────────────────────┬──────────────────────────────────┘ │
    │                             │                                    │
    │  ┌──────────────────────────▼──────────────────────────────────┐ │
    │  │ Servicios: lógica de negocio, validaciones, orquestación    │ │
    │  └──────────────────────────┬──────────────────────────────────┘ │
    │                             │                                    │
    │  ┌──────────────────────────▼──────────────────────────────────┐ │
    │  │ Repositorios: SQLAlchemy, queries, transacciones            │ │
    │  └──────────────────────────┬──────────────────────────────────┘ │
    │                             │                                    │
    │  ┌──────────────────────────▼──────────────────────────────────┐ │
    │  │ Modelos SQLAlchemy + Schemas Pydantic                       │ │
    │  └─────────────────────────────────────────────────────────────┘ │
    └──────┬────────────────────────────────────┬──────────────────────┘
           │                                    │
           ▼                                    ▼
    ┌──────────────────────┐         ┌──────────────────────┐
    │  PostgreSQL 16       │         │   Redis 7 (caché)    │
    │  ┌────────────────┐  │         │  Reportes            │
    │  │ public         │  │         │  Listados            │
    │  │  operativo     │  │         │  Detalles            │
    │  ├────────────────┤  │         └──────────────────────┘
    │  │ analitica      │  │
    │  │  estrella      │  │
    │  └────────────────┘  │
    └──────────────────────┘

---

## 3. Flujo de una petición

Ejemplo del flujo previsto: el coordinador pulsa Generate Schedule.

    [Usuario] pulsa Generate
        │
        ▼
    [React] TanStack Query dispara mutation
        │
        ▼
    [axios] añade header Authorization: Bearer <token>
        │
        ▼
    [Uvicorn] recibe la petición HTTP
        │
        ▼
    [Middleware de logging] registra método, ruta, duración
        │
        ▼
    [FastAPI] resuelve dependencias:
        - get_db → sesión de PostgreSQL
        - get_current_user → usuario desde JWT
        - require_role(COORDINATOR) → verifica rol
        │
        ▼
    [Router] valida el body con Pydantic (GenerateScheduleRequest)
        │
        ▼
    [Servicio schedule_generator_service]
        ├─ Carga bloques de la BD (repositorio)
        ├─ Valida que pertenezcan al programa
        ├─ Carga franjas y aulas
        ├─ Construye el modelo CP-SAT
        ├─ Ejecuta el solver (timeout 60s)
        ├─ Persiste Schedule + ScheduleBlock
        └─ Invalida la caché
        │
        ▼
    [Router] serializa con ScheduleDetail (Pydantic)
        │
        ▼
    [Uvicorn] envía la respuesta JSON al frontend
        │
        ▼
    [TanStack Query] invalida queries y redirige a /schedules/{id}

En la propuesta, si en cualquier punto se lanza una excepción de dominio (NotFoundError, ConflictError, ValidationError), el handler global la convierte en respuesta HTTP con el status y mensaje correspondientes. Los routers no contienen try/except.

---

## 4. Capas del backend

Organización prevista del backend. Los fragmentos de código ilustran la forma prevista; no son extractos del repositorio.

### 4.1 API (app/routers/)

Responsabilidad:
- Recibir peticiones HTTP.
- Validar entrada con Pydantic.
- Llamar al servicio correspondiente.
- Devolver respuesta serializada.

No debe:
- Contener lógica de negocio.
- Acceder directamente a la base de datos.
- Conocer detalles del ORM.
- Capturar excepciones de dominio.

Ejemplo de la forma prevista:

```python
    @router.post("/generate", response_model=ScheduleDetail, status_code=201)
    def generate_schedule(
        data: GenerateScheduleRequest,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(require_role(UserRole.COORDINATOR))],
    ) -> Schedule:
        if user.coordinator_id is None:
            raise ForbiddenError("Coordinator profile not linked")
        coordinator = coordinator_repository.get_by_id(db, user.coordinator_id)
        if coordinator is None:
            raise ForbiddenError("Coordinator profile not found")
        schedule, _ = schedule_generator_service.generate_schedule(db, data, coordinator)
        return schedule_service.get_schedule(db, schedule.id)
```

### 4.2 Servicios (app/services/)

Responsabilidad:
- Concentrar reglas de negocio.
- Orquestar repositorios.
- Lanzar excepciones de dominio.
- Gestionar transacciones lógicas.

No debe:
- Conocer HTTP.
- Construir queries SQL.
- Depender de FastAPI.

Ejemplo de la forma prevista:

```python
    def create_program(db: Session, data: AcademicProgramCreate) -> AcademicProgram:
        if academic_program_repository.get_by_name(db, data.name):
            raise ConflictError(f"Program name '{data.name}' is already taken")
        program = AcademicProgram(name=data.name, study_plan=data.study_plan)
        return academic_program_repository.add(db, program)
```

### 4.3 Repositorios (app/repositories/)

Responsabilidad:
- Único punto de acceso a la base de datos.
- Encapsular queries SQLAlchemy.
- Sin lógica de negocio.

Ejemplo de la forma prevista:

```python
    def get_by_name(db: Session, name: str) -> AcademicProgram | None:
        return db.query(AcademicProgram).filter(AcademicProgram.name == name).first()

    def add(db: Session, program: AcademicProgram) -> AcademicProgram:
        db.add(program)
        db.commit()
        db.refresh(program)
        return program
```

### 4.4 Modelos (app/models/)

Entidades SQLAlchemy 2.0 con Mapped y mapped_column. Representan tablas y relaciones.

### 4.5 Schemas (app/schemas/)

Modelos Pydantic. Representan contratos de entrada y salida.
Nunca se expone un modelo SQLAlchemy directamente en la API. Siempre se usa response_model con un schema Pydantic.

### 4.6 Core (app/core/)

| Archivo | Función |
|---------|---------|
| config.py | Settings con pydantic-settings |
| security.py | bcrypt + JWT |
| cache.py | Helpers de Redis |
| redis.py | Cliente Redis compartido |
| exceptions.py | Excepciones de dominio |
| error_handlers.py | Handler global |
| middleware.py | Request logging |

---

## 5. Patrones de diseño

### 5.1 Repository

Problema: los servicios no deben saber si los datos vienen de PostgreSQL, MongoDB o un archivo.

Solución: cada entidad tiene su módulo de repositorio con funciones puras. El servicio solo ve estas funciones.

Ubicación prevista: app/repositories/.

### 5.2 Service Layer

Problema: los routers no deben contener reglas de negocio.

Solución: cada dominio tiene su módulo de servicio. Concentra validaciones, orquesta repositorios, lanza excepciones.

Ubicación prevista: app/services/.

### 5.3 DTO (Data Transfer Object)

Problema: la representación externa (JSON) no debe acoplarse a la interna (ORM).

Solución: schemas Pydantic separados por operación:
- XxxCreate: entrada para crear.
- XxxUpdate: entrada para actualizar.
- XxxRead: salida estándar.
- XxxCreateResponse: salida con campos extra.

Ubicación prevista: app/schemas/.

### 5.4 Strategy

Problema: el generador de horarios puede evolucionar con distintas estrategias.

Solución: el servicio previsto `schedule_generator_service` expone una función `generate_schedule`. Internamente tendría `_build_model`, `_load_blocks` y `_validate_program`. Si más adelante se añade otra estrategia, se crea un módulo nuevo sin tocar los routers.

Ubicación prevista: app/services/schedule_generator_service.py.

### 5.5 Cache-Aside

Problema: consultas costosas repetidas.

Solución: los endpoints consultarían primero Redis. Si hay miss, consultan la BD, guardan en Redis con TTL y devuelven. Al escribir, invalidan.

Ubicación prevista: app/core/cache.py, aplicada en routers/reports.py y routers/schedules.py.

### 5.6 Dependency Injection

Problema: compartir recursos (sesión de BD, usuario actual, rol) sin repetir código.

Solución: Depends de FastAPI. Los endpoints declaran lo que necesitan y FastAPI lo resuelve.

Ubicación prevista: app/dependencies/auth.py, app/db/session.py.

---

## 6. Modelo de datos

La fuente del diseño es `docs/informes/informe-diseno-base-de-datos.md`. El DDL está en `docs/diagramas/db/oltp.sql` y `docs/diagramas/db/olap.sql`.

### 6.1 Esquema operativo (public)

- `usuarios` se especializa, de forma total y disjunta, en coordinador, estudiante, administrador o jefe.
- `programas_academicos` 1—N `asignaturas`. La asignatura no se comparte entre programas.
- `coordinador_programa` separa `puede_generar` y `puede_validar`.
- `estudiante_programa` es la matrícula. `estudiantes.grupo` es un atributo, no una entidad.
- `bloques_contenido` los crea un coordinador. Duplicado: misma descripción, asignatura y tipo de actividad. La complejidad no distingue.
- `horarios` guarda creador, fecha, semestre, estado y los parámetros: proporciones por tipo de actividad, cobertura mínima, cantidad total y estrategia.
- `sesiones_horario` ubica un bloque en un aula y una franja del catálogo. No guarda la fecha de la clase.
- `validaciones_horario`: varios actos. El revisor es un usuario coordinador con `puede_validar` en el programa. Decisión: validado u observado.
- `aprobaciones_horario`: varios actos. El revisor es un usuario con rol jefe. Decisión: aprobado o nueva confección. El horario final es el aprobado.
- `asignacion_estudiante_horario` es N:N. Puede haber más de un horario del mismo programa y semestre. La asignación doble es el solape de sesiones.
- `asistencias` es única por sesión, estudiante y fecha.
- `solicitudes_cambio` guarda origen, destino opcional, coordinador asignado y apoyo opcional.
- `proyeccion_disponibilidad` sirve la lectura de matrícula. No forma parte del histórico.

### 6.2 Reglas que cierra el esquema

| Regla | Dónde |
|-------|--------|
| Duplicado de bloque | `UNIQUE (descripcion, asignatura_id, tipo_actividad)` |
| Solape de sesiones del estudiante | Disparadores al asignar y al grabar la sesión |
| Más de un horario del mismo programa | Sin unicidad por estudiante, programa y semestre |
| Quién valida | `revisor_id` hacia `usuarios` y disparador de `puede_validar` |
| Quién aprueba | `revisor_id` hacia `usuarios` con rol jefe. Varios actos por horario |
| Asistencia repetida | `UNIQUE (sesion_id, estudiante_id, fecha)` |
| Misma aula y franja en un horario | `UNIQUE (horario_id, aula_id, franja_id)` |

### 6.3 Esquema analítico (analitica)

Estrella, sin claves foráneas hacia el operativo. Dos hechos:

- `dim_tiempo`, `dim_aula`, `dim_franja`, `dim_grupo` (código del grupo del estudiante), `dim_bloque`.
- `fact_ocupacion_aula`, única por tiempo, aula y franja. El edificio sale del aula.
- `fact_asistencia_bloque`, única por tiempo, grupo, estudiante, programa y bloque.

La solicitud de cambio permanece en el OLTP. El promedio del grupo en un programa sale de `fact_asistencia_bloque`.

---

## 7. Caché con Redis

La propuesta usa el patrón cache-aside con invalidación por namespace. La lectura repetida de matrícula sale de `proyeccion_disponibilidad`, no de la estrella `analitica` ni de un recorrido del detalle de sesiones.

### Claves

Todas las claves van prefijadas con cache: para poder limpiarlas en bloque.

Ejemplos:
- cache:report:schedules:program_id=1
- cache:schedules:detail:id=42

### TTLs

| Endpoint | TTL |
|----------|-----|
| Reportes | 300 s |
| Listado de horarios | 60 s |
| Detalle de horario | 60 s |

### Invalidación

Al escribir, la propuesta llama a `cache_clear()`, que recorre las claves con SCAN y las elimina. Es agresivo, pero simple y correcto para el volumen del proyecto.

### Degradación elegante

Los helpers capturarían `redis.RedisError` con `contextlib.suppress`. Si Redis no responde, el endpoint consulta la BD y sigue funcionando.

---

## 8. Autenticación y autorización

### Flujo

    POST /auth/login
        │
        ▼
    Verificar credenciales (bcrypt)
        │
        ▼
    Generar access token (30 min) + refresh token (7 días)
        │
        ▼
    Frontend guarda tokens en localStorage
        │
        ▼
    Cada petición añade Authorization: Bearer <access_token>

### Dependencias

- get_current_user: extrae el usuario del JWT.
- require_role(*roles): verifica que el rol esté autorizado.

Ejemplo de la forma prevista:

    @router.post("/", response_model=UserRead, status_code=201)
    def create_user(
        data: UserCreate,
        db: Annotated[Session, Depends(get_db)],
        _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    ) -> User:
        return user_service.create_user(db, data)

### Roles

Los valores guardados en `usuarios.rol` son `administrador`, `coordinador`, `jefe` y `estudiante`.

| Rol | Puede hacer |
|-----|-------------|
| administrador | Impide bloques duplicados y el solape de sesiones |
| coordinador | Bloques propios; genera si `puede_generar`; valida si `puede_validar`; ve horarios del mismo programa; ocupación y apoyo en cambios |
| jefe | Aprueba el horario o pide otra confección. No sustituye la validación del coordinador |
| estudiante | Sus horarios, asistencia y solicitudes de cambio |

### En el frontend

En la propuesta, `ProtectedRoute` verifica autenticación y rol. El Sidebar filtra ítems según el rol. Al cerrar sesión, `queryClient.clear()` limpia la caché del usuario anterior.

---

## 9. Frontend

### Estructura

Estructura prevista del frontend:

    src/
    ├── api/              Clientes HTTP (axios)
    ├── components/       Componentes reutilizables
    ├── contexts/         AuthContext + AuthProvider
    ├── hooks/            useAuth
    ├── pages/            Vistas por ruta
    │   └── reports/      Subpáginas de reportes
    ├── test/             Configuración de Vitest
    ├── App.tsx
    └── main.tsx

### Estado del servidor

TanStack Query manejaría:
- Caché de peticiones (por queryKey).
- Refetch automático al invalidar.
- Mutaciones con callbacks (onSuccess, onError).

Al cerrar sesión o cambiar de usuario, `queryClient.clear()` limpia toda la caché.

### Rutas

Planas, sin anidar. Cada ruta protegida declara los roles permitidos.

Ejemplo de la forma prevista:

    <Route
        path="/schedules/generate"
        element={
            <ProtectedPage allowedRoles={['coordinator']}>
                <GenerateSchedule />
            </ProtectedPage>
        }
    />

---

## 10. Generación con OR-Tools

### Modelo CP-SAT

La propuesta modela la generación con CP-SAT.

Variables: x[b][s][c] booleana, 1 si el bloque b va en la franja s en el aula c.

Restricciones duras:
1. El bloque de la sesión pertenece al programa del horario.
2. Cada sesión tiene aula y franja del catálogo.
3. Un aula vigente no queda ocupada dos veces en la misma franja.
4. Un estudiante no recibe sesiones que se solapan.

Criterios que se guardan con el horario. De ellos sale `equilibrio_cumplido`:
1. Proporción de bloques por tipo de actividad (teórica, práctica, laboratorio).
2. Cobertura mínima de asignaturas del programa.
3. Cantidad total de bloques.

Esos criterios no se sustituyen por un reparto por día. Un segundo horario del mismo programa no es conflicto. La complejidad no parte un bloque duplicado.

Solver: CP-SAT con max_time_in_seconds configurable (60 por defecto). Si encuentra OPTIMAL o FEASIBLE, guarda el horario y sus parámetros. Si no, lanza ValidationError.

### Complejidad

| Bloques | Franjas | Aulas | Variables | Tiempo típico |
|---------|---------|-------|-----------|---------------|
| 4 | 6 | 2 | 48 | < 1 s |
| 20 | 30 | 5 | 3 000 | 1–5 s |
| 100 | 60 | 10 | 60 000 | 30–60 s |

---

## 11. Histórico y ETL

### Objetivo

Conservar datos de semestres anteriores sin afectar las operaciones transaccionales.

### Diseño

- Esquema separado `analitica` en PostgreSQL. Es una estrella, no una copia de dos tablas.
- Sin claves foráneas hacia el operativo.
- Hechos: `fact_ocupacion_aula` y `fact_asistencia_bloque`.
- La disponibilidad de matrícula no entra en la estrella. La sirve `proyeccion_disponibilidad`.

### ETL

Carga aparte, solo administrador, por periodo. No usa el OLTP como camino de consulta.

Pasos:
1. Toma los horarios del periodo que se cierra.
2. Sustituye el snapshot de ese periodo.
3. Agrega ocupación por tiempo, aula y franja.
4. Agrega asistencia por tiempo, grupo, estudiante, programa y bloque.

### Consultas agregadas

- Ocupación por franja y por edificio. El edificio sale de `dim_aula`.
- Asistencia por bloque, complejidad y creador. Esos atributos salen de `dim_bloque`.
- Promedio del grupo en un programa, desde `fact_asistencia_bloque`.

---

## 12. Decisiones arquitectónicas

Estas decisiones fijan el stack de la propuesta.


Por qué SQLAlchemy 2.0: tipado fuerte, soporte sync y async, integración directa con Alembic.

Por qué PostgreSQL : PostgreSQL tiene mejor soporte de JSONB, tipos ENUM, esquemas separados, particionado, y es gratuito. SQLite no escala.

Por qué Redis y no solo PostgreSQL: reportes y listados se consultan repetidas veces. Redis elimina la carga. Si Redis cae, la app sigue funcionando.

Por qué un esquema histórico separado: el enunciado lo exige y el informe lo fija como estrella `analitica`, con ocupación y asistencia, aparte de la proyección de matrícula.

Por qué OR-Tools: gratuito, de Google, con CP-SAT que resuelve scheduling con restricciones complejas. Gurobi es caro. Escribir un solver desde cero es inviable.

Por qué Docker Compose y no Kubernetes: suficiente para desarrollo y para un servidor único.


Por qué no interfaces abstractas para repositorios: el patrón Repository no exige interfaces abstractas. Exige que la lógica de negocio no dependa del ORM.

---

## 13. Consideraciones de seguridad

Medidas previstas para la aplicación:

- Contraseñas con bcrypt.
- JWT firmado con HS256.
- CORS restringido a los orígenes permitidos.
- Validación de entrada con Pydantic en todos los endpoints.
- Autorización por rol en cada endpoint protegido.
- Los tokens se guardarían en localStorage (válido para curso, no para producción con XSS).
- En producción se debería usar HTTPS y HttpOnly cookies.
- Nunca commitear .env.

---

