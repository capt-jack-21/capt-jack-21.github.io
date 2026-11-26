#!/usr/bin/env python3
"""Static blog generator for capt-jack-21.github.io.

Reads blog-src/posts/*.md (simple front matter + Markdown) and writes
blog/index.html, blog/<theme>/index.html, blog/posts/<slug>/index.html and
blog/og/<slug>.png (share cards). Run from anywhere:  python3 blog-src/build.py
"""
import html
import re
import shutil
import sys
from pathlib import Path

import markdown
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "blog-src" / "posts"
OUT = ROOT / "blog"
SITE = "https://capt-jack-21.github.io"

# ---- the one place to change the blog's own accent colour -------------------
BLOG_ACCENT = "#ffd400"   # the blog is all yellow; change here to recolour everything
# -----------------------------------------------------------------------------

THEMES = {
    "iiot": dict(name="IIoT", color=BLOG_ACCENT,
                 blurb="Protocols, time-series and data platforms, digital twins and edge gateways."),
    "ai": dict(name="Agentic AI", color=BLOG_ACCENT,
               blurb="Agents on operational data: tool design, grounding, guardrails and evals."),
    "robotics": dict(name="Robotics / Embedded", color=BLOG_ACCENT,
                     blurb="ROS2, ESP32 and firmware: lab notes from the bench."),
    "web3": dict(name="Web3 / Blockchain", color=BLOG_ACCENT,
                 blurb="Crypto and blockchain seen through an architect's eyes."),
}
TYPES = {
    "problem": "Problem solved",
    "decision": "Decision record",
    "teardown": "Teardown",
    "lab": "Lab notes",
    "opinion": "Opinion",
}

Y = "#ffde00"      # sticker yellow
K = "#0a0a0a"      # ink
PAPER = "#e7e7e7"  # light grid paper

