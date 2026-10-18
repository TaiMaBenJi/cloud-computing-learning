#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2html.py —— 把仓库里的 Markdown 生成成带 UTF-8 声明的 HTML 页面
=====================================================================
为什么要做：
  GitHub Pages 对 .md 返回 `Content-Type: text/markdown` **且不带 charset**，
  浏览器会按 Latin-1 猜编码 → 站内所有指向 .md 的链接打开全是乱码。
  本脚本把 .md 编译成 .html（显式 charset=utf-8 + 站内样式），并把
  HTML 页面里指向 .md 的链接改写成 .html，从根上消除乱码。

用法：
  python3 tools/md2html.py            # 全量生成 + 改写链接
  python3 tools/md2html.py --check    # 只检查：哪些 .md 还没有对应 .html
"""
import io, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIR = {".git", "node_modules"}
SITE = "https://taimabenji.github.io/cloud-computing-learning/"

# ---------------------------------------------------------------- 极简 Markdown 渲染
INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?!\*)")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def inline(t):
    """行内渲染。顺序很关键：代码片段必须**先摘出来占位**，
    否则 `2 + 3 * 4` 里的 * 会被当成斜体，把 <code> 拆成
    <code>2 + 3 <em> 4</code> 这种坏结构。"""
    t = html.escape(t, quote=False)
    t = IMG.sub(lambda m: '<img alt="%s" src="%s">' % (m.group(1), m.group(2)), t)
    t = LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1) or m.group(2)), t)
    # 1) 代码片段抽出为占位符，逃出后续所有正则
    slots = []
    def stash(m):
        slots.append("<code>%s</code>" % m.group(1))
        return "\x00%d\x00" % (len(slots) - 1)
    t = INLINE_CODE.sub(stash, t)
    # 2) 强调 / 加粗
    t = BOLD.sub(lambda m: "<strong>%s</strong>" % m.group(1), t)
    t = ITALIC.sub(lambda m: "<em>%s</em>" % m.group(1), t)
    # 3) 代码片段放回，内容保持字面量
    t = re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], t)
    return t


def slug(text, used):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower()).strip("-")
    s = s or "sec"
    base, n = s, 2
    while s in used:
        s = "%s-%d" % (base, n)
        n += 1
    used.add(s)
    return s


def render(md):
    out, used = [], set()
    lines = md.split("\n")
    i, n = 0, len(lines)
    in_code = False
    code_buf = []
    para = []
    lst = None            # None | 'ul' | 'ol'

    def flush_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para).strip()))
            para.clear()

    def close_list():
        nonlocal lst
        if lst:
            out.append("</%s>" % lst)
            lst = None

    while i < n:
        raw = lines[i]
        line = raw.rstrip()

        if line.strip().startswith("```"):
            flush_para(); close_list()
            if in_code:
                out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code_buf)))
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        if not line.strip():
            flush_para(); close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para(); close_list()
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            sid = slug(txt, used)
            out.append('<h%d id="%s">%s</h%d>' % (lvl, sid, inline(txt), lvl))
            i += 1
            continue

        # 表格
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            flush_para(); close_list()
            def cells(r):
                return [c.strip() for c in r.strip().strip("|").split("|")]
            head = cells(line)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            out.append("<div class=\"tw\"><table><thead><tr>"
                       + "".join("<th>%s</th>" % inline(c) for c in head)
                       + "</tr></thead><tbody>")
            for r in rows:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table></div>")
            continue

        m = re.match(r"^\s*([-*_])\1{2,}\s*$", line)
        if m:
            flush_para(); close_list()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            flush_para()
            if lst != "ul":
                close_list(); out.append("<ul>"); lst = "ul"
            out.append("<li>%s</li>" % inline(m.group(1)))
            i += 1
            continue

        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if m:
            flush_para()
            if lst != "ol":
                close_list(); out.append("<ol>"); lst = "ol"
            out.append("<li>%s</li>" % inline(m.group(2)))
            i += 1
            continue

        m = re.match(r"^\s*>\s?(.*)$", line)
        if m:
            flush_para(); close_list()
            out.append("<blockquote>%s</blockquote>" % inline(m.group(1)))
            i += 1
            continue

        para.append(line.strip())
        i += 1

    flush_para(); close_list()
    if in_code and code_buf:
        out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code_buf)))
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%(title)s - 知识公社</title>
<meta name="description" content="%(title)s：云计算竞赛学习项目文档。">
<meta name="theme-color" content="#0e1b33">
<link rel="stylesheet" href="%(css)s">
<style>
body{margin:0;background:#f3f6fb;color:#16233c;line-height:1.8;
font:16px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif}
.doc{max-width:860px;margin:0 auto;padding:26px 18px 80px}
.doc h1{font-size:26px;border-bottom:2px solid #2b5cd9;padding-bottom:10px;margin:6px 0 20px}
.doc h2{font-size:21px;margin:30px 0 12px;border-left:5px solid #2b5cd9;padding-left:10px}
.doc h3{font-size:17px;margin:22px 0 10px;color:#12408f}
.doc h4{font-size:15px;margin:18px 0 8px;color:#3b5a86}
.doc p{margin:10px 0}
.doc ul,.doc ol{padding-left:24px;margin:10px 0}
.doc li{margin:5px 0}
.doc a{color:#12408f}
.doc code{background:#eaf0fa;color:#0b3b86;padding:2px 6px;border-radius:4px;
font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9em}
.doc pre{background:#16233c;color:#e6edf3;padding:14px 16px;border-radius:8px;overflow-x:auto}
.doc pre code{background:none;color:#e6edf3;padding:0}
.doc blockquote{margin:12px 0;padding:10px 14px;background:#eaf0fa;border-left:4px solid #2b5cd9;
border-radius:0 6px 6px 0;color:#33405c}
.doc table,.tw table{width:100%%;border-collapse:collapse;margin:14px 0;font-size:14px;
background:#fff;box-shadow:0 1px 3px rgba(22,35,60,.08)}
.doc th,.doc td{border:1px solid #dde5f0;padding:8px 10px;text-align:left;vertical-align:top}
.doc th{background:#eaf0fa;font-weight:700}
.doc hr{border:0;border-top:1px solid #dde5f0;margin:24px 0}
.back{display:inline-block;margin-bottom:14px;color:#2b5cd9;text-decoration:none;font-size:14px}
@media(max-width:620px){.doc{font-size:15px;padding:18px 14px 60px}}
</style>
</head>
<body>
<div class="doc">
<a class="back" href="%(home)s">← 返回项目首页</a>
%(body)s
</div>
</body>
</html>
"""


