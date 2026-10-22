#!/usr/bin/env python3
"""Build the explainer: inline src/sections/*.html into src/shell.html and lint them.

Usage:
    python3 -I src/build.py [--only GLOB[,GLOB...]] [--out PATH]

--only  filename globs (matched against e.g. 000-hero.html), comma separated.
--out   output file (default dist/index.html). dist/dt-dragonfly-mark.svg is
        copied beside it. Safe to run concurrently: output is written to a unique
        temp file in the target directory and then renamed into place.

Exit status is 1 when the lint finds any ERROR (the page is still written so it
can be inspected), 0 otherwise. WARN lines never change the exit status.
"""
import argparse
import fnmatch
import os
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
SECTIONS_DIR = os.path.join(SRC, "sections")
SHELL = os.path.join(SRC, "shell.html")
DEFAULT_OUT = os.path.join(ROOT, "dist", "index.html")
MARK = os.path.join(ROOT, "dist", "dt-dragonfly-mark.svg")
PLACEHOLDER = "<!--SECTIONS-->"

PARTS = {"intro", "apis", "mcp", "safe", "close"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
FORBIDDEN_TAGS = {"img": "no <img> tags (use inline SVG)",
                  "iframe": "no <iframe>", "object": "no <object>",
                  "embed": "no <embed>", "link": "no <link> in fragments",
                  "base": "no <base>", "meta": "no <meta> in fragments"}
URL_ATTRS = {"src", "href", "xlink:href", "poster", "action", "data", "srcset", "formaction"}
HEX_ATTRS = {"fill", "stroke", "stop-color", "flood-color", "lighting-color", "color"}
EXTERNAL = re.compile(r"^(?:https?:)?//", re.I)
CSS_URL_EXTERNAL = re.compile(r"url\(\s*['\"]?\s*(?:https?:)?//", re.I)
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⭐⭕️‍]")
AMERICAN = re.compile(
    r"\b(colors?|colou?red|centers?|centered|organizations?|organized|organizing|analy[sz]e[sd]?|"
    r"analy[sz]ing|favorites?|behaviors?|grays?|summariz\w*|recogniz\w*|customiz\w*|"
    r"authoriz\w*|minimiz\w*|prioritiz\w*)\b", re.I)
AMERICAN_OK = {"analyse", "analysed", "analyses"}
NETWORK_JS = re.compile(r"\b(fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts)")


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def error(self, where, msg, line=None):
        self.errors += 1
        print("ERROR %s%s: %s" % (where, (":%d" % line) if line else "", msg))

    def warn(self, where, msg, line=None):
        self.warnings += 1
        print("WARN  %s%s: %s" % (where, (":%d" % line) if line else "", msg))


# ---------------------------------------------------------------- HTML parse
class Frag(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # open element names
        self.roots = []          # (tag, attrs, line) of depth-0 elements
        self.ids = []            # (id, line)
        self.tags = []           # (tag, attrs, line)
        self.styles = []         # (css, line)
        self.scripts = []        # (js, line)
        self.texts = []          # (text, line)
        self.stray = []          # (text, line) non-whitespace text at depth 0
        self._cur = None         # (kind, line, [chunks]) while inside style/script

    def _open(self, tag, attrs, selfclose):
        line = self.getpos()[0]
        a = dict((k, (v if v is not None else "")) for k, v in attrs)
        if not self.stack:
            self.roots.append((tag, a, line))
        self.tags.append((tag, a, line))
        if "id" in a:
            self.ids.append((a["id"], line))
        if tag in ("style", "script") and not selfclose:
            self._cur = (tag, line, [])
        if not selfclose and tag not in VOID:
            self.stack.append(tag)

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, True)

    def handle_endtag(self, tag):
        if self._cur and self._cur[0] == tag:
            kind, line, chunks = self._cur
            (self.styles if kind == "style" else self.scripts).append(("".join(chunks), line))
            self._cur = None
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        line = self.getpos()[0]
        if self._cur:
            self._cur[2].append(data)
            return
        if not self.stack:
            if data.strip():
                self.stray.append((data.strip(), line))
            return
        if "template" in self.stack:
            return
        self.texts.append((data, line))


