# Figuras del informe

- `source/diagrams.py`: las 10 figuras (MERX en notación de Chen y esquema estrella), dibujadas como SVG desde Python. Cada figura es una función registrada en `FIGURES`.
- `source/export.py`: imprime cada figura a PDF vectorial con Chrome o Edge.
- `export/`: los PDF que incluye `main.tex` (`\figura{<nombre>}{...}`). Se versionan en git para que el informe compile sin Python.

## Regenerar

Requisitos: Python 3.9+ y Chrome o Edge (ruta configurable con la variable `CHROME`).

```bash
python docs/evaluaciones/documentos/informe-diseno-base-de-datos/assets/source/export.py           # todas
python docs/evaluaciones/documentos/informe-diseno-base-de-datos/assets/source/export.py valida    # una
```

El nombre de cada PDF es el id de la figura sin el prefijo `fig-`. Tras exportar, vuelve a compilar el informe.
