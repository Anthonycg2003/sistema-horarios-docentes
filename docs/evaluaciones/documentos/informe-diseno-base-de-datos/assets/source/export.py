# -*- coding: utf-8 -*-
"""Exporta las figuras de diagrams.py a PDF vectorial en ../export/.

Cada figura se imprime con un navegador Chromium (Chrome o Edge) en una
página del tamaño exacto de su SVG, para conservar la fuente Segoe UI.

Uso:
    python export.py              # todas las figuras
    python export.py isa valida   # solo esas (nombre sin el prefijo fig-)

La ruta del navegador se puede forzar con la variable de entorno CHROME.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from diagrams import FIGURES

SOURCE = Path(__file__).resolve().parent
EXPORT = SOURCE.parent / "export"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("No se encontró Chrome ni Edge. Indica la ruta con la variable CHROME.")


def page_html(svg):
    width, height = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups()
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        f"@page{{size:{width}px {height}px;margin:0}}"
        "html,body{margin:0}"
        f"svg{{display:block;width:{width}px;height:{height}px}}"
        f"</style></head><body>{svg}</body></html>"
    )


def print_pdf(browser, html_path, pdf_path):
    pdf_path.unlink(missing_ok=True)
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=False,
        capture_output=True,
    )
    # Chrome en Windows puede volver antes de terminar de escribir el archivo
    for _ in range(50):
        if pdf_path.exists() and pdf_path.stat().st_size > 1000:
            time.sleep(0.3)
            return
        time.sleep(0.2)
    raise SystemExit(f"No se escribió el PDF: {pdf_path}")


def main(names):
    browser = find_browser()
    EXPORT.mkdir(exist_ok=True)
    known = {fid.removeprefix("fig-") for fid, _, _ in FIGURES}
    unknown = set(names) - known
    if unknown:
        raise SystemExit(f"Figuras desconocidas: {', '.join(sorted(unknown))}. Disponibles: {', '.join(sorted(known))}")
    with tempfile.TemporaryDirectory() as tmp:
        for fid, _, draw in FIGURES:
            name = fid.removeprefix("fig-")
            if names and name not in names:
                continue
            html_path = Path(tmp) / f"{name}.html"
            html_path.write_text(page_html(draw()), encoding="utf-8")
            pdf_path = EXPORT / f"{name}.pdf"
            print_pdf(browser, html_path, pdf_path)
            print(f"{pdf_path.relative_to(SOURCE.parent.parent)}")


if __name__ == "__main__":
    main(sys.argv[1:])