# ---------------------------------------------------------------------- CSS
def strip_css_comments(css):
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), css, flags=re.S)


def match_brace(s, i):
    """s[i] == '{'. Return index of the matching '}' (or len(s))."""
    depth = 0
    j = i
    quote = None
    while j < len(s):
        c = s[j]
        if quote:
            if c == "\\":
                j += 1
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return len(s)


def split_selectors(sel):
    out, depth, cur = [], 0, ""
    for c in sel:
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if c == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def lint_css(css, sec_id, prefix, where, rep, line0):
    """Scope check (every selector starts with #s-XXX) plus the declaration rules."""
    css = strip_css_comments(css)
    scope = re.compile(r"^#" + re.escape(sec_id) + r"(?![\w\\-])(?!\s*[+~])")
    rules = []

    def walk(s):
        i = 0
        while i < len(s):
            if s[i].isspace():
                i += 1
                continue
            if s[i] == "@":
                m = re.match(r"@([\w-]+)", s[i:])
                name = m.group(1).lower() if m else ""
                brace = s.find("{", i)
                semi = s.find(";", i)
                if semi != -1 and (brace == -1 or semi < brace):
                    rep.error(where, "@%s statement is not allowed in a fragment" % name, line0)
                    i = semi + 1
                    continue
                if brace == -1:
                    return
                end = match_brace(s, brace)
                head = s[i:brace]
                if name.endswith("keyframes"):
                    kf = head.split(None, 1)[1].strip() if len(head.split(None, 1)) > 1 else ""
                    if not kf.startswith(prefix):
                        rep.error(where, "@keyframes name '%s' must start with '%s'" % (kf, prefix), line0)
                elif name in ("media", "supports", "container", "layer"):
                    walk(s[brace + 1:end])
                else:
                    rep.error(where, "@%s is not allowed in a fragment" % name, line0)
                i = end + 1
                continue
            brace = s.find("{", i)
            if brace == -1:
                return
            sel = s[i:brace]
            for one in split_selectors(sel):
                if not scope.match(one):
                    rep.error(where, "CSS selector '%s' must start with #%s" % (one[:70], sec_id), line0)
            end = match_brace(s, brace)
            rules.append((sel, s[brace + 1:end]))
            i = end + 1

    walk(css)
    lint_decls(css, rules, sec_id, where, rep, line0)


HEX = re.compile(r"(?<![\w&-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])")
HEADING_SEL = re.compile(r"(?<![\w-])(h[1-3]|\.h2|\.h3|\.h-display)(?![\w-])")
GRADIENT = re.compile(r"(?:linear|radial|conic|repeating-linear|repeating-radial)-gradient\(", re.I)
FORBID_DECLS = [
    (re.compile(r"position\s*:\s*fixed", re.I), "position: fixed is not allowed in a fragment (the presenter bar owns the fixed layer)"),
    (re.compile(r"scroll-snap-[\w-]+\s*:", re.I), "scroll-snap is not allowed (normal scrolling only)"),
    (re.compile(r"scroll-behavior\s*:", re.I), "scroll-behavior is not allowed (the presenter script owns it)"),
]


