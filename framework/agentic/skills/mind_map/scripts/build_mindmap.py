"""mind-map engine: outline / JSON -> SVG, HTML, PNG, PDF, Markdown, Mermaid.

    python scripts/build_mindmap.py map.md -o map.svg                 # SVG (no browser needed)
    python scripts/build_mindmap.py map.md -o map.png --also svg,md   # PNG needs Edge/Chrome/Chromium
    python scripts/build_mindmap.py map.json -o map.html              # interactive page (pan / zoom / save PNG)
    python scripts/build_mindmap.py - -o map.svg < outline.txt

Input: an indented outline (Markdown headings / bullets), a Mermaid mindmap, or
JSON {"root": "...", "nodes": [...]}.  See SKILL.md.

Python:
    from build_mindmap import build_mindmap, format_result
    res = build_mindmap(text, "map.svg", theme="rainbow")     # never raises
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outline_parser import parse_mindmap, to_mermaid, to_outline  # noqa: E402
from render_svg import THEMES, render, stats  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR_ENV = "PPTX_OUTPUT_DIR"
BROWSER_ENV = "POSTER_BROWSER"
FORMATS = ("svg", "html", "png", "pdf", "md", "mmd", "json")


def _result(ok, **kw):
    d = {"ok": ok}
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
# HTML wrapper (interactive)
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="__LANG__"><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
html,body{margin:0;height:100%;background:__BG__;font-family:Poppins,'Segoe UI',Arial,sans-serif;overflow:hidden}
#stage{width:100%;height:100%;cursor:grab}
#stage svg{width:100%;height:100%}
#bar{position:fixed;left:12px;top:12px;display:flex;gap:6px;z-index:2}
#bar button{border:1px solid #cbd5e1;background:#fff;border-radius:8px;padding:6px 10px;font-size:13px;cursor:pointer}
#bar button:hover{background:#f1f5f9}
@media print{#bar{display:none}}
</style></head><body>
<div id="bar"><button onclick="zoomBy(1.2)">+</button><button onclick="zoomBy(1/1.2)">&minus;</button>
<button onclick="fit()">Fit</button><button onclick="savePng()">Save PNG</button></div>
<div id="stage">__SVG__</div>
<script>
var svg=document.querySelector('#stage svg');var vb=svg.getAttribute('viewBox').split(' ').map(Number);
var view={x:vb[0],y:vb[1],w:vb[2],h:vb[3]};var base=vb.slice();
function apply(){svg.setAttribute('viewBox',[view.x,view.y,view.w,view.h].join(' '));}
function fit(){view={x:base[0],y:base[1],w:base[2],h:base[3]};apply();}
function zoomBy(f,cx,cy){var r=svg.getBoundingClientRect();cx=cx===undefined?r.width/2:cx;cy=cy===undefined?r.height/2:cy;
  var px=view.x+cx/r.width*view.w,py=view.y+cy/r.height*view.h;view.w/=f;view.h/=f;view.x=px-cx/r.width*view.w;view.y=py-cy/r.height*view.h;apply();}
svg.addEventListener('wheel',function(e){e.preventDefault();var r=svg.getBoundingClientRect();zoomBy(e.deltaY<0?1.15:1/1.15,e.clientX-r.left,e.clientY-r.top);},{passive:false});
var drag=null;svg.addEventListener('mousedown',function(e){drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y};});
window.addEventListener('mousemove',function(e){if(!drag)return;var r=svg.getBoundingClientRect();view.x=drag.vx-(e.clientX-drag.x)*view.w/r.width;view.y=drag.vy-(e.clientY-drag.y)*view.h/r.height;apply();});
window.addEventListener('mouseup',function(){drag=null;});
svg.setAttribute('preserveAspectRatio','xMidYMid meet');
function savePng(){var s=new XMLSerializer().serializeToString(svg);var clone=svg.cloneNode(true);clone.setAttribute('viewBox',base.join(' '));
  clone.setAttribute('width',base[2]*2);clone.setAttribute('height',base[3]*2);s=new XMLSerializer().serializeToString(clone);
  var img=new Image();img.onload=function(){var c=document.createElement('canvas');c.width=base[2]*2;c.height=base[3]*2;
    c.getContext('2d').drawImage(img,0,0);var a=document.createElement('a');a.download='__FILE__.png';a.href=c.toDataURL('image/png');a.click();};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(s);}
</script></body></html>"""


