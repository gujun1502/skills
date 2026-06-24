#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_pdf.py —— Windows 友好的 Markdown → PDF（中文）

不依赖 weasyprint/GTK：用 python-markdown 渲染 HTML（内嵌微软雅黑/宋体 + A4 排版），
再调用系统自带的 Edge(Chromium) 或 Chrome 的 headless --print-to-pdf 生成 PDF。

用法：
  python md_to_pdf.py reports/NOW_2026-06-21.md
  python md_to_pdf.py in.md out.pdf
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import markdown  # pip install markdown

CSS = """
@page { size: A4; margin: 1.8cm 1.6cm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei","微软雅黑","SimSun",sans-serif;
       font-size: 11.5pt; line-height: 1.75; color: #1a1a1a; }
h1 { font-size: 20pt; color: #b91c1c; border-bottom: 3px solid #b91c1c;
     padding-bottom: 8px; margin: 0 0 14px; }
h2 { font-size: 15pt; color: #0f3d6b; border-left: 5px solid #0f3d6b;
     padding-left: 10px; margin: 22px 0 10px; }
h3 { font-size: 13pt; color: #0f3d6b; margin: 16px 0 8px; }
blockquote { background: #f4f6f8; border-left: 4px solid #94a3b8;
     margin: 10px 0; padding: 8px 14px; color: #475569; font-size: 10.5pt; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
th, td { border: 1px solid #cbd5e1; padding: 6px 9px; text-align: left;
     vertical-align: top; word-break: break-word; }
th { background: #0f3d6b; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f6f8fa; }
code { background: #eef2f5; padding: 1px 5px; border-radius: 3px;
     font-family: Consolas,monospace; font-size: 10pt; }
strong { color: #b91c1c; }
hr { border: none; border-top: 1px solid #d1d5db; margin: 18px 0; }
ul, ol { margin: 8px 0 8px 4px; padding-left: 22px; }
li { margin: 3px 0; }
a { color: #0f3d6b; text-decoration: none; }
"""

HTML_TMPL = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{css}</style></head><body>{body}</body></html>"""


def find_browser() -> str | None:
    cands = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in cands:
        if Path(c).exists():
            return c
    return None


def convert(md_path: str, out_path: str | None = None) -> str:
    md_file = Path(md_path)
    text = md_file.read_text(encoding="utf-8")
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    html = HTML_TMPL.format(css=CSS, body=body)

    out = (Path(out_path) if out_path else md_file.with_suffix(".pdf")).resolve()
    tmp_html = Path(tempfile.gettempdir()) / (md_file.stem + "_render.html")
    tmp_html.write_text(html, encoding="utf-8")

    browser = find_browser()
    if not browser:
        raise RuntimeError("未找到 Edge/Chrome，无法生成 PDF")
    user_dir = Path(tempfile.gettempdir()) / "mdpdf_profile"
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-first-run", "--no-pdf-header-footer",
           f"--user-data-dir={user_dir}",
           f"--print-to-pdf={out}", tmp_html.as_uri()]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if not out.exists():
        raise RuntimeError(f"PDF 生成失败：{r.stderr.decode('utf-8','ignore')[:300]}")
    return str(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python md_to_pdf.py input.md [output.pdf]")
        sys.exit(1)
    out = convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("PDF:", out)