def lint_decls(css, rules, sec_id, where, rep, line):
    """Declaration rules shared by <style> blocks and style="" attributes (rules is [(selector, body)])."""
    for rx, msg in FORBID_DECLS:
        if rx.search(css):
            rep.error(where, msg, line)
    for m in re.finditer(r"box-shadow\s*:\s*([^;}]*)", css, re.I):
        val = re.sub(r"!\s*important", "", m.group(1), flags=re.I).strip().lower()
        if val not in ("none", "inherit", "initial", "unset"):
            rep.error(where, "box-shadow is not allowed (the design is flat): %r" % val[:40], line)
    if re.search(r"drop-shadow\s*\(", css, re.I):
        rep.warn(where, "drop-shadow filter: the design is flat, no shadows", line)
    if re.search(r"image-set\s*\(\s*(?:url\(|['\"])", css, re.I):
        rep.error(where, "image-set() with URLs is not allowed", line)
    m = HEX.search(css)
    if m:
        rep.warn(where, "hex colour %s in CSS: use a token (var(--...))" % m.group(0), line)
    for sel, body in rules:
        if GRADIENT.search(body):
            if sec_id in ("s-12", "s-hero") and ".grad" in sel:
                continue
            rep.warn(where, "gradient in '%s' (gradients are for .grad in the hero and s-12 only)" % sel.strip()[:50], line)
        if HEADING_SEL.search(sel):
            m = re.search(r"font-weight\s*:\s*(\d+|bold|bolder)", body, re.I)
            if m and (not m.group(1).isdigit() or int(m.group(1)) >= 600):
                rep.warn(where, "bold weight on a heading ('%s'): headings stay regular (400)" % sel.strip()[:50], line)
    for m in re.finditer(r"font-size\s*:\s*([\d.]+)(px|rem)\b", css, re.I):
        px = float(m.group(1)) * (16 if m.group(2).lower() == "rem" else 1)
        if px < 15:
            rep.warn(where, "font-size %s%s is under 15px" % (m.group(1), m.group(2)), line)


# ---------------------------------------------------------------- JS helpers
def js_code(js):
    """Return js with comments blanked (strings and template literals preserved)."""
    out, i, n = [], 0, len(js)
    while i < n:
        c = js[i]
        if c in "\"'`":
            j = i + 1
            while j < n and js[j] != c:
                j += 2 if js[j] == "\\" else 1
            out.append(js[i:j + 1]); i = j + 1
        elif js.startswith("//", i):
            j = js.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i)); i = j
        elif js.startswith("/*", i):
            j = js.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(re.sub(r"[^\n]", " ", js[i:j])); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def js_match_brace(code, i):
    """code[i] == '{'. Index of the matching '}' or -1, skipping strings, templates and regex literals."""
    depth, n, prev = 0, len(code), ""
    j = i
    while j < n:
        c = code[j]
        if c in "\"'":
            k = j + 1
            while k < n and code[k] != c:
                k += 2 if code[k] == "\\" else 1
            j = k; prev = "x"
        elif c == "`":
            k = j + 1
            while k < n and code[k] != "`":
                if code[k] == "\\":
                    k += 2
                elif code.startswith("${", k):
                    e = js_match_brace(code, k + 1)
                    k = (e if e != -1 else n) + 1
                else:
                    k += 1
            j = k; prev = "x"
        elif c == "/" and (prev == "" or prev in "(,=:[!&|?{};" or re.search(r"(?:return|typeof|case)\s*$", code[max(0, j - 8):j])):
            k = j + 1
            in_cls = False
            while k < n and (code[k] != "/" or in_cls) and code[k] != "\n":
                if code[k] == "\\":
                    k += 1
                elif code[k] == "[":
                    in_cls = True
                elif code[k] == "]":
                    in_cls = False
                k += 1
            j = k; prev = "x"
        elif c == "{":
            depth += 1; prev = c
        elif c == "}":
            depth -= 1; prev = c
            if depth == 0:
                return j
        elif not c.isspace():
            prev = c
        j += 1
    return -1


IIFE_HEAD = re.compile(r"^;?\s*\(\s*(?:async\s+)?(?:function\s*[\w$]*\s*\(\s*\)|\(\s*\)\s*=>)\s*\{")
IIFE_TAIL = re.compile(r"^\s*(?:\)\s*\(\s*\)|\(\s*\)\s*\))\s*;?\s*$")


def is_single_iife(js):
    code = js_code(js).strip()
    if not code:
        return True
    m = IIFE_HEAD.match(code)
    if not m:
        return False
    end = js_match_brace(code, m.end() - 1)
    return end != -1 and bool(IIFE_TAIL.match(code[end + 1:]))


STR_LIT = re.compile(r"""(['"`])((?:\\.|(?!\1)[^\\])*)\1""", re.S)