CSS = """
:root{--y:#ffde00;--k:#0a0a0a;--w:#fff;--paper:#e7e7e7;--mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,"Liberation Mono",monospace;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--disp:"Anton","Bebas Neue",Impact,"Arial Narrow Bold","Haettenschweiler",sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:linear-gradient(rgba(0,0,0,.055) 1px,transparent 1px) 0 0/32px 32px,linear-gradient(90deg,rgba(0,0,0,.055) 1px,transparent 1px) 0 0/32px 32px,var(--paper);color:var(--k);font-family:var(--sans);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
.d{font-family:var(--disp);text-transform:uppercase;font-weight:400;letter-spacing:.015em;line-height:1.02}
/* top strip */
.strip{background:var(--y);border-bottom:2px solid var(--k);font-family:var(--mono);font-size:12px;letter-spacing:.06em}
.strip .wrap{display:flex;align-items:center;gap:0;height:40px;overflow:hidden}
.strip b{background:var(--k);color:var(--y);font-family:var(--disp);font-weight:400;font-size:20px;letter-spacing:.04em;padding:0 16px;height:100%;display:flex;align-items:center;margin-left:-20px;margin-right:16px}
.strip a{white-space:nowrap;padding:0 14px 0 0;display:inline-flex;align-items:center;gap:8px;text-transform:uppercase}
.strip a:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--k)}
.strip a:hover{text-decoration:underline}
/* header box */
.top{margin:16px auto 0;background:var(--w);border:2px solid var(--k);border-radius:18px;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 18px}
.logo{display:flex;align-items:center;gap:10px}
.logo i{font-style:normal;display:grid;place-items:center;width:40px;height:40px;background:var(--k);color:var(--y);font-family:var(--disp);font-size:22px;border-radius:9px;letter-spacing:.02em}
.logo span{font-family:var(--disp);font-size:34px;letter-spacing:.02em;text-transform:uppercase;line-height:1}
.logo span em{font-style:normal;color:var(--k);background:var(--y);padding:0 6px;margin-left:4px;border-radius:5px}
.top ul{display:flex;gap:22px;list-style:none;font-family:var(--disp);font-size:20px;text-transform:uppercase;letter-spacing:.03em}
.top ul a{display:inline-flex;align-items:center;gap:8px}
.top ul a:before{content:"";width:11px;height:11px;border-radius:50%;border:2px solid var(--k)}
.top ul a.on:before,.top ul a:hover:before{background:var(--y)}
.top ul a.on{text-decoration:underline;text-underline-offset:5px}
/* hero */
.hero{padding:46px 0 10px}
.kick{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;display:flex;align-items:center;gap:10px}
.kick i{width:10px;height:10px;border-radius:50%;background:var(--y);border:2px solid var(--k)}
.hero h1{font-size:clamp(64px,13vw,150px);margin:10px 0 6px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.wave{width:clamp(90px,14vw,190px);height:auto;color:var(--k)}
.sticker{display:inline-block;background:var(--y);border:2px solid var(--k);border-radius:10px;padding:6px 14px;font-family:var(--disp);font-size:22px;text-transform:uppercase;letter-spacing:.04em;transform:rotate(-4deg);box-shadow:4px 4px 0 var(--k)}
.lede{max-width:640px;font-size:17px;color:#222;margin-top:6px}
/* theme cards */
.themes{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:34px 0 0}
.tcard{position:relative;display:flex;flex-direction:column;border:2px solid var(--k);border-radius:18px;padding:18px;min-height:230px;transition:transform .15s,box-shadow .15s;box-shadow:0 0 0 var(--k)}
.tcard:hover{transform:translate(-3px,-3px);box-shadow:6px 6px 0 var(--k)}
.tcard h3{font-size:34px;margin-bottom:8px}
.tcard p{font-size:14px;max-width:30ch}
.tcard .ic{width:84px;height:54px;margin-bottom:12px}
.tcard .cnt{margin-top:auto;display:flex;align-items:center;justify-content:space-between;font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;border-top:2px solid currentColor;padding-top:10px}
.t-y{background:var(--y);color:var(--k)}.t-w{background:var(--w);color:var(--k)}.t-k{background:var(--k);color:var(--y)}.t-k p{color:#e8e8e8}
/* bar */
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:44px 0 22px}
.chip{font-family:var(--disp);font-size:17px;letter-spacing:.04em;text-transform:uppercase;padding:6px 14px;border-radius:999px;border:2px solid var(--k);background:var(--w);color:var(--k);cursor:pointer;transition:background .12s}
.chip:hover{background:#fff6b0}.chip.on{background:var(--y)}
.sep{width:2px;height:26px;background:var(--k);margin:0 4px}
.search{margin-left:auto;font-family:var(--mono);font-size:13px;background:var(--w);border:2px solid var(--k);border-radius:999px;color:var(--k);padding:8px 16px;min-width:200px}
.search:focus{outline:none;box-shadow:0 0 0 3px var(--y)}
.sh{display:flex;align-items:center;gap:14px;margin:0 0 18px}
.sh h2{font-size:clamp(38px,6vw,60px)}
.sh svg{width:70px;height:20px}
/* post cards */
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:18px;margin-bottom:70px}
.post{display:flex;flex-direction:column;border:2px solid var(--k);border-radius:18px;padding:14px;background:var(--w);transition:transform .15s,box-shadow .15s}
.post:hover{transform:translate(-3px,-3px);box-shadow:6px 6px 0 var(--k)}
.cov{position:relative;border:2px solid var(--k);border-radius:12px;background:var(--y);overflow:hidden;aspect-ratio:16/9;display:grid;place-items:center;color:var(--k)}
.cov svg{width:78%;height:auto}
.cov:after{content:"";position:absolute;left:0;right:0;bottom:0;height:12px;border-top:2px solid var(--k);background:repeating-linear-gradient(90deg,var(--k) 0 2px,transparent 2px 10px);opacity:.9}
.txt{display:flex;flex-direction:column;flex:1;padding:14px 4px 2px}
.tags{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase}
.tg{background:var(--k);color:var(--y);padding:2px 9px;border-radius:999px;font-weight:700}
.post h3{font-size:30px;margin:12px 0 8px}
.post p{font-size:14px;color:#333;margin-bottom:14px}
.mr{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-family:var(--disp);font-size:16px;letter-spacing:.04em;text-transform:uppercase;border-top:2px solid var(--k);border-bottom:2px solid var(--k);padding:6px 0;margin-bottom:14px}
.btn{display:flex;align-items:center;justify-content:flex-end}
.btn b{font-family:var(--disp);font-weight:400;font-size:19px;letter-spacing:.04em;text-transform:uppercase;border:2px solid var(--k);border-radius:999px;padding:5px 20px;background:var(--w);color:var(--k);margin-right:-12px;z-index:1}
.btn s{display:grid;place-items:center;width:42px;height:42px;border:2px solid var(--k);border-radius:50%;background:var(--y);color:var(--k);text-decoration:none;font-size:20px;line-height:1;transform:rotate(-45deg);transition:transform .2s}
.post:hover .btn s{transform:rotate(0)}
.v-y{background:var(--y)}.v-y .cov{background:var(--w)}.v-y p{color:#222}
.v-k{background:var(--k);color:var(--w)}.v-k .mr{border-color:var(--y);color:var(--y)}.v-k h3{color:var(--y)}.v-k p{color:#ddd}.v-k .tg{background:var(--y);color:var(--k)}.v-k .btn b{background:var(--k);color:var(--y);border-color:var(--y)}.v-k .btn s{border-color:var(--y)}
.v-k:hover{box-shadow:6px 6px 0 var(--y)}
.v-f{grid-column:1/-1;flex-direction:row;gap:20px;background:var(--y)}
.v-f .cov{flex:0 0 42%;aspect-ratio:auto;min-height:230px;background:var(--w)}
.v-f .txt{padding:8px 8px 4px 0}.v-f h3{font-size:clamp(36px,5vw,56px)}
@media(max-width:760px){.v-f{flex-direction:column}.v-f .cov{flex:none;aspect-ratio:16/9;min-height:0}.v-f .txt{padding:14px 4px 2px}}
.ph{display:inline-block;font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;padding:2px 8px;border:2px solid var(--k);border-radius:4px;color:var(--k);background:repeating-linear-gradient(-45deg,var(--y) 0 6px,var(--w) 6px 12px);font-weight:700}
.v-k .ph{border-color:var(--y)}
.empty{font-family:var(--mono);font-size:14px;padding:20px 0;display:none}
/* article */
.art{max-width:800px;margin:34px auto 0;background:var(--w);border:2px solid var(--k);border-radius:20px;padding:34px 34px 26px;box-shadow:8px 8px 0 var(--k)}
.crumb{font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:16px}
.crumb a{text-decoration:underline;text-underline-offset:3px}
.art h1{font-size:clamp(40px,7vw,72px);margin:14px 0 12px}
.byline{font-family:var(--disp);font-size:16px;letter-spacing:.05em;text-transform:uppercase;border-top:2px solid var(--k);border-bottom:2px solid var(--k);padding:6px 0;margin:16px 0}
.banner{margin:22px 0;padding:26px 14px 12px;border:2px solid var(--k);border-radius:10px;font-family:var(--mono);font-size:12.5px;font-weight:700;background:repeating-linear-gradient(-45deg,var(--y) 0 14px,var(--k) 14px 28px) top/100% 12px no-repeat,var(--w)}
.banner span{background:var(--y);border:2px solid var(--k);padding:2px 8px;display:inline-block;border-radius:5px;margin-right:6px}
.body{font-size:17px}
.body h2{font-family:var(--disp);font-weight:400;font-size:34px;text-transform:uppercase;letter-spacing:.02em;margin:34px 0 12px;display:inline-block;background:var(--y);padding:2px 12px;border:2px solid var(--k);border-radius:8px;line-height:1.15}
.body p,.body ul,.body ol,.body table{margin:12px 0}
.body ul,.body ol{padding-left:22px}.body li{margin:5px 0}
.body em{color:#444}
.body code{font-family:var(--mono);font-size:.9em;background:#f1f1f1;border:2px solid var(--k);border-radius:5px;padding:0 5px}
.body pre{background:var(--k);color:var(--y);border-radius:12px;padding:16px;overflow:auto;margin:14px 0;border:2px solid var(--k)}
.body pre code{background:none;border:0;color:inherit;padding:0}
.body blockquote{border-left:6px solid var(--y);background:#fafafa;padding:8px 16px;margin:14px 0}
.body table{border-collapse:separate;border-spacing:0;width:100%;font-size:15px;border:2px solid var(--k);border-radius:10px;overflow:hidden}
.body th,.body td{border-bottom:2px solid var(--k);border-right:2px solid var(--k);padding:8px 12px;text-align:left}
.body th:last-child,.body td:last-child{border-right:0}.body tr:last-child td{border-bottom:0}
.body th{background:var(--y);font-family:var(--disp);font-weight:400;font-size:18px;letter-spacing:.04em;text-transform:uppercase}
.diagram{margin:22px 0;border:2px solid var(--k);border-radius:12px;padding:14px 14px 10px;background:#fafafa}
.diagram figcaption{font-family:var(--mono);font-size:12px;letter-spacing:.04em;margin-top:8px;color:#333}
.more{max-width:800px;margin:44px auto 70px}
.more .sh h2{font-size:44px}
.more .list{grid-template-columns:repeat(auto-fill,minmax(260px,1fr));margin-bottom:0}
.more .v-f{grid-column:auto;flex-direction:column}.more .v-f .cov{flex:none;aspect-ratio:16/9;min-height:0}.more .v-f .txt{padding:14px 4px 2px}.more .v-f h3{font-size:30px}
/* footer */
footer{background:var(--k);color:var(--y);border-top:2px solid var(--k);padding:26px 0 34px;font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase}
footer .wrap{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
footer a:hover{text-decoration:underline}
@media(max-width:720px){.top ul li.hide{display:none}.top ul{gap:14px;font-size:18px}.logo span{font-size:28px}.search{margin-left:0;width:100%}.sep{display:none}.art{padding:22px 18px;box-shadow:5px 5px 0 var(--k)}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

# ---------- original telemetry-flavoured motifs (all drawn here) ----------
SW = 'fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"'
MOTIFS = {
    # sensors -> gateway -> database
    "iiot": f'<svg viewBox="0 0 400 220" aria-hidden="true"><g {SW}><rect x="18" y="26" width="46" height="34"/><rect x="18" y="93" width="46" height="34"/><rect x="18" y="160" width="46" height="34"/>'
            f'<path d="M64 43H120L170 110M64 110H170M64 177H120L170 110"/><path d="M170 82L214 110L170 138L126 110Z" transform="translate(44 0)"/>'
            f'<path d="M258 110H292"/><ellipse cx="332" cy="60" rx="42" ry="14"/><path d="M290 60V160C290 176 374 176 374 160V60"/><path d="M290 110C290 126 374 126 374 110"/></g></svg>',
    # agent node graph
    "ai": f'<svg viewBox="0 0 400 220" aria-hidden="true"><g {SW}><circle cx="200" cy="110" r="34"/><circle cx="200" cy="110" r="8" fill="currentColor"/>'
          f'<path d="M172 90L110 50M228 90L290 50M168 120L90 150M232 120L310 150M200 144V190"/>'
          f'<circle cx="96" cy="42" r="16"/><rect x="274" y="28" width="34" height="34"/><circle cx="78" cy="156" r="16"/><rect x="298" y="134" width="34" height="34"/><circle cx="200" cy="198" r="14"/></g></svg>',
    # robot arm
    "robotics": f'<svg viewBox="0 0 400 220" aria-hidden="true"><g {SW}><path d="M60 196H200M110 196V168H170V196"/><circle cx="140" cy="150" r="18"/><path d="M140 132L108 74"/><circle cx="108" cy="66" r="16"/>'
                f'<path d="M122 56L226 32"/><circle cx="240" cy="30" r="14"/><path d="M250 38L300 86M300 86L282 118M300 86L330 108"/><path d="M290 170H350M320 170V196" /></g></svg>',
    # chained blocks
    "web3": f'<svg viewBox="0 0 400 220" aria-hidden="true"><g {SW}><rect x="14" y="70" width="100" height="80" rx="10"/><rect x="150" y="70" width="100" height="80" rx="10"/><rect x="286" y="70" width="100" height="80" rx="10"/>'
            f'<path d="M114 110H150M250 110H286"/><path d="M34 96H94M34 124H72M170 96H230M170 124H208M306 96H366M306 124H344"/></g></svg>',
}
WAVE = ('<svg class="wave" viewBox="0 0 200 60" aria-hidden="true"><path d="M2 30H40L52 8L70 52L84 18L96 40L106 30H198" fill="none" '
        'stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
SQUIG = ('<svg viewBox="0 0 70 20" aria-hidden="true"><path d="M2 10C10 -2 16 22 24 10S38 -2 46 10S60 22 68 10" fill="none" '
         'stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></svg>')
ICONS = {k: v.replace('<svg viewBox="0 0 400 220"', '<svg class="ic" viewBox="0 0 400 220"') for k, v in MOTIFS.items()}


def esc(s):
    return html.escape(s, quote=True)


def head(title, desc, url, image, body_cls=""):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="AV Connected · Blog">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{image}">
<meta name="theme-color" content="#ffde00">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23ffde00' stroke='%230a0a0a' stroke-width='4'/%3E%3Cpath d='M14 48 28 16l8 18M32 16l16 32' fill='none' stroke='%230a0a0a' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>"""


