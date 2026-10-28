# Figuras y verificación del informe

- `source/diagrams.py`: las 9 figuras (MERX en la notación del curso y esquema estrella), dibujadas como SVG desde Python. Cada figura es una función registrada en `FIGURES`.
- `source/export.py`: imprime cada figura a PDF vectorial con Chrome o Edge.
- `export/`: los PDF que incluye `main.tex` (`\figura{<nombre>}{...}`). Se versionan en git para que el informe compile sin Python.
- `source/verificacion.py`: define el universo U y el conjunto F del diseño intuitivo, y calcula el cubrimiento minimal, la descomposición en 3FN con PPDF, las llaves de R(U, G) y la comprobación de la PLJ con el algoritmo de la matriz. Escribe las tablas de la sección 4 y del anexo en `../secciones/generado/`, que también se versionan.

## Regenerar

Requisitos: Python 3.9+ y, para las figuras, Chrome o Edge (ruta configurable con la variable `CHROME`).

```bash
python docs/evaluaciones/documentos/informe-diseno-base-de-datos/assets/source/export.py           # todas
python docs/evaluaciones/documentos/informe-diseno-base-de-datos/assets/source/export.py sesion    # una
python docs/evaluaciones/documentos/informe-diseno-base-de-datos/assets/source/verificacion.py     # sección 4
```

El nombre de cada PDF es el id de la figura sin el prefijo `fig-`. Si cambia el modelo, actualiza `UNIVERSO`, `F` y `NOMBRES` en `verificacion.py`, vuelve a ejecutarlo y compila el informe.