def js_text_literals(js):
    """String literals that become visible or spoken text: DT.announce(...), textContent/innerHTML =, aria-label/title/alt."""
    code = js_code(js)
    found = []
    for m in re.finditer(r"DT\s*\.\s*announce\s*\(", code):
        j = m.end()
        depth = 1
        while j < len(code) and depth:
            depth += {"(": 1, ")": -1}.get(code[j], 0)
            j += 1
        found += [x.group(2) for x in STR_LIT.finditer(code[m.end():j])]
    for m in re.finditer(r"(?:textContent|innerText|innerHTML)\s*\+?=\s*([^;\n]*)", code):
        found += [x.group(2) for x in STR_LIT.finditer(m.group(1))]
    for m in re.finditer(r"setAttribute\(\s*['\"](?:aria-label|title|alt)['\"]\s*,\s*([^;\n]*)", code):
        found += [x.group(2) for x in STR_LIT.finditer(m.group(1))]
    return found


# --------------------------------------------------------------------- lint
IZE = re.compile(r"\b[a-z]{3,}(?:iz(?:e|es|ed|ing|ation|ations))\b", re.I)
IZE_OK = {"capsize", "downsize", "upsize", "oversize", "undersize", "supersize", "outsize", "resize",
          "resized", "resizes", "resizing", "baize", "maize"}
BANG = re.compile(r"!(?!=)")


def american_hits(t):
    hits = [m.group(0) for m in AMERICAN.finditer(t) if m.group(0).lower() not in AMERICAN_OK]
    hits += [m.group(0) for m in IZE.finditer(t) if m.group(0).lower() not in IZE_OK]
    return hits


def lint_text(texts, where, rep):
    for text, line in texts:
        t = text.strip()
        if not t:
            continue
        if "!" in t:
            rep.warn(where, "'!' in visible text: %r" % t[:60], line)
        if EMOJI.search(t):
            rep.warn(where, "emoji/pictograph in visible text: %r" % t[:60], line)
        for h in american_hits(t):
            rep.warn(where, "American spelling %r in visible text (use Australian)" % h, line)


def clean_url(v):
    """Strip whitespace and control characters (browsers ignore them inside URLs) and unify slashes."""
    return re.sub(r"[\x00-\x20\x7f]+", "", v).replace("\\", "/")


BAD_SCHEME = re.compile(r"^(javascript|data|vbscript|mailto):", re.I)
LINKISH = {"href", "xlink:href", "action", "formaction"}
ALLOWED_LINK_HOSTS = {"datacommons.org", "www.datacommons.org"}


def check_url(tag, attrs, k, v, where, rep, line):
    n = clean_url(v)
    if k in LINKISH and BAD_SCHEME.match(n):
        rep.error(where, "%s: URL scheme not allowed in %s=%r" % (n.split(":")[0].lower(), k, v[:50]), line)
        return
    parts = [clean_url(x.strip().split(" ")[0]) for x in v.split(",")] if k == "srcset" else [n]
    for u in parts:
        if not EXTERNAL.match(u):
            continue
        host = urlsplit(u if u.lower().startswith("http") else "https:" + u)
        if tag == "a" and k == "href" and (host.hostname or "") in ALLOWED_LINK_HOSTS:
            rel = attrs.get("rel", "").lower().split()
            if host.scheme != "https" or host.netloc.lower() != host.hostname:
                rep.error(where, "datacommons.org links must be plain https://datacommons.org (no userinfo or port): %r" % v[:60], line)
            elif attrs.get("target") != "_blank" or "noopener" not in rel:
                rep.error(where, 'datacommons.org links need target="_blank" rel="noopener"', line)
            continue
        rep.error(where, 'external URL in %s="%s" (only https://datacommons.org links are allowed)' % (k, v[:60]), line)


