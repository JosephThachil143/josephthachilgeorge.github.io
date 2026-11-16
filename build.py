#!/usr/bin/env python3
"""Static site builder (stdlib only).

Reads src/*.html. Elements carry English in data-en and German in data-de
(the element's own content is ignored on build and only kept as a no-build
fallback). Attributes can be localised with data-de-<attr> (e.g. data-de-content).
Emits English pages at / and German pages at /de/, plus sitemap.xml, robots.txt.

Placeholders: {{HEAD_COMMON}}, {{LANGSWITCH}}, {{YEAR}}.
Usage: python3 build.py   ->  dist/
"""
import datetime
import html
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
SITE = "https://josephthachilgeorge.com"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
       "font-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; "
       "base-uri 'none'; form-action 'none'; upgrade-insecure-requests")

errors = []


def err(msg):
    errors.append(msg)


class Localizer(HTMLParser):
    def __init__(self, lang, name):
        super().__init__(convert_charrefs=False)
        self.lang, self.name = lang, name
        self.out = []
        self.skip_tag = None
        self.depth = 0

    # -- helpers
    def build_tag(self, tag, attrs, selfclose=False):
        parts = []
        for k, v in attrs:
            if k in ("data-en", "data-de"):
                continue
            if k.startswith("data-de-"):
                if self.lang == "de":
                    base = k[len("data-de-"):]
                    parts = [(a, b) for a, b in parts if a != base]
                    parts.append((base, v))
                continue
            if any(a == k for a, _ in parts):
                continue
            parts.append((k, v))
        s = "<" + tag
        for k, v in parts:
            s += f" {k}" if v is None else f' {k}="{html.escape(v, quote=True)}"'
        return s + (" />" if selfclose else ">")

    def start(self, tag, attrs, selfclose):
        if self.skip_tag:
            if tag == self.skip_tag and tag not in VOID and not selfclose:
                self.depth += 1
            return
        d = dict(attrs)
        has_en, has_de = "data-en" in d, "data-de" in d
        if has_en != has_de:
            err(f"{self.name}: <{tag}> has only one of data-en/data-de near {self.getpos()}")
        if has_en and has_de:
            self.out.append(self.build_tag(tag, attrs))
            self.out.append(d["data-" + self.lang])
            if tag in VOID:
                return
            self.skip_tag, self.depth = tag, 1
            return
        if any(k.startswith("data-de-") for k in d):
            self.out.append(self.build_tag(tag, attrs, selfclose))
        else:
            self.out.append(self.get_starttag_text())

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, True)

    def handle_endtag(self, tag):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.depth -= 1
                if self.depth == 0:
                    self.out.append(f"</{tag}>")
                    self.skip_tag = None
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip_tag:
            self.out.append(data)

    def handle_entityref(self, name):
        if not self.skip_tag:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self.skip_tag:
            self.out.append(f"&#{name};")

    def handle_decl(self, decl):
        self.out.append(f"<!{decl}>")


def page_url(name, lang):
    base = "/" if name == "index" else f"/{name}.html"
    if lang == "de":
        return "/de/" if name == "index" else f"/de{base}"
    return base


def localize(text, lang, name):
    p = Localizer(lang, name)
    p.feed(text)
    p.close()
    out = "".join(p.out)
    if lang == "de":
        def fix(m):
            path, _, frag = m.group(1).partition("#")
            if path.startswith("/de/"):
                return m.group(0)
            if path == "/" or path.endswith(".html"):
                path = "/de/" if path == "/" else "/de" + path
                return f'href="{path}{"#" + frag if frag else ""}"'
            return m.group(0)
        out = re.sub(r'href="(/(?!/)[^"]*)"', fix, out)
    return out


