.PHONY: pdf pdf-all clean

# ID = nombre de carpeta bajo documentos/ (ej. 03-practica-arquitectura)
ID ?=

ifeq ($(OS),Windows_NT)
pdf:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-pdf.ps1 -Id "$(ID)"
pdf-all:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-pdf.ps1 -All
else
pdf:
	@test -n "$(ID)" || { echo "Uso: make pdf ID=<carpeta>" >&2; exit 1; }
	bash scripts/build-pdf.sh $(ID)
pdf-all:
	bash scripts/build-pdf.sh --all
endif

clean:
ifeq ($(OS),Windows_NT)
	powershell -NoProfile -Command "Get-ChildItem -Path documentos -Directory | ForEach-Object { $$e = Join-Path $$_.FullName 'entrega'; if (Test-Path $$e) { Remove-Item -Recurse -Force $$e } }"
else
	find documentos -type d -name entrega -exec rm -rf {} +
endif