def wrap_html(svg: str, title: str, bg: str, lang: str, name: str) -> str:
    return (_HTML.replace("__TITLE__", escape(title)).replace("__BG__", bg).replace("__LANG__", lang)
            .replace("__SVG__", svg).replace("__FILE__", escape(name)))


# ---------------------------------------------------------------------------
# Browser rendering (PNG / PDF)
# ---------------------------------------------------------------------------

def find_browser():
    env = os.environ.get(BROWSER_ENV)
    if env and Path(env).is_file():
        return env
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge", "microsoft-edge"):
        exe = shutil.which(name)
        if exe:
            return exe
    for c in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if Path(c).is_file():
            return c
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return "playwright"
    except ImportError:
        return None


def render_bitmap(svg: str, out: Path, kind: str, w: int, h: int, scale: int, warn) -> bool:
    """PNG: screenshot at `scale`x; PDF: one page the size of the map."""
    browser = find_browser()
    if not browser:
        try:
            import cairosvg  # optional pure-python fallback
            if kind == "png":
                cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out), scale=scale)
            else:
                cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=str(out))
            return True
        except ImportError:
            warn(f"no browser found for {kind.upper()} - the SVG was written instead; install Edge/Chrome, "
                 "`pip install cairosvg`, or set POSTER_BROWSER")
            return False
        except Exception as e:
            warn(f"cairosvg failed: {e}")
            return False
    page = (f"<!doctype html><html><head><meta charset='utf-8'><style>@page{{size:{w}px {h}px;margin:0}}"
            f"html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}svg{{display:block;width:{w}px;height:{h}px}}"
            f"</style></head><body>{svg}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "map.html"
        html_path.write_text(page, encoding="utf-8")
        try:
            if browser == "playwright":
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    b = p.chromium.launch()
                    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
                    pg.goto(html_path.as_uri())
                    pg.wait_for_timeout(300)
                    if kind == "png":
                        pg.screenshot(path=str(out))
                    else:
                        pg.pdf(path=str(out), width=f"{w}px", height=f"{h}px", print_background=True,
                               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                    b.close()
            else:
                args = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                        f"--user-data-dir={tmp}/profile", "--no-first-run", "--virtual-time-budget=2000"]
                if kind == "png":   # some builds lose ~100px of window height: over-size, then crop
                    args += [f"--screenshot={out}", f"--window-size={w + 40},{h + 140}", f"--force-device-scale-factor={scale}"]
                else:
                    args += ["--no-pdf-header-footer", f"--print-to-pdf={out}"]
                args.append(html_path.as_uri())
                r = subprocess.run(args, capture_output=True, text=True, timeout=180)
                if not out.is_file():
                    warn(f"browser did not write {out.name}: {(r.stderr or '')[-200:].strip()}")
                    return False
                if kind == "png":
                    try:
                        from PIL import Image
                        with Image.open(out) as im:
                            im.crop((0, 0, w * scale, h * scale)).save(out)
                    except Exception:
                        pass
            return out.is_file()
        except Exception as e:
            warn(f"{kind.upper()} rendering failed ({type(e).__name__}: {e}) - SVG written instead")
            return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_mindmap(source, filename: str = "mindmap.svg", output_dir=None, theme: str | None = None,
                  title: str | None = None, layout: str | None = None, font_scale: float | None = None,
                  also: list[str] | None = None, scale: int = 2) -> dict:
    """Build the map.  Returns {"ok", "path", "files", "stats", "warnings"} and never raises."""
    warnings: list[str] = []
    warn = lambda m: warnings.append(m) if m not in warnings else None  # noqa: E731
    try:
        root, meta, w = parse_mindmap(source)
    except ValueError as e:
        return _result(False, error=f"Could not read the mind map: {e}",
                       hint="Give an indented outline (# root, - branch, '  - leaf') or JSON {\"root\":..., \"nodes\":[...]}",
                       warnings=warnings)
    warnings += w
    theme = (theme or meta.get("theme") or "rainbow").lower()
    if theme not in THEMES:
        warn(f"theme {theme!r} unknown -> 'rainbow' (valid: {', '.join(THEMES)})")
        theme = "rainbow"
    layout = (layout or meta.get("layout") or "radial").lower()
    if layout not in ("radial", "right"):
        warn(f"layout {layout!r} unknown -> 'radial'")
        layout = "radial"
    title = title if title is not None else str(meta.get("title") or "")
    try:
        fs = float(font_scale if font_scale is not None else meta.get("font_scale") or 1.0)
    except (TypeError, ValueError):
        fs = 1.0
    fs = max(0.6, min(2.0, fs))
    lang = str(meta.get("language") or "en")[:2]

    name = str(filename or "mindmap.svg")
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in FORMATS:
        name, ext = name + ".svg", "svg"
    out = Path(name).expanduser()
    if not out.is_absolute():
        out = Path(output_dir or os.environ.get(OUTPUT_DIR_ENV) or (Path.cwd() / "output")) / out
    out = out.resolve()
    wanted = [ext] + [f.strip().lower() for f in (also or []) if f.strip().lower() in FORMATS and f.strip().lower() != ext]

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        svg = render(root, theme=theme, title=title, layout_mode=layout, font_scale=fs)
        w_px, h_px = (int(float(v)) for v in svg.split('width="')[1].split('"')[0:1] + svg.split('height="')[1].split('"')[0:1])
    except Exception as e:
        return _result(False, error=f"Rendering failed: {type(e).__name__}: {e}", hint="", warnings=warnings)

    files = {}
    for f in wanted:
        p = out.with_suffix("." + f)
        try:
            if f == "svg":
                p.write_text(svg, encoding="utf-8")
            elif f == "html":
                p.write_text(wrap_html(svg, title or root["text"], THEMES[theme]["bg"], lang, out.stem), encoding="utf-8")
            elif f == "md":
                p.write_text(to_outline(root), encoding="utf-8")
            elif f == "mmd":
                p.write_text(to_mermaid(root), encoding="utf-8")
            elif f == "json":
                p.write_text(json.dumps({"title": title, "theme": theme, "layout": layout, "root": root},
                                        ensure_ascii=False, indent=1), encoding="utf-8")
            elif f in ("png", "pdf"):
                if not render_bitmap(svg, p, f, w_px, h_px, scale, warn):
                    if "svg" not in files:
                        out.with_suffix(".svg").write_text(svg, encoding="utf-8")
                        files["svg"] = str(out.with_suffix(".svg"))
                    continue
            files[f] = str(p)
        except Exception as e:
            warn(f"could not write {f}: {e}")
    if not files:
        return _result(False, error="No file could be written.", hint="Check the output folder permissions.",
                       warnings=warnings)
    path = files.get(ext) or next(iter(files.values()))
    return _result(True, path=path, files=files, stats=stats(root), theme=theme, layout=layout,
                   size=[w_px, h_px], warnings=warnings)


def format_result(res: dict) -> str:
    if res.get("ok"):
        st = res["stats"]
        lines = [f"OK: created {res['path']} ({st['nodes']} nodes, {st['branches']} branches, depth {st['depth']}, "
                 f"{res['size'][0]}x{res['size'][1]} px, theme={res['theme']})"]
        lines += [f"{k.upper()}: {v}" for k, v in res["files"].items() if v != res["path"]]
    else:
        lines = [f"ERROR: {res.get('error')}"]
        if res.get("hint"):
            lines.append(f"HINT: {res['hint']}")
    ws = res.get("warnings") or []
    if ws:
        lines.append(f"AUTO-FIXED / WARNINGS ({len(ws)}):")
        lines += [f"- {w}" for w in ws[:12]]
        if len(ws) > 12:
            lines.append(f"- ... and {len(ws) - 12} more")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a mind map from an outline or JSON (see SKILL.md).")
    ap.add_argument("source", help="outline / JSON file, or '-' for stdin")
    ap.add_argument("-o", "--output", default="mindmap.svg", help=".svg .html .png .pdf .md .mmd .json")
    ap.add_argument("--also", default="", help="extra formats, comma separated (e.g. svg,md,mmd)")
    ap.add_argument("--theme", help="rainbow | blue | pastel | dark | mono")
    ap.add_argument("--layout", help="radial (two-sided, default) | right (tree to the right)")
    ap.add_argument("--title", help="small caption in the corner")
    ap.add_argument("--font-scale", type=float, help="0.6 - 2.0")
    ap.add_argument("--scale", type=int, default=2, help="PNG pixel density (default 2)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    if args.source == "-":
        raw = sys.stdin.read()
    else:
        p = Path(args.source)
        if not p.is_file():
            print(f"ERROR: file not found: {p}")
            return 2
        raw = p.read_text(encoding="utf-8-sig")
    out = Path(args.output)
    res = build_mindmap(raw, filename=str(out if out.is_absolute() else Path.cwd() / out), theme=args.theme,
                        title=args.title, layout=args.layout, font_scale=args.font_scale,
                        also=[x for x in args.also.split(",") if x], scale=args.scale)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_result(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
