# Convenciones de código

Reglas de estilo y estructura previstas para el backend y el frontend.

## 1. Generales

- **Idioma del código:** inglés. Variables, funciones, clases, comentarios y docstrings en inglés.
- **Idioma de la documentación:** español.
- **Idioma de la app final de cara al usuario:** español.
- **Indentación:** 4 espacios en Python, TypeScript, JSON. 2 espacios en YAML.
- **Líneas:** máximo 100 caracteres. Cuando exista el código, ruff y prettier lo aplican.
- **Final de archivo:** siempre con newline.
- **Sin trailing whitespace.**
- **UTF-8 sin BOM.**



## 2. Backend (Python)



### 2.1 Nombres

- Clases: `PascalCase` (`AcademicProgram`, `ScheduleService`).
- Funciones y variables: `snake_case` (`get_by_id`, `program_id`).
- Constantes: `UPPER_SNAKE_CASE` (`CACHE_PREFIX`, `REPORT_TTL`).
- Módulos: `snake_case` (`academic_program_repository.py`).



### 2.2 Imports

Orden estricto:

1. Standard library.
2. Third-party.
3. Local (`app.*`).

Separados por una línea vacía entre grupos. Cuando exista el backend, ruff lo aplica con `ruff check --fix`.

### 2.3 Type hints

Obligatorios en todas las funciones. Sin excepciones.

```python
    def get_by_id(db: Session, program_id: int) -> AcademicProgram | None:
        ...
```

Usar `T | None` en lugar de `Optional[T]`. Usar `list[X]` en lugar de `List[X]`.

### 2.4 Docstrings

Toda función pública lleva docstring. Formato Google-style.

```python
    def create_program(db: Session, data: AcademicProgramCreate) -> AcademicProgram:
        """Create a new program.

        Args:
            db: Database session.
            data: Validated program creation payload.

        Returns:
            The created program.

        Raises:
            ConflictError: If the name is already in use.
        """
        ...
```



### 2.5 Errores

Nunca lanzar `HTTPException` desde un servicio. Lanzar excepciones de dominio (`NotFoundError`, `ConflictError`, `ValidationError`, `ForbiddenError`, `UnauthorizedError`). El handler global las convierte.

### 2.6 Commits

```
feat: add schedule generation endpoint
fix: prevent duplicate program names
docs: update architecture with cache section
test: add unit tests for auth service
refactor: extract username derivation into user_service
ci: add GitHub Actions workflow
```



## 3. Frontend (TypeScript + React)



### 3.1 Nombres

- Componentes: `PascalCase` (por ejemplo, `DataTable.tsx`, `ProgramForm.tsx`).
- Hooks: `camelCase` con prefijo `use` (`useAuth`, `useQuery`).
- Variables y funciones: `camelCase` (`handleSubmit`, `programId`).
- Constantes: `UPPER_SNAKE_CASE` (`DAY_NAMES`, `COMPLEXITY_LABELS`).
- Interfaces y tipos: `PascalCase` (`AcademicProgram`, `ScheduleDetail`).



### 3.2 Estructura de componentes

```ts
    import { useState, type FormEvent } from 'react';

    import { createProgram } from '../api/programs';
    import Button from '../components/Button';

    interface Props {
        id: number;
        onClose: () => void;
    }

    export default function Component({ id, onClose }: Props) {
        const [error, setError] = useState<string | null>(null);

        function handleSubmit(event: FormEvent): void {
            event.preventDefault();
            // ...
        }

        return (
            <div>
                {/* ... */}
            </div>
        );
    }
```



### 3.3 Imports

Orden:

1. React.
2. Librerías externas (TanStack Query, react-router, axios).
3. Componentes y utilidades locales.

Separados por línea vacía entre grupos.

### 3.4 Type hints

Todo tipo. Sin `any`. Interfaces explícitas para props.

```ts
    interface DataTableProps<T> {
        columns: Column<T>[];
        items: T[];
        getKey: (item: T) => number | string;
        actions?: (item: T) => ReactNode;
    }
```



### 3.5 Estilos

Inline con objeto `style` para este proyecto. Paleta:

- Fondo del main: `#e5e7eb`.
- Sidebar: `#1f2937`.
- Cards: `#ffffff`.
- Texto principal: `#1f2937`.
- Texto secundario: `#6b7280`.
- Acento (botones, links): `#3b82f6`.
- Peligro: `#ef4444`.



### 3.6 Manejo de errores

Siempre mostrar el error al usuario. No silenciar. Usar el campo `detail` del backend si está disponible.

```ts
    onError: (err: { response?: { data?: { detail?: string } } }) => {
        setError(err.response?.data?.detail ?? 'Could not complete the operation.');
    }
```



## 4. Base de datos

El diseño está en `docs/informes/informe-diseno-base-de-datos.md`. Los nombres de tablas y columnas siguen ese esquema, en inglés.

- Tablas en plural y `snake_case` (`academic_programs`, `schedule_sessions`).
- Columnas en `snake_case` (`program_id`, `created_at`).
- PK `id`, salvo las tablas asociativas con PK compuesta (`coordinator_program`, `student_program`, `student_schedule_assignment`).
- FKs con sufijo `_id` (`program_id`, `classroom_id`).
- Timestamps: `TIMESTAMPTZ`.
- Booleanos como en el esquema: `can_generate`, `can_validate`, `automatically_generated`, `balance_met`.
- Valores de dominio en español, con los `CHECK` del DDL (`teórica`, `aprobado`, `jefe`).
- El código de la aplicación se escribe en inglés. El nombre de una tabla no se traduce en el esquema.



## 5. Tests



### Backend

- Nombres de archivo: `test_*.py`.
- Nombres de función: `test_*`.
- Docstring breve en cada test.
- Un assert principal por test, los auxiliares pueden agruparse.



### Frontend

- Nombres de archivo: `*.test.tsx`.
- Uso de `describe` e `it`.
- Mocks con `vi.mock`.
- Reset de mocks en `beforeEach`.



## 6. Git

- Rama `main`: estable.
- Rama `develop`: integración.
- Ramas `feature/*`: una por tarea.
- PR antes de mergear a `develop`.
- Mensajes en inglés, imperativo.



## 7. Archivos que no se tocan

- `.env` nunca se commitea.
- `.env.example` sí.
- `node_modules/`, `__pycache__/`, `.venv/` quedan en `.gitignore`.
- Migraciones de Alembic se commitean.

