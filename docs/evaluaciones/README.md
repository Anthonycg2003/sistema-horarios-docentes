# Evaluaciones (LaTeX → PDF)

Carpeta para **fuentes LaTeX** de evaluaciones del curso. Cada entrega vive en `documentos/<nombre>/` (fuentes versionadas en git). Al compilar, el PDF y los auxiliares van a `documentos/<nombre>/entrega/` (carpeta ignorada por git: no hace falta subir el PDF de cada persona a GitHub).


## Añadir una evaluación

1. Crear `documentos/<nombre>/` (sin espacios; p. ej. `practica-01` o `03-seminario-arquitectura`).
2. Poner ahí `main.tex` y los `.tex` que necesitéis (`\input{...}` relativos a esa carpeta; evitad `\include` con subcarpetas, `pdflatex` no crea `entrega/<subcarpeta>/`).
3. Tras compilar, el PDF queda en `documentos/<nombre>/entrega/<nombre>.pdf`.

Ejemplo mínimo de `documentos/practica-01/main.tex`:

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\begin{document}
Hola, evaluación.
\end{document}
```

## Compilar en local

Requisito: `pdflatex` (MiKTeX o TeX Live). Para **bibliografía** (`\cite`, BibTeX/biber) instala además `latexmk` (en MiKTeX requiere Perl; `biber` si usas `biblatex`): los scripts lo usan automáticamente, igual que el CI. Sin `latexmk` hacen solo dos pasadas de `pdflatex` y avisan de que las citas no se resuelven.

```powershell
# Una carpeta
.\docs\evaluaciones\scripts\build-pdf.ps1 -Id practica-01

# Todas las que tengan main.tex
.\docs\evaluaciones\scripts\build-pdf.ps1 -All
```

```bash
./docs/evaluaciones/scripts/build-pdf.sh practica-01
./docs/evaluaciones/scripts/build-pdf.sh --all
```

```bash
make -C docs/evaluaciones pdf ID=practica-01
make -C docs/evaluaciones pdf-all
```

Si no hay carpetas con `main.tex`, `pdf-all` / `-All` termina sin error.

## Bibliografía

Pon el `.bib` en la misma carpeta (`documentos/<nombre>/referencias.bib`) y en `main.tex` usa `ibliographystyle{...}` + `ibliography{referencias}` (BibTeX) o `biblatex` + `ddbibresource{referencias.bib}` (biber). Tanto en local (con `latexmk`) como en CI se ejecuta bibtex/biber solo.

## CI

El workflow [`.github/workflows/evaluaciones-latex.yml`](../../.github/workflows/evaluaciones-latex.yml) se ejecuta al cambiar `docs/evaluaciones/**`:

- En cada push/PR compara el diff y compila **solo** las carpetas `documentos/<nombre>/` con archivos modificados (y `main.tex` presente), **en paralelo** (un job por carpeta).
- Si cambian `Makefile`, `scripts/` o el propio workflow, compila **todas** las evaluaciones (por si afecta al build).
- Cambios solo en `README.md` u otros archivos fuera de `documentos/<nombre>/` no disparan compilación.
- Si no hay carpetas que compilar, el pipeline queda en verde sin jobs de LaTeX.
- Cada job publica un artefacto con el PDF (`<nombre-carpeta>.pdf`).

No hace falta editar el workflow al añadir una evaluación nueva.

## Estructura

```text
docs/evaluaciones/
  README.md
  documentos/
    <nombre>/          main.tex y demás fuentes (en git)
      entrega/         PDF y basura de pdflatex (gitignore)
  scripts/             build-pdf.ps1, build-pdf.sh
  Makefile
```
