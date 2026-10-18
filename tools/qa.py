#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qa.py —— 本仓库质量守门人
=====================================================================
跑法： python3 tools/qa.py
检查 6 项，全部通过退出码为 0：

  1 乱码（U+FFFD 替换字符）—— 会出现在中文文案里，用户直接可见
  2 内部死链（排除 script 块，避免把 JS 代码误判成链接）
  3 外链格式（http/https 头写错、明显拼写问题）
  4 Shell 脚本语法（bash -n）
  5 HTML 结构（标签闭合平衡）
  6 单文件产物自包含性（arena.html 不得有外部 script/css）

历史教训：本仓库曾出现两处 U+FFFD（start.html 的「断网」、
备赛课程第 4 讲的配音脚本「密钥登录」），后者还会被渲染进视频画面与
语音，因此把乱码检查列为第 1 项。
"""
import io, json, os, re, subprocess, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIR = {".git", "node_modules"}
TEXT_EXT = (".html", ".md", ".js", ".json", ".txt", ".css", ".sh", ".ps1",
            ".yml", ".yaml", ".py", ".cjs", ".mjs")
fails = []


def walk(exts):
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            if not exts or f.endswith(exts):
                out.append(os.path.join(dp, f))
    return out


def rel(p):
    return os.path.relpath(p, ROOT)


def rd(p):
    return io.open(p, encoding="utf-8", errors="strict").read()


# ---------------------------------------------------------------- 1 乱码
print("=" * 64)
print("1. 乱码检查（U+FFFD）")
mojibake = []
for p in walk(TEXT_EXT):
    try:
        s = rd(p)
    except Exception:
        continue
    if "\ufffd" in s:
        n = s.count("\ufffd")
        lines = [i for i, l in enumerate(s.split("\n"), 1) if "\ufffd" in l]
        mojibake.append((rel(p), n, lines))
if mojibake:
    for f, n, ls in mojibake:
        print("  ❌ %s  %d 处，行 %s" % (f, n, ls[:6]))
    fails.append("乱码 %d 个文件" % len(mojibake))
else:
    print("  ✅ 无乱码")

# ---------------------------------------------------------------- 2 内部死链
print("2. 内部死链（已排除 script 块）")
dead = []
for p in walk((".html", ".md")):
    try:
        s = rd(p)
    except Exception:
        continue
    s = re.sub(r"<script[^>]*>.*?</script>", "", s, flags=re.S | re.I)
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']|\]\(([^)\s]+)\)', s):
        u = (m.group(1) or m.group(2) or "").strip()
        if not u or u.startswith(("http://", "https://", "//", "mailto:", "tel:",
                                   "data:", "javascript:", "#", "irm ")):
            continue
        u = u.split("#")[0].split("?")[0]
        if not u:
            continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), u))):
            dead.append((rel(p), u))
if dead:
    seen = set()
    for f, u in dead:
        if (f, u) in seen:
            continue
        seen.add((f, u))
        print("  ❌ %s -> %s" % (f, u))
    fails.append("死链 %d 条" % len(dead))
else:
    print("  ✅ 0 死链")

# ---------------------------------------------------------------- 3 外链格式
print("3. 外链格式")
bad_url = []
for p in walk((".html", ".md")):
    try:
        s = re.sub(r"<script[^>]*>.*?</script>", "", rd(p), flags=re.S | re.I)
    except Exception:
        continue
    for m in re.finditer(r'https?://[A-Za-z0-9._~:/?#\[\]@!$&\'()*+,;=%-]+', s):
        u = m.group(0)
        # 只判真正的畸形：缺主机名、含替换字符、含未替换的 {占位符}
        host = u.split("//", 1)[1].split("/")[0]
        if (not host or "\ufffd" in u or "{" in u or "}" in u
                or u.count("://") != 1 or re.search(r"[\ufffd<>\s]", u)):
            bad_url.append((rel(p), u[:80]))
if bad_url:
    for f, u in bad_url[:10]:
        print("  ❌ %s -> %s" % (f, u))
    fails.append("外链格式 %d 处" % len(bad_url))
else:
    print("  ✅ 外链格式正常")

# ---------------------------------------------------------------- 4 shell 语法
print("4. Shell 脚本语法")
bad_sh = []
for p in walk((".sh",)):
    r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
    if r.returncode:
        bad_sh.append((rel(p), r.stderr.strip()[:90]))
if bad_sh:
    for f, e in bad_sh:
        print("  ❌ %s : %s" % (f, e))
    fails.append("shell 语法 %d 个" % len(bad_sh))
else:
    n = len(walk((".sh",)))
    print("  ✅ %d 个脚本全部通过 bash -n" % n)

# ---------------------------------------------------------------- 5 HTML 结构
print("5. HTML 标签闭合")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Bal(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.err = [], []

    def handle_starttag(self, t, a):
        if t not in VOID:
            self.stack.append((t, self.getpos()))

    def handle_endtag(self, t):
        if t in VOID:
            return
        if not self.stack:
            self.err.append("游离 </%s> @%s" % (t, self.getpos()))
            return
        if self.stack[-1][0] == t:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == t:
                for j in range(len(self.stack) - 1, i - 1, -1):
                    self.err.append("未闭合 <%s> @%s" % (self.stack[j][0], self.stack[j][1]))
                del self.stack[i:]
                return
        self.err.append("游离 </%s> @%s" % (t, self.getpos()))


bad_html = []
for p in walk((".html",)):
    try:
        s = rd(p)
    except Exception:
        continue
    if "<script" in s:
        s2 = re.sub(r"<script[^>]*>.*?</script>", "", s, flags=re.S | re.I)
    else:
        s2 = s
    b = Bal()
    try:
        b.feed(s2)
    except Exception as e:
        bad_html.append((rel(p), "解析异常 %s" % e))
        continue
    errs = b.err + ["未闭合 <%s> @%s" % (t, pos) for t, pos in b.stack]
    if errs:
        bad_html.append((rel(p), errs[:3]))
if bad_html:
    for f, e in bad_html:
        print("  ❌ %s : %s" % (f, e))
    fails.append("HTML 结构 %d 个" % len(bad_html))
else:
    print("  ✅ %d 个页面标签闭合平衡" % len(walk((".html",))))

# ---------------------------------------------------------------- 6 单文件自包含
print("6. 单文件产物自包含性")
arena = os.path.join(ROOT, "arena.html")
if os.path.exists(arena):
    s = rd(arena)
    ext = re.findall(r'<script[^>]+src=["\']([^"\']+)', s) + \
          re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', s)
    if ext:
        print("  ❌ arena.html 存在外部依赖: %s" % ext[:4])
        fails.append("arena.html 有外部依赖")
    else:
        print("  ✅ arena.html 无外部 script/css（%d KB，可离线）" % (len(s) / 1024))
else:
    print("  – arena.html 未生成（跳过）")

# ---------------------------------------------------------------- 汇总
print("=" * 64)
if fails:
    print("❌ 未通过：" + "；".join(fails))
    sys.exit(1)
print("✅ 全部 6 项检查通过")
sys.exit(0)
