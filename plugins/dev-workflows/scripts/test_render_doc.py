#!/usr/bin/env python3
"""Tests for render_doc.py. Run: python test_render_doc.py"""
import json
import os
import sys
import tempfile

from render_doc import build_html, find_browser, main

MD = """# ตัวอย่าง

```mermaid
flowchart TD
    A["เริ่ม"] --> B["จบ"]
```

ข้อความไทยพร้อม **ตัวหนา**
"""


def test_build_html_embeds_markdown_as_json():
    html = build_html(MD, "ตัวอย่าง", None, None)
    assert json.dumps(MD) in html          # md embedded as a JS string
    assert "cdn.jsdelivr.net/npm/marked" in html
    assert "cdn.jsdelivr.net/npm/mermaid" in html
    assert "Sarabun" in html               # Thai-capable font stack
    assert "<title>ตัวอย่าง</title>" in html


def test_build_html_offline_inlines_scripts():
    html = build_html(MD, "t", "/*MARKED*/", "/*MERMAID*/")
    assert "/*MARKED*/" in html and "/*MERMAID*/" in html
    assert "cdn.jsdelivr.net" not in html


def test_cli_writes_html():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "doc.md")
        with open(src, "w", encoding="utf-8") as f:
            f.write(MD)
        rc = main([src, "--out-dir", d])
        assert rc == 0
        assert os.path.exists(os.path.join(d, "doc.html"))


def test_find_browser_returns_path_or_none():
    b = find_browser()
    assert b is None or os.path.exists(b)


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