def strip():
    links = "".join(f'<a href="/blog/{k}/">{v["name"]}</a>' for k, v in THEMES.items())
    return f'<div class="strip"><div class="wrap"><b>Log</b>{links}</div></div>'


def nav():
    return ('<div class="wrap"><nav class="top"><a class="logo" href="/blog/"><i>AV</i><span>Blog</span></a>'
            '<ul><li class="hide"><a href="/#cases">Case studies</a></li><li class="hide"><a href="/#projects">Projects</a></li>'
            '<li><a href="/blog/" class="on">Blog</a></li><li><a href="/">Portfolio</a></li></ul></nav></div>')


FOOT = """<footer><div class="wrap"><span>Adithya Venkatesh · AV Connected · Sense • Connect • Solve</span>
<span><a href="/">Portfolio</a> · <a href="/blog/">Blog</a> · <a href="https://github.com/capt-jack-21" rel="noopener">GitHub</a></span></div></footer>"""

VARIANTS = ["v-f", "", "v-k", "", "v-y", "v-k", "", "v-y"]


def card(p, i=0, feature=True):
    v = VARIANTS[i % len(VARIANTS)]
    if v == "v-f" and not feature:
        v = "v-y"
    ph = '<span class="ph">PLACEHOLDER</span>' if p["placeholder"] else ""
    return (f'<a class="post {v}" href="/blog/posts/{p["slug"]}/" data-theme="{p["theme"]}" data-type="{p["type"]}" '
            f'data-q="{esc((p["title"] + " " + p["summary"] + " " + " ".join(p["tags"])).lower())}">'
            f'<div class="cov">{MOTIFS[p["theme"]]}</div><div class="txt">'
            f'<div class="tags"><span class="tg">{THEMES[p["theme"]]["name"]}</span><span>{TYPES[p["type"]]}</span>{ph}</div>'
            f'<h3 class="d">{esc(p["title"])}</h3><p>{esc(p["summary"])}</p>'
            f'<div class="mr"><span>{p["date_h"]}</span><span>{p["mins"]} min read</span></div>'
            f'<div class="btn"><b>Read post</b><s>↑</s></div></div></a>')


