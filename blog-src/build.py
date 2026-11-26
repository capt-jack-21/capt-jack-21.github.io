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

CSS = """
:root{--bg:#07090d;--panel:#0d1219;--panel2:#111826;--line:#1c2635;--text:#e6edf3;--muted:#8b98a9;
--b:%(accent)s;--mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,"Liberation Mono",monospace;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1.2px) 0 0/26px 26px,var(--bg);color:var(--text);font-family:var(--sans);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1040px;margin:0 auto;padding:0 22px}
nav{position:sticky;top:0;z-index:20;background:rgba(7,9,13,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.mark{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:13px;letter-spacing:.14em;color:var(--muted)}
.mark b{display:inline-grid;place-items:center;width:28px;height:28px;border:1px solid var(--b);color:var(--b);border-radius:6px;font-size:12px;letter-spacing:0}
nav ul{display:flex;gap:22px;list-style:none;font-family:var(--mono);font-size:12px;letter-spacing:.06em}
nav ul a{color:var(--muted);transition:color .15s}nav ul a:hover,nav ul a.on{color:var(--b)}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.2em;color:var(--b);text-transform:uppercase;display:flex;align-items:center;gap:10px}
.eyebrow i{width:8px;height:8px;border-radius:50%%;background:var(--b)}
.hero{padding:64px 0 36px;border-bottom:1px solid var(--line)}
h1{font-size:clamp(30px,5vw,46px);line-height:1.15;margin:14px 0 12px;letter-spacing:-.01em}
h1 span{color:var(--b)}
.lede{color:var(--muted);max-width:660px;font-size:17px}
.themes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:34px 0 8px}
.tcard{display:block;background:rgba(13,18,25,.88);border:1px solid var(--line);border-top:2px solid var(--c);border-radius:12px;padding:18px;transition:border-color .2s,transform .2s}
.tcard:hover{border-color:var(--c);transform:translateY(-2px)}
.tcard h3{font-size:17px;margin-bottom:6px;color:var(--c)}
.tcard p{color:var(--muted);font-size:13.5px;min-height:62px}
.tcard .meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:12px;letter-spacing:.04em}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:30px 0 18px}
.chip{font-family:var(--mono);font-size:12px;letter-spacing:.04em;padding:7px 12px;border-radius:999px;border:1px solid var(--line);color:var(--muted);background:transparent;cursor:pointer;transition:all .15s}
.chip:hover{color:var(--text);border-color:var(--muted)}
.chip.on{color:#07090d;background:var(--b);border-color:var(--b);font-weight:700}
.sep{width:1px;height:22px;background:var(--line);margin:0 4px}
.search{margin-left:auto;font-family:var(--mono);font-size:12px;background:var(--panel);border:1px solid var(--line);border-radius:8px;color:var(--text);padding:8px 12px;min-width:190px}
.search:focus{outline:none;border-color:var(--b)}
.list{display:grid;gap:12px;margin-bottom:60px}
.post{display:block;background:rgba(13,18,25,.88);border:1px solid var(--line);border-left:3px solid var(--c);border-radius:10px;padding:16px 18px;transition:border-color .2s,transform .2s}
.post:hover{border-color:var(--c);transform:translateY(-1px)}
.post h3{font-size:18px;line-height:1.3;margin:6px 0}
.post p{color:var(--muted);font-size:14px}
.tags{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-family:var(--mono);font-size:11.5px;letter-spacing:.04em;color:var(--muted)}
.th{color:var(--c);font-weight:700;text-transform:uppercase;letter-spacing:.1em}
.ph{border:1px dashed #6b7686;border-radius:4px;padding:0 6px;color:#aab4c2;text-transform:uppercase;letter-spacing:.1em}
.empty{color:var(--muted);font-family:var(--mono);font-size:13px;padding:20px 0;display:none}
article{max-width:720px;margin:0 auto;padding:44px 22px 20px}
article .crumb{font-family:var(--mono);font-size:12px;color:var(--muted);letter-spacing:.04em;margin-bottom:22px}
article .crumb a{color:var(--c)}
article h1{font-size:clamp(28px,4.6vw,40px);margin:12px 0 10px}
.byline{color:var(--muted);font-size:14px;margin-bottom:6px}
.banner{margin:22px 0;padding:12px 14px;border:1px dashed #6b7686;border-radius:8px;color:#aab4c2;font-family:var(--mono);font-size:12.5px}
.body h2{font-size:22px;margin:34px 0 10px;padding-top:6px;border-top:1px solid var(--line)}
.body p,.body ul,.body ol,.body table{margin:12px 0}
.body ul,.body ol{padding-left:22px}
.body li{margin:5px 0}
.body em{color:#aab4c2}
.body code{font-family:var(--mono);font-size:.9em;background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
.body pre{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;margin:14px 0}
.body pre code{background:none;border:0;padding:0}
.body blockquote{border-left:3px solid var(--c);padding:4px 14px;color:var(--muted);margin:14px 0}
.body table{border-collapse:collapse;width:100%%;font-size:14px}
.body th,.body td{border:1px solid var(--line);padding:8px 10px;text-align:left}
.body th{background:var(--panel2);font-family:var(--mono);font-size:12px;letter-spacing:.04em}
.more{max-width:720px;margin:34px auto 70px;padding:0 22px}
.more h4{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
footer{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--muted);font-family:var(--mono);font-size:12px}
footer .wrap{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
footer a:hover{color:var(--b)}
@media(max-width:720px){nav ul li.hide{display:none}.search{margin-left:0;width:100%%}.sep{display:none}}
""" % {"accent": BLOG_ACCENT}


