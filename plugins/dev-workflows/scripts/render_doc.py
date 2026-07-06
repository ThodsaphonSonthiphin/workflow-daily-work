#!/usr/bin/env python3
"""render_doc.py — sa-doc renderer: Markdown -> self-contained HTML -> optional PDF.

Usage:
  python render_doc.py <input.md> [--pdf] [--out-dir DIR]
                       [--marked-js FILE] [--mermaid-js FILE]

The HTML renders the Markdown client-side (marked.js) and the Mermaid blocks
(mermaid.js). Default script sources are CDN; pass local files for offline use.
PDF uses headless Edge/Chrome with --virtual-time-budget so client-side
rendering finishes before printing. Missing browser degrades to HTML + advice,
never a failure.
"""
import argparse
import html
import json
import pathlib
import shutil
import subprocess
import sys

MARKED_CDN = "https://cdn.jsdelivr.net/npm/marked/marked.min.js"
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

WINDOWS_BROWSER_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

CSS = """
@page { size: A4; margin: 20mm 18mm; }
body { font-family: "Sarabun", "Leelawadee UI", Tahoma, sans-serif;
       font-size: 11pt; line-height: 1.6; max-width: 180mm; margin: 0 auto;
       color: #1a1a1a; }
h1 { page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h1, h2, h3 { line-height: 1.3; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; }
th, td { border: 1px solid #999; padding: 4px 8px; text-align: left;
         vertical-align: top; }
th { background: #f0f0f0; }
pre { background: #f6f6f6; padding: 8px; overflow-x: auto; }
.mermaid { display: flex; justify-content: center; margin: 1em 0;
           page-break-inside: avoid; }
"""


def _script_tag(inline_body, cdn_url):
    if inline_body is not None:
        return f"<script>{inline_body}</script>"
    return f'<script src="{cdn_url}"></script>'


def build_html(md_text, title, marked_js, mermaid_js):
    # json.dumps() does not escape "/", so a literal "</script>" inside md_text
    # would prematurely close this inline <script> block in the browser. Escaping
    # "</" to "<\/" is valid JS/JSON and parses back to the identical string.
    raw_json = json.dumps(md_text).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div id="content"></div>
{_script_tag(marked_js, MARKED_CDN)}
{_script_tag(mermaid_js, MERMAID_CDN)}
<script>
const raw = {raw_json};
document.getElementById("content").innerHTML = marked.parse(raw);
document.querySelectorAll("pre code.language-mermaid").forEach(code => {{
  const div = document.createElement("div");
  div.className = "mermaid";
  div.textContent = code.textContent;
  code.closest("pre").replaceWith(div);
}});
mermaid.initialize({{ startOnLoad: false, theme: "neutral" }});
mermaid.run();
</script>
</body>
</html>
"""


def find_browser():
    for name in ("msedge", "chrome", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    for path in WINDOWS_BROWSER_PATHS:
        if pathlib.Path(path).exists():
            return path
    return None


def print_pdf(browser, html_path, pdf_path):
    cmd = [browser, "--headless", "--disable-gpu",
           "--no-pdf-header-footer", "--virtual-time-budget=15000",
           f"--print-to-pdf={pdf_path}", pathlib.Path(html_path).resolve().as_uri()]
    subprocess.run(cmd, check=True, capture_output=True)


def _read_optional(path):
    if path is None:
        return None
    return pathlib.Path(path).read_text(encoding="utf-8")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--marked-js", default=None)
    ap.add_argument("--mermaid-js", default=None)
    args = ap.parse_args(argv)

    src = pathlib.Path(args.input)
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    md_text = src.read_text(encoding="utf-8")
    title = src.stem
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    html_path = out_dir / f"{src.stem}.html"
    html_path.write_text(
        build_html(md_text, title,
                   _read_optional(args.marked_js),
                   _read_optional(args.mermaid_js)),
        encoding="utf-8")
    print(f"HTML: {html_path}")

    if args.pdf:
        browser = find_browser()
        if browser is None:
            print("No Edge/Chrome/Chromium found - open the HTML in a browser "
                  "and print to PDF (Ctrl+P).")
        else:
            pdf_path = out_dir / f"{src.stem}.pdf"
            try:
                print_pdf(browser, html_path, pdf_path)
                print(f"PDF:  {pdf_path}")
            except (subprocess.CalledProcessError, OSError) as exc:
                print(f"PDF generation failed ({exc}) - the HTML is ready at "
                      f"{html_path}; open it in a browser and print to PDF "
                      "manually (Ctrl+P).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