def index_page(posts, preset=None):
    if preset:
        t = THEMES[preset]
        title = f"{t['name']} · Blog · Adithya Venkatesh"
        desc = t["blurb"]
        url = f"{SITE}/blog/{preset}/"
    else:
        title = "Blog · Adithya Venkatesh · AV Connected"
        desc = "Problems solved, decisions and lab notes across IIoT, agentic AI, robotics and embedded, and Web3."
        url = f"{SITE}/blog/"
    h = head(title, desc, url, f"{SITE}/blog/og/_index.png") + strip() + nav()
    big = esc(THEMES[preset]["name"]) if preset else "Blog"
    sub = (THEMES[preset]["blurb"] if preset else
           "Problems I have solved, decisions I have made and things I build on the bench. Four themes, written plainly.")
    h += f'<header class="hero"><div class="wrap"><div class="kick"><i></i> Notes from the field</div><h1 class="d">{big}{WAVE}<span class="sticker">4 themes</span></h1><p class="lede">{esc(sub)}</p>'
    cards = ""
    for n, (key, t) in enumerate(THEMES.items()):
        cnt = sum(1 for p in posts if p["theme"] == key)
        cls = ["t-y", "t-k", "t-w", "t-y"][n]
        cards += (f'<a class="tcard {cls}" href="/blog/{key}/">{ICONS[key]}<h3 class="d">{t["name"]}</h3><p>{esc(t["blurb"])}</p>'
                  f'<div class="cnt"><span>{cnt} post{"s" if cnt != 1 else ""}</span><span>Open →</span></div></a>')
    h += f'<div class="themes">{cards}</div></div></header><main class="wrap">'
    tchips = '<button class="chip on" data-t="">All themes</button>' + "".join(
        f'<button class="chip" data-t="{k}">{v["name"]}</button>' for k, v in THEMES.items())
    ychips = '<button class="chip on" data-y="">All types</button>' + "".join(
        f'<button class="chip" data-y="{k}">{v}</button>' for k, v in TYPES.items())
    h += f'<div class="bar">{tchips}<span class="sep"></span>{ychips}<input class="search" id="q" type="search" placeholder="search posts" aria-label="Search posts"></div>'
    h += f'<div class="sh"><h2 class="d">Latest posts</h2>{SQUIG}</div>'
    h += '<div class="list" id="list">' + "".join(card(p, i) for i, p in enumerate(posts)) + '</div><p class="empty" id="none">No posts match yet.</p></main>'
    h += FOOT
    h += """<script>
(function(){var T=%s,Y="",Q="";var cs=[].slice.call(document.querySelectorAll('.chip'));
function run(){var n=0;[].forEach.call(document.querySelectorAll('.post'),function(p){
var ok=(!T||p.dataset.theme===T)&&(!Y||p.dataset.type===Y)&&(!Q||p.dataset.q.indexOf(Q)>-1);p.style.display=ok?'':'none';if(ok)n++});
document.getElementById('none').style.display=n?'none':'block';
cs.forEach(function(c){if(c.dataset.t!==undefined)c.classList.toggle('on',c.dataset.t===T);if(c.dataset.y!==undefined)c.classList.toggle('on',c.dataset.y===Y)})}
cs.forEach(function(c){c.addEventListener('click',function(){if(c.dataset.t!==undefined)T=c.dataset.t;else Y=c.dataset.y;run()})});
document.getElementById('q').addEventListener('input',function(e){Q=e.target.value.toLowerCase().trim();run()});run()})();
</script></body></html>""" % (f'"{preset}"' if preset else '""')
    return h