def lint_fragment(name, html, rep, seen_ids, shell_ids=frozenset()):
    where = name
    p = Frag()
    p.feed(html)
    p.close()

    for text, line in p.stray:
        rep.error(where, "text outside the root <section>: %r" % text[:40], line)
    roots = [r for r in p.roots]
    if len(roots) != 1 or roots[0][0] != "section":
        rep.error(where, "fragment must have exactly one root <section> (found: %s)" %
                  (", ".join("<%s>" % r[0] for r in roots) or "none"))
        if not roots or roots[0][0] != "section":
            return None
    _, attrs, sline = roots[0]
    sid = attrs.get("id", "")
    if not re.match(r"^s-[a-z0-9]+$", sid):
        rep.error(where, "root <section> needs id like s-04 / s-hero (got %r)" % sid, sline)
        return None
    prefix = "s" + sid[2:] + "-"
    if attrs.get("data-part") not in PARTS:
        rep.error(where, "data-part must be one of %s (got %r)" % (sorted(PARTS), attrs.get("data-part")), sline)
    if not attrs.get("data-label", "").strip():
        rep.error(where, "root <section> needs a data-label", sline)
    if "slide" not in attrs.get("class", "").split():
        rep.error(where, 'root <section> needs class="slide" (the presenter bar only finds main > section.slide)', sline)
    lb = attrs.get("aria-labelledby")
    if not lb:
        rep.warn(where, "root <section> should have aria-labelledby pointing at its heading", sline)
    if sid in seen_ids:
        rep.error(where, "duplicate section id %r (also in %s)" % (sid, seen_ids[sid]), sline)
    seen_ids[sid] = name

    # ids
    local = set()
    for i, line in p.ids:
        if i == sid and line == sline:
            continue
        if i in local:
            rep.error(where, "duplicate id %r inside fragment" % i, line)
        local.add(i)
        if not i.startswith(prefix):
            rep.error(where, "id %r must start with %r" % (i, prefix), line)
    if lb:
        for ref in lb.split():
            if ref not in local:
                rep.warn(where, "aria-labelledby points at missing id %r" % ref, sline)

    # tags / urls / attributes
    for tag, a, line in p.tags:
        if tag in FORBIDDEN_TAGS:
            rep.error(where, "<%s>: %s" % (tag, FORBIDDEN_TAGS[tag]), line)
        if tag == "script" and "src" in a:
            rep.error(where, "no <script src>: fragment scripts must be inline", line)
        for k, v in a.items():
            if k.startswith("on") and len(k) > 3 and k[2:].isalpha():
                rep.warn(where, "inline %s handler: use addEventListener inside the script IIFE" % k, line)
            if k in URL_ATTRS:
                check_url(tag, a, k, v, where, rep, line)
            if k == "style":
                if CSS_URL_EXTERNAL.search(v):
                    rep.error(where, "external url() in inline style", line)
                lint_decls(v, [], sid, where, rep, line)
                if GRADIENT.search(v):
                    rep.warn(where, "gradient in an inline style", line)
                if tag in ("h1", "h2", "h3") and re.search(r"font-weight\s*:\s*(?:[6-9]00|bold)", v, re.I):
                    rep.warn(where, "bold weight on a heading", line)
            if k in ("aria-label", "title", "alt", "placeholder"):
                if "!" in v:
                    rep.warn(where, "'!' in %s=%r" % (k, v[:50]), line)
                for h in american_hits(v):
                    rep.warn(where, "American spelling %r in %s=%r" % (h, k, v[:50]), line)
            if k in HEX_ATTRS and HEX.fullmatch(v.strip()):
                rep.warn(where, "hex colour %s in %s attribute: use a token (currentColor or var(--...))" % (v.strip(), k), line)
        if tag == "use":
            ref = a.get("href", a.get("xlink:href", ""))
            if ref.startswith("#") and ref[1:] not in shell_ids and ref[1:] not in local:
                rep.error(where, '<use href="%s"> points to an id that exists in neither the shell nor this fragment' % ref, line)
    for css, line in p.styles:
        if CSS_URL_EXTERNAL.search(css) or re.search(r"@import", css):
            rep.error(where, "external url()/@import in <style>", line)
        lint_css(css, sid, prefix, where, rep, line)
    for js, line in p.scripts:
        if not is_single_iife(js):
            rep.error(where, "script must be a single IIFE: (()=>{ ... })(); or (function(){ ... })();", line)
        code = js_code(js)
        if NETWORK_JS.search(code):
            rep.warn(where, "script appears to make a network call; everything must be simulated", line)
        for m in re.finditer(r"getElementById\(\s*['\"]([^'\"]+)['\"]", code):
            if m.group(1) != sid and not m.group(1).startswith(prefix):
                rep.warn(where, "getElementById(%r) outside this section's prefix" % m.group(1), line)
        if re.search(r"\bdocument\.querySelector(All)?\(", code):
            rep.warn(where, "use root.querySelector, not document.querySelector, so the fragment stays scoped", line)
        for m in re.finditer(r"\b(document\.body|document|window)\s*\.\s*addEventListener\(\s*['\"`](keydown|keyup|keypress|wheel)['\"`]", code):
            rep.warn(where, "%s.addEventListener('%s'): attach key and wheel handlers to your own elements (presenter keys live on document)" % (m.group(1), m.group(2)), line)
        for lit in js_text_literals(js):
            if BANG.search(lit):
                rep.warn(where, "'!' in script text literal %r" % lit[:50], line)
            for h in american_hits(lit):
                rep.warn(where, "American spelling %r in script text literal %r" % (h, lit[:40]), line)
    lint_text(p.texts, where, rep)
    return sid


