# Compila docs/evaluaciones/documentos/<carpeta>/main.tex → documentos/<carpeta>/entrega/<carpeta>.pdf
param(
    [string]$Id = "",
    [switch]$All
)

$ErrorActionPreference = "Stop"
$miktexBin = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"
if (Test-Path $miktexBin) {
    $env:Path = "$miktexBin;$env:Path"
}

function Get-DocumentIds {
    param([string]$DocsRoot)
    Get-ChildItem -Directory $DocsRoot -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName "main.tex") } |
        Sort-Object Name |
        ForEach-Object { $_.Name }
}

function Build-Document {
    param([string]$DocId)
    $evalRoot = Split-Path -Parent $PSScriptRoot
    $docDir = Join-Path (Join-Path $evalRoot "documentos") $DocId
    if (-not (Test-Path (Join-Path $docDir "main.tex"))) {
        throw "No hay main.tex en $docDir"
    }
    $out = Join-Path $docDir "entrega"
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $job = $DocId
    $common = @(
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory=$out",
        "-jobname=$job"
    )
    Push-Location $docDir
    try {
        if (Get-Command latexmk -ErrorAction SilentlyContinue) {
            # latexmk repite pasadas y ejecuta bibtex/biber cuando hace falta (igual que el CI)
            # BIBINPUTS: bibtex corre desde entrega/ y debe encontrar los .bib de la carpeta del documento
            $env:BIBINPUTS = "..;"
            latexmk -pdf @common main.tex
            if ($LASTEXITCODE -ne 0) { throw "latexmk falló en $DocId" }
        } else {
            Write-Warning "latexmk no encontrado: se usa pdflatex x2 (la bibliografía no se resuelve)."
            $extra = @()
            if ($env:Path -match "MiKTeX") { $extra = @("--enable-installer") }
            foreach ($pass in 1..2) {
                pdflatex @common @extra main.tex
                if ($LASTEXITCODE -ne 0) { throw "pdflatex falló en $DocId (pasada $pass)" }
            }
        }
    } finally {
        Pop-Location
    }
    Write-Host "PDF: $(Join-Path $out "$job.pdf")"
}

if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
    throw "No se encontró pdflatex. Instala MiKTeX o TeX Live."
}

$evalRoot = Split-Path -Parent $PSScriptRoot
$docsRoot = Join-Path $evalRoot "documentos"
$ids = @(Get-DocumentIds -DocsRoot $docsRoot)

if ($All) {
    if ($ids.Count -eq 0) {
        Write-Host "No hay evaluaciones en documentos/ (ninguna carpeta con main.tex)." -ForegroundColor Yellow
        exit 0
    }
    foreach ($docId in $ids) {
        Write-Host "=== $docId ===" -ForegroundColor Cyan
        Build-Document -DocId $docId
    }
    exit 0
}

if (-not $Id) {
    throw "Indica -Id <carpeta> o -All. Ejemplo: -Id practica-01"
}

if ($Id -notin $ids) {
    if ($ids.Count -eq 0) {
        throw "documentos/ está vacío. Crea documentos/<nombre>/main.tex y vuelve a compilar."
    }
    throw "Carpeta desconocida: $Id. Disponibles: $($ids -join ', ')"
}

Build-Document -DocId $Id
