"""Convierte un Markdown a HTML con estilos de impresion y luego a PDF via Chrome headless.

Uso:
    python scripts/md2pdf.py docs/CASOS_DE_USO.md docs/CASOS_DE_USO.pdf
"""

import html
import pathlib
import re
import subprocess
import sys

import markdown

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 14mm 16mm 14mm; }
:root { --ink:#1a1a1a; --muted:#5b5b5b; --line:#d8d2c7; --accent:#8a5a2b; --soft:#faf7f2; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Calibri", system-ui, sans-serif;
  color: var(--ink); font-size: 9.6pt; line-height: 1.45; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 19pt; color: var(--accent); border-bottom: 2.5px solid var(--accent);
     padding-bottom: 5px; margin: 0 0 4pt; letter-spacing: -0.2pt; }
h1 + p { margin-top: 2pt; }
h2 { font-size: 13.5pt; color: var(--accent); margin: 16pt 0 5pt; padding-bottom: 2pt;
     border-bottom: 1px solid var(--line); page-break-after: avoid; }
h3 { font-size: 11.2pt; margin: 12pt 0 4pt; color: #2f2f2f; page-break-after: avoid; }
h4 { font-size: 10pt; margin: 9pt 0 3pt; color: #3a3a3a; page-break-after: avoid; }
p { margin: 0 0 5pt; orphans: 2; widows: 2; }
ul, ol { margin: 0 0 6pt; padding-left: 16pt; }
li { margin-bottom: 2pt; }
strong { color: #000; }
a { color: var(--accent); text-decoration: none; }
code {
  font-family: "Cascadia Mono", Consolas, monospace; font-size: 8.4pt;
  background: var(--soft); border: 1px solid var(--line); border-radius: 3px;
  padding: 0 3px; word-break: break-word;
}
pre {
  background: var(--soft); border: 1px solid var(--line); border-left: 3px solid var(--accent);
  border-radius: 3px; padding: 7pt 9pt; overflow: visible; page-break-inside: avoid;
  white-space: pre-wrap; word-break: break-word;
}
pre code { background: none; border: none; padding: 0; font-size: 8.2pt; line-height: 1.35; }
table {
  width: 100%; border-collapse: collapse; margin: 6pt 0 9pt; font-size: 8.6pt;
  page-break-inside: avoid;
}
thead { display: table-header-group; }
th {
  background: var(--accent); color: #fff; text-align: left; font-weight: 600;
  padding: 4pt 5pt; border: 1px solid var(--accent); font-size: 8.6pt;
}
td { padding: 3.5pt 5pt; border: 1px solid var(--line); vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f4ef; }
blockquote {
  margin: 6pt 0; padding: 6pt 9pt; background: var(--soft);
  border-left: 3px solid var(--accent); color: #333;
}
blockquote p:last-child { margin-bottom: 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 12pt 0; }
input[type=checkbox] { margin-right: 5px; }
li:has(> input[type=checkbox]) { list-style: none; margin-left: -12pt; }
.doc-header { border-bottom: 3px solid var(--accent); margin-bottom: 10pt; padding-bottom: 8pt; }
.doc-footer { margin-top: 14pt; padding-top: 6pt; border-top: 1px solid var(--line);
              font-size: 8pt; color: var(--muted); text-align: center; }
table:first-of-type { page-break-inside: avoid; }
h2 + table, h3 + table { page-break-before: auto; }
"""


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if pathlib.Path(path).exists():
            return path
    raise SystemExit("No se encontro Chrome ni Edge para generar el PDF.")


def build_html(md_text: str, title: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    return (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"{body}"
        "<div class='doc-footer'>Donata IA · Especificacion de Casos de Uso Funcionales · "
        "Trabajo Practico Integrador · Desarrollo y Arquitectura de Agentes de IA</div>"
        "</body></html>"
    )


def to_pdf(html_path: pathlib.Path, pdf_path: pathlib.Path) -> None:
    chrome = find_chrome()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src = pathlib.Path(sys.argv[1]).resolve()
    dst = pathlib.Path(sys.argv[2]).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".html")
    tmp.write_text(build_html(src.read_text(encoding="utf-8"), src.stem), encoding="utf-8")
    to_pdf(tmp, dst)
    tmp.unlink(missing_ok=True)
    size_kb = dst.stat().st_size / 1024
    print(f"PDF generado: {dst} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