def lint_shell(html, rep):
    where = "shell.html"
    if PLACEHOLDER not in html:
        rep.error(where, "missing %s placeholder" % PLACEHOLDER)
    for m in re.finditer(r"""(?:src|href)\s*=\s*["'](?:https?:)?//([^"'/]+)""", html, re.I):
        if m.group(1) not in ("fonts.googleapis.com", "fonts.gstatic.com"):
            rep.error(where, "external URL host %s (only Google Fonts allowed)" % m.group(1))
    for m in re.finditer(r"url\(\s*['\"]?(?:https?:)?//([^'\")/]+)", html, re.I):
        rep.error(where, "external url() host %s" % m.group(1))
    p = Frag()
    p.feed(html)
    p.close()
    lint_text(p.texts, where, rep)


# --------------------------------------------------------------------- main
def write_atomic(path, data, binary=False):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".build-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f:
            f.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma separated filename globs, e.g. '000-*,10[1-3]-*'")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output file (default dist/index.html)")
    args = ap.parse_args()

    rep = Report()
    with open(SHELL, encoding="utf-8") as f:
        shell = f.read()
    lint_shell(shell, rep)
    sp = Frag()
    sp.feed(shell)
    shell_ids = set(i for i, _ in sp.ids)

    files = sorted(fn for fn in os.listdir(SECTIONS_DIR) if fn.endswith(".html"))
    if args.only:
        globs = [g.strip() for g in args.only.split(",") if g.strip()]
        files = [fn for fn in files if any(fnmatch.fnmatch(fn, g) or fnmatch.fnmatch(fn[:-5], g) for g in globs)]
    if not files:
        rep.error("build", "no section files matched")
    seen = {}
    parts = []
    for fn in files:
        with open(os.path.join(SECTIONS_DIR, fn), encoding="utf-8") as f:
            html = f.read()
        lint_fragment(fn, html, rep, seen, shell_ids)
        parts.append("<!-- %s -->\n%s" % (fn, html.strip()))

    out = os.path.abspath(args.out)
    page = shell.replace(PLACEHOLDER, "\n\n".join(parts))
    write_atomic(out, page)
    if os.path.exists(MARK):
        with open(MARK, "rb") as f:
            write_atomic(os.path.join(os.path.dirname(out), "dt-dragonfly-mark.svg"), f.read(), binary=True)
    print("Built %d section(s) -> %s (%d KB). %d error(s), %d warning(s)." %
          (len(files), out, len(page.encode("utf-8")) // 1024, rep.errors, rep.warnings))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