def post_page(p, posts):
    t = THEMES[p["theme"]]
    url = f"{SITE}/blog/posts/{p['slug']}/"
    h = head(f"{p['title']} · Adithya Venkatesh", p["summary"], url, f"{SITE}/blog/og/{p['slug']}.png") + strip() + nav()
    ban = ('<div class="banner"><span>PLACEHOLDER</span> This is an outline with the structure of the final post. '
           'The real write-up will replace it.</div>') if p["placeholder"] else ""
    tags = "".join(f'<span>#{esc(x)}</span>' for x in p["tags"])
    h += (f'<div class="wrap"><article class="art"><div class="crumb"><a href="/blog/">Blog</a> / <a href="/blog/{p["theme"]}/">{t["name"]}</a></div>'
          f'<div class="tags"><span class="tg">{t["name"]}</span><span>{TYPES[p["type"]]}</span></div>'
          f'<h1 class="d">{esc(p["title"])}</h1><div class="byline">Adithya Venkatesh · {p["date_h"]} · {p["mins"]} min read</div>'
          f'<div class="tags">{tags}</div>{ban}<div class="body">{p["html"]}</div></article>')
    rel = [x for x in posts if x["theme"] == p["theme"] and x["slug"] != p["slug"]]
    if len(rel) < 2:
        rel += [x for x in posts if x["theme"] != p["theme"] and x["slug"] != p["slug"]][:2 - len(rel)]
    h += ('<div class="more"><div class="sh"><h2 class="d">Keep reading</h2>' + SQUIG + '</div><div class="list">'
          + "".join(card(x, 2 + i, feature=False) for i, x in enumerate(rel[:2])) + "</div></div></div>")
    h += FOOT + "</body></html>"
    return h


