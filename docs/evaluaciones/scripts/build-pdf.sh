#!/usr/bin/env bash
# Compila docs/evaluaciones/documentos/<carpeta>/main.tex → documentos/<carpeta>/entrega/<carpeta>.pdf
set -euo pipefail

EVAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_ROOT="$EVAL_ROOT/documentos"
usage() {
  echo "Uso: $0 <carpeta> | --all" >&2
  echo "Ejemplo: $0 practica-01" >&2
  exit 1
}

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "No se encontró pdflatex. Instala TeX Live o MiKTeX." >&2
  exit 1
fi

list_ids() {
  local dir
  for dir in "$DOCS_ROOT"/*/; do
    [[ -d "$dir" ]] || continue
    [[ -f "${dir}main.tex" ]] || continue
    basename "$dir"
  done
}

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) bib_sep=";" ;;
  *) bib_sep=":" ;;
esac

build_one() {
  local doc_id="$1"
  local doc_dir="$DOCS_ROOT/$doc_id"
  if [[ ! -f "$doc_dir/main.tex" ]]; then
    echo "No hay main.tex en $doc_dir" >&2
    exit 1
  fi
  local out="$doc_dir/entrega"
  mkdir -p "$out"
  local common=(-interaction=nonstopmode -halt-on-error -file-line-error "-output-directory=$out" "-jobname=$doc_id")
  (
    cd "$doc_dir"
    if command -v latexmk >/dev/null 2>&1; then
      # latexmk repite pasadas y ejecuta bibtex/biber cuando hace falta (igual que el CI)
      # BIBINPUTS: bibtex corre desde entrega/ y debe encontrar los .bib de la carpeta del documento
      BIBINPUTS="..$bib_sep" latexmk -pdf "${common[@]}" main.tex
    else
      echo "latexmk no encontrado: se usa pdflatex x2 (la bibliografía no se resuelve)." >&2
      pdflatex "${common[@]}" main.tex
      pdflatex "${common[@]}" main.tex
    fi
  )
  echo "PDF: $out/$doc_id.pdf"
}

if [[ $# -ne 1 ]]; then
  usage
fi

mapfile -t ids < <(list_ids | sort)

if [[ "$1" == "--all" ]]; then
  if [[ ${#ids[@]} -eq 0 ]]; then
    echo "No hay evaluaciones en documentos/ (ninguna carpeta con main.tex)."
    exit 0
  fi
  for id in "${ids[@]}"; do
    echo "=== $id ==="
    build_one "$id"
  done
else
  if [[ ${#ids[@]} -eq 0 ]]; then
    echo "documentos/ está vacío. Crea documentos/<nombre>/main.tex." >&2
    exit 1
  fi
  if [[ " ${ids[*]} " != *" $1 "* ]]; then
    echo "Carpeta desconocida: $1. Disponibles: ${ids[*]}" >&2
    exit 1
  fi
  build_one "$1"
fi