def grab(pattern, text):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def head_common(name, lang, body):
    title = grab(r"<title>(.*?)</title>", body)
    desc = grab(r'<meta name="description" content="([^"]*)"', body)
    url = SITE + page_url(name, lang)
    en, de = SITE + page_url(name, "en"), SITE + page_url(name, "de")
    e = lambda s: html.escape(s, quote=True)
    loc, alt = ("en_US", "de_DE") if lang == "en" else ("de_DE", "en_US")
    lines = [
        '<meta charset="UTF-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}" />',
        '<meta name="referrer" content="no-referrer" />',
        '<meta name="theme-color" content="#f4f7fb" />',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml" />',
        f'<link rel="canonical" href="{url}" />',
        f'<link rel="alternate" hreflang="en" href="{en}" />',
        f'<link rel="alternate" hreflang="de" href="{de}" />',
        f'<link rel="alternate" hreflang="x-default" href="{en}" />',
        '<meta property="og:type" content="website" />',
        '<meta property="og:site_name" content="Joseph Thachil George" />',
        f'<meta property="og:title" content="{e(title)}" />',
        f'<meta property="og:description" content="{e(desc)}" />',
        f'<meta property="og:url" content="{url}" />',
        f'<meta property="og:image" content="{SITE}/og-image.png" />',
        '<meta property="og:image:width" content="1200" />',
        '<meta property="og:image:height" content="630" />',
        f'<meta property="og:locale" content="{loc}" />',
        f'<meta property="og:locale:alternate" content="{alt}" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{e(title)}" />',
        f'<meta name="twitter:description" content="{e(desc)}" />',
        f'<meta name="twitter:image" content="{SITE}/og-image.png" />',
    ]
    return "\n  ".join(lines)


def lang_switch(name, lang):
    def a(l, label, full):
        cur = ' aria-current="true"' if l == lang else ""
        return (f'<a href="{page_url(name, l)}" lang="{l}" hreflang="{l}" '
                f'aria-label="{full}"{cur}>{label}</a>')
    return ('<span class="lang-switch">' + a("en", "EN", "English") +
            '<span class="lang-sep" aria-hidden="true">/</span>' + a("de", "DE", "Deutsch") + "</span>")


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "de").mkdir()
    pages = sorted(p.stem for p in SRC.glob("*.html"))
    for item in SRC.iterdir():
        if item.suffix == ".html":
            continue
        if item.is_dir():
            shutil.copytree(item, DIST / item.name)
        else:
            shutil.copy2(item, DIST / item.name)
    year = str(datetime.date.today().year)
    for name in pages:
        text = (SRC / f"{name}.html").read_text(encoding="utf-8")
        for lang in ("en", "de"):
            body = localize(text, lang, f"{name}[{lang}]")
            body = body.replace("{{HEAD_COMMON}}", head_common(name, lang, body))
            body = body.replace("{{LANGSWITCH}}", lang_switch(name, lang))
            body = body.replace("{{YEAR}}", year)
            body = re.sub(r'<html lang="[a-z]+"', f'<html lang="{lang}"', body, count=1)
            out = DIST / ("de" if lang == "de" else "") / f"{name}.html"
            out.write_text(body, encoding="utf-8")
    # sitemap + robots
    today = datetime.date.today().isoformat()
    urls = []
    for name in pages:
        for lang in ("en", "de"):
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{page_url(name, l)}"/>'
                for l in ("en", "de"))
            urls.append(f"  <url><loc>{SITE}{page_url(name, lang)}</loc><lastmod>{today}</lastmod>{alts}</url>")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    validate(pages)


def validate(pages):
    for f in DIST.rglob("*.html"):
        t = f.read_text(encoding="utf-8")
        rel = f.relative_to(DIST)
        if "{{" in t:
            err(f"{rel}: unexpanded placeholder")
        if re.search(r"\sdata-(en|de)(-\w+)?=", t):
            err(f"{rel}: leftover data-en/data-de attribute")
        if re.search(r"<style\b|<script(?![^>]*\bsrc=)|\sstyle=|\son[a-z]+=", t, re.I):
            err(f"{rel}: inline style/script/event handler (violates CSP)")
        if "fonts.googleapis" in t or "fonts.gstatic" in t:
            err(f"{rel}: external font reference")
        for href in re.findall(r'(?:href|src)="(/[^"]*)"', t):
            path = href.split("#")[0].split("?")[0]
            if path.startswith("//"):
                continue
            target = DIST / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                err(f"{rel}: broken internal link {href}")
        for rid in re.findall(r'href="[^"#]*#([^"]+)"', t):
            pass
    # in-page anchors and cross-page anchors
    for f in DIST.rglob("*.html"):
        t = f.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]*#[^"]+)"', t):
            path, _, frag = href.partition("#")
            if path.startswith("http") or path.startswith("mailto"):
                continue
            tgt = f if path == "" else (DIST / (path.lstrip("/") + ("index.html" if path.endswith("/") else "")))
            if tgt.exists() and f'id="{frag}"' not in tgt.read_text(encoding="utf-8"):
                err(f"{f.relative_to(DIST)}: anchor #{frag} not found in {tgt.relative_to(DIST)}")


if __name__ == "__main__":
    build()
    if errors:
        print("BUILD FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("Build OK ->", DIST)