def share_card(path, title, label, color=None):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), Y)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill="#f2cf00")
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill="#f2cf00")
    d.rounded_rectangle([28, 28, W - 28, H - 28], radius=36, outline=K, width=8)
    mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_small, f_title = ImageFont.truetype(mono, 28), ImageFont.truetype(sans, 66)
    tw = d.textlength(label.upper(), font=f_small)
    d.rounded_rectangle([72, 70, 72 + tw + 40, 120], radius=25, fill=K)
    d.text((92, 80), label.upper(), font=f_small, fill=Y)
    words, lines, cur = title.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f_title) > W - 170:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    y = 170
    for ln in lines[:4]:
        d.text((72, y), ln.upper(), font=f_title, fill=K)
        y += 86
    d.line([(72, H - 112), (W - 72, H - 112)], fill=K, width=5)
    d.text((72, H - 90), "ADITHYA VENKATESH  ·  AV CONNECTED  ·  BLOG", font=f_small, fill=K)
    im.save(path, optimize=True)


def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        sys.exit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for key in ("title", "theme", "type", "date", "summary"):
        if not meta.get(key):
            sys.exit(f"{path.name}: front matter lacks '{key}'")
    if meta["theme"] not in THEMES:
        sys.exit(f"{path.name}: unknown theme {meta['theme']}")
    if meta["type"] not in TYPES:
        sys.exit(f"{path.name}: unknown type {meta['type']}")
    from datetime import date as _d
    if re.fullmatch(r"\d{4}-\d{2}", meta["date"]):      # month only, e.g. 2024-02
        _dt = _d.fromisoformat(meta["date"] + "-01")
        meta["date_h"] = _dt.strftime("%B %Y")
        meta["date"] = meta["date"] + "-01"                # sort key
    else:
        _dt = _d.fromisoformat(meta["date"])
        meta["date_h"] = f"{_dt.day} {_dt.strftime('%B %Y')}"
    meta["slug"] = path.stem
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["placeholder"] = meta.get("status", "") == "placeholder"
    body = m.group(2).strip()
    meta["words"] = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", body)))
    meta["mins"] = max(1, round(meta["words"] / 200))
    meta["html"] = markdown.markdown(body, extensions=["fenced_code", "tables", "sane_lists"])
    return meta