def esc(s):
    return html.escape(s, quote=True)


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
    meta["slug"] = path.stem
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["placeholder"] = meta.get("status", "") == "placeholder"
    body = m.group(2).strip()
    meta["words"] = len(re.findall(r"\w+", body))
    meta["mins"] = max(1, round(meta["words"] / 200))
    meta["html"] = markdown.markdown(body, extensions=["fenced_code", "tables", "sane_lists"])
    return meta


def head(title, desc, url, image, extra_css=""):
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
<meta name="theme-color" content="#07090d">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%2307090d'/%3E%3Cpath d='M12 50 28 14l8 18' fill='none' stroke='%23ffd400' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M32 14l16 36' fill='none' stroke='%23e6edf3' stroke-width='6' stroke-linecap='round'/%3E%3C/svg%3E">
<style>{CSS}{extra_css}</style></head><body>"""


def nav(on_blog=True):
    return """<nav><div class="wrap">
<a class="mark" href="/blog/"><b>AV</b>BLOG</a>
<ul><li class="hide"><a href="/#cases">Case studies</a></li><li class="hide"><a href="/#projects">Projects</a></li>
<li><a href="/blog/" class="on">Blog</a></li><li><a href="/">← Portfolio</a></li></ul></div></nav>"""


FOOT = """<footer><div class="wrap"><span>Adithya Venkatesh · AV Connected</span>
<span><a href="/">Portfolio</a> · <a href="/blog/">Blog</a> · <a href="https://github.com/capt-jack-21" rel="noopener">GitHub</a></span></div></footer></body></html>"""


def card(p):
    c = THEMES[p["theme"]]["color"]
    ph = '<span class="ph">placeholder</span>' if p["placeholder"] else ""
    return (f'<a class="post" href="/blog/posts/{p["slug"]}/" style="--c:{c}" '
            f'data-theme="{p["theme"]}" data-type="{p["type"]}" '
            f'data-q="{esc((p["title"] + " " + p["summary"] + " " + " ".join(p["tags"])).lower())}">'
            f'<div class="tags"><span class="th">{THEMES[p["theme"]]["name"]}</span><span>·</span>'
            f'<span>{TYPES[p["type"]]}</span><span>·</span><span>{p["mins"]} min</span>{ph}</div>'
            f'<h3>{esc(p["title"])}</h3><p>{esc(p["summary"])}</p></a>')


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
    h = head(title, desc, url, f"{SITE}/blog/og/_index.png")
    h += nav()
    h1 = (f'<span>{esc(THEMES[preset]["name"])}</span>' if preset else "Blog")
    sub = (THEMES[preset]["blurb"] if preset else
           "Problems I have solved, decisions I have made and things I build on the bench. Four themes, written plainly.")
    h += f'<header class="hero"><div class="wrap"><div class="eyebrow"><i></i> Notes from the field</div><h1>{h1}</h1><p class="lede">{esc(sub)}</p>'
    cards = ""
    for key, t in THEMES.items():
        n = sum(1 for p in posts if p["theme"] == key)
        cards += (f'<a class="tcard" href="/blog/{key}/" style="--c:{t["color"]}"><h3>{t["name"]}</h3>'
                  f'<p>{esc(t["blurb"])}</p><div class="meta">{n} post{"s" if n != 1 else ""}</div></a>')
    h += f'<div class="themes">{cards}</div></div></header><main class="wrap">'
    tchips = '<button class="chip on" data-t="">All themes</button>' + "".join(
        f'<button class="chip" data-t="{k}">{v["name"]}</button>' for k, v in THEMES.items())
    ychips = '<button class="chip on" data-y="">All types</button>' + "".join(
        f'<button class="chip" data-y="{k}">{v}</button>' for k, v in TYPES.items())
    h += f'<div class="bar">{tchips}<span class="sep"></span>{ychips}<input class="search" id="q" type="search" placeholder="search posts" aria-label="Search posts"></div>'
    h += '<div class="list" id="list">' + "".join(card(p) for p in posts) + '</div><p class="empty" id="none">No posts match yet.</p></main>'
    h += FOOT.replace("</body></html>", "")
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
    c = t["color"]
    url = f"{SITE}/blog/posts/{p['slug']}/"
    h = head(f"{p['title']} · Adithya Venkatesh", p["summary"], url, f"{SITE}/blog/og/{p['slug']}.png",
             f"article,.more{{--c:{c}}}")
    h += nav()
    ban = ('<div class="banner">PLACEHOLDER: this is an outline with the structure of the final post. '
           'The real write-up will replace it.</div>') if p["placeholder"] else ""
    tags = "".join(f"<span>#{esc(x)}</span>" for x in p["tags"])
    h += (f'<article><div class="crumb"><a href="/blog/">Blog</a> / <a href="/blog/{p["theme"]}/">{t["name"]}</a></div>'
          f'<div class="tags"><span class="th">{t["name"]}</span><span>·</span><span>{TYPES[p["type"]]}</span>'
          f'<span>·</span><span>{p["mins"]} min read</span></div>'
          f'<h1>{esc(p["title"])}</h1><p class="byline">Adithya Venkatesh · {p["date"]}</p>'
          f'<div class="tags">{tags}</div>{ban}<div class="body">{p["html"]}</div></article>')
    rel = [x for x in posts if x["theme"] == p["theme"] and x["slug"] != p["slug"]]
    if len(rel) < 2:
        rel += [x for x in posts if x["theme"] != p["theme"] and x["slug"] != p["slug"]][:2 - len(rel)]
    h += '<div class="more"><h4>Keep reading</h4><div class="list">' + "".join(card(x) for x in rel[:2]) + "</div></div>"
    h += FOOT
    return h


def share_card(path, title, label, color):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#07090d")
    d = ImageDraw.Draw(im)
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill="#0d121a")
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill="#0d121a")
    d.rectangle([0, 0, 14, H], fill=color)
    mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_small, f_title = ImageFont.truetype(mono, 28), ImageFont.truetype(sans, 60)
    d.text((70, 64), label.upper(), font=f_small, fill=color)
    words, lines, cur = title.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f_title) > W - 150:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    y = 170
    for ln in lines[:4]:
        d.text((70, y), ln, font=f_title, fill="#e6edf3")
        y += 78
    d.text((70, H - 80), "ADITHYA VENKATESH  ·  AV CONNECTED  ·  BLOG", font=f_small, fill="#8b98a9")
    im.save(path, optimize=True)


def main():
    posts = sorted((parse(p) for p in SRC.glob("*.md")), key=lambda p: (p["date"], p["title"]), reverse=True)
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