def css_rel(md_rel):
    depth = md_rel.count("/")
    return "../" * depth + "style.css" if depth else "style.css"


def home_rel(md_rel):
    depth = md_rel.count("/")
    return "../" * depth + "index.html" if depth else "index.html"


def main():
    check_only = "--check" in sys.argv
    mds = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            if f.endswith(".md"):
                mds.append(os.path.join(dp, f))
    mds.sort()
    gen = 0
    for p in mds:
        rel = os.path.relpath(p, ROOT)
        out = p[:-3] + ".html"
        if check_only:
            print(("  ✅ " if os.path.exists(out) else "  ❌ ") + rel)
            continue
        md = io.open(p, encoding="utf-8").read()
        title = next((l.lstrip("# ").strip() for l in md.split("\n")
                      if l.strip().startswith("#")), os.path.basename(rel))
        body = render(md)
        page = PAGE % {"title": html.escape(title), "body": body,
                       "css": css_rel(rel), "home": home_rel(rel)}
        io.open(out, "w", encoding="utf-8").write(page)
        gen += 1
        print("  生成 %s" % os.path.relpath(out, ROOT))

    if check_only:
        return 0

    # ---- 把 HTML 页面里指向 .md 的链接改写成 .html ----
    fixed = [0]
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            if not f.endswith(".html"):
                continue
            hp = os.path.join(dp, f)
            s = io.open(hp, encoding="utf-8").read()
            o = s

            def fix(m, fixed=fixed):
                pre, u, post = m.group(1), m.group(2), m.group(3)
                if u.startswith(("http", "//", "#", "mailto:")):
                    return m.group(0)
                u2 = u.split("#")[0]
                if not u2.endswith(".md"):
                    return m.group(0)
                cand = os.path.normpath(os.path.join(dp, u2[:-3] + ".html"))
                if os.path.exists(cand):
                    fixed[0] += 1
                    return pre + u2[:-3] + ".html" + post + m.group(4)
                return m.group(0)

            s = re.sub(r'(href=["\'])([^"\']+\.md)((?:#[^"\']*)?)(["\'])', fix, s)
            # 防呆：任何被截断的 href（引号不配对）都视为失败
            import re as _r
            for _h in _r.findall(r'href="([^"]*)"', s):
                if '"' in _h or "<" in _h:
                    raise SystemExit("href 被截断：%r" % _h[:80])
            if s != o:
                io.open(hp, "w", encoding="utf-8").write(s)
                print("  改写链接 %s" % os.path.relpath(hp, ROOT))
    print("\n生成 %d 个 HTML，改写 %d 处 .md 链接" % (gen, fixed[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