def main():
    posts = sorted((parse(p) for p in SRC.glob("*.md")), key=lambda p: (not p["placeholder"], p["date"], p["title"]), reverse=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "og").mkdir(parents=True)
    (OUT / "index.html").write_text(index_page(posts), encoding="utf-8")
    for key in THEMES:
        (OUT / key).mkdir()
        (OUT / key / "index.html").write_text(index_page(posts, key), encoding="utf-8")
    for p in posts:
        d = OUT / "posts" / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(post_page(p, posts), encoding="utf-8")
        share_card(OUT / "og" / f"{p['slug']}.png", p["title"],
                   f"{THEMES[p['theme']]['name']} · {TYPES[p['type']]}", THEMES[p["theme"]]["color"])
    share_card(OUT / "og" / "_index.png", "Problems solved, decisions made, things built on the bench.",
               "Blog", BLOG_ACCENT)
    # data for the portfolio's home strip
    import json
    (OUT / "posts.json").write_text(json.dumps([
        {"slug": p["slug"], "title": p["title"], "theme": p["theme"], "themeName": THEMES[p["theme"]]["name"],
         "color": THEMES[p["theme"]]["color"], "type": TYPES[p["type"]], "mins": p["mins"],
         "placeholder": p["placeholder"]} for p in posts], indent=1), encoding="utf-8")
    print(f"built {len(posts)} posts, {len(THEMES)} theme pages")


if __name__ == "__main__":
    main()
