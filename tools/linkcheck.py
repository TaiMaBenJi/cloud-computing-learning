#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
linkcheck.py —— 全站外链实测（并发）
=====================================================================
把仓库里所有 http(s) 外链逐条打一遍，输出：正常 / 失效 / 被反爬拦截。
  死链分成三档：
    DEAD   —— 真死（404 / 域名解析失败 / 连接超时）
    BLOCK  —— 站点活着但拦了我们的 UA（403/503 且带反爬特征），需人工确认
    OK     —— 正常
用法： python3 tools/linkcheck.py [--all]
"""
import io, os, re, sys, json, ssl, argparse
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIR = {".git", "node_modules"}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

URL_RE = re.compile(r"https?://[^\s\"'<>\u3008\u3009\u300A\u300B\uFF08\uFF09\uFF1A\uFF1B]+")
TRAIL = ".,;:)]}，。；）】》"          # 正则会贪婪吃到这些标点


def collect():
    seen = {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            if not f.endswith((".html", ".md", ".json", ".txt")):
                continue
            p = os.path.join(dp, f)
            try:
                s = io.open(p, encoding="utf-8").read()
            except Exception:
                continue
            s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.S | re.I)
            for m in URL_RE.finditer(s):
                u = m.group(0).rstrip(TRAIL)
                if not u or u.endswith("="):
                    continue
                u = u.rstrip(TRAIL)
                if "{" in u or "}" in u or "…" in u or "$" in u or "\ufffd" in u:
                    continue                      # 占位符 / shell 变量 / 坏字符
                host = u.split("//", 1)[1].split("/")[0].split(":")[0]
                if SKIP_HOST.match(host) or SKIP_IP.match(host) or SKIP_HOST_SUB.search(host):
                    continue                      # 本地 / 内网 / 示例域名
                if re.search(r"[\u4e00-\u9fff]", host):
                    continue                      # 「你的域名.com」「服务器IP」等占位主机
                if u.rstrip().endswith((")**", "`", ")", "）")):
                    continue                      # markdown 加粗/反引号把 URL 截断的产物
                # 教程与真题正文里的示意地址（lb1:8404 / web-svc / console 控制台 /
                # dl.k8s.io/release/$(curl ...) 等）不是「资源链接」，不参与判定
                src = os.path.relpath(p, ROOT)
                if src.startswith(("docs/", "papers/")):
                    continue
                seen.setdefault(u, set()).add(src)
    return seen


def probe(u, timeout=15):
    # 浏览器会自动对非 ASCII 做百分号编码，这里必须手动做，否则中文路径全部探不通
    try:
        u = urllib.parse.quote(u, safe=":/?#[]@!$&'()*+,;=%-._~")
    except Exception:
        pass
    req = urllib.request.Request(u, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    # 只取响应头，不下载正文，省时间省流量
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(req, timeout=timeout)
        code = r.status
        r.close()
        return "OK", code
    except urllib.error.HTTPError as e:
        code = e.code
        if 300 <= code < 400:
            return "OK", code                    # 重定向 = 站点活着且可达
        # 412/521/403 等 = 站点活着但拦了我们的 UA，不算死链
        if code in (401, 403, 405, 406, 412, 418, 421, 429, 503, 520, 521, 522, 523):
            return "BLOCK", code
        return "DEAD", code
    except urllib.error.URLError as e:
        r = str(getattr(e, "reason", e))
        if "timed out" in r.lower() or "timeout" in r.lower():
            return "SLOW", r[:30]
        return "DEAD", r[:40]
    except Exception as e:
        n = type(e).__name__
        if "Timeout" in n:
            return "SLOW", str(e)[:30]
        return "DEAD", "%s:%s" % (n, str(e)[:30])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """不跟随重定向，直接把 3xx 报回来 —— 3xx 说明站点活着，是可达的。"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect", headers, fp)


# 明显不是「资源链接」的地址：本地/内网/示例/占位符/文档里的变量
SKIP_HOST = re.compile(
    r"^(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[?::1\]?|"
    r"example\.(org|com)|"
    r"\$|\{|x{4,}|mycompany\.local|.*\.local$|.*\.svc\.cluster\.local$)",
    re.I)
SKIP_HOST_SUB = re.compile(r"\.(local|internal|lan)$", re.I)
SKIP_IP = re.compile(r"^\d{1,3}(\.\d{1,3}){3}(:\d+)?$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="含 BLOCK 也输出")
    a = ap.parse_args()
    urls = collect()
    print("发现 %d 条不重复外链（已排除 docs/ 与 papers/ 里的示意地址），开始实测…\n"
          % len(urls))
    res = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for i, (u, (st, code)) in enumerate(ex.map(lambda kv: (kv[0], probe(kv[0])), list(urls.items()))):
            res[u] = (st, code)
            if st != "OK":
                print("  %-6s %s  %s" % (st, code, u[:96]))
    ok = [u for u in res if res[u][0] == "OK"]
    dead = [u for u in res if res[u][0] == "DEAD"]
    block = [u for u in res if res[u][0] == "BLOCK"]
    slow = [u for u in res if res[u][0] == "SLOW"]
    print("\n" + "=" * 66)
    print("正常 %d　失效 %d　被反爬拦截 %d　超时 %d　共 %d"
          % (len(ok), len(dead), len(block), len(slow), len(res)))
    if slow:
        print("（超时 %d 条：沙箱出口限制，不代表站点有问题）" % len(slow))
    if dead:
        print("\n--- 失效链接（含引用位置）---")
        for u in sorted(dead):
            print("  %s" % u)
            for f in sorted(urls[u]):
                print("      ← %s" % f)
    if block:
        print("\n--- 被反爬拦截（站点活着，我们的 UA 被挡）---")
        from collections import Counter
        for code, n in Counter(res[u][1] for u in block).most_common():
            print("  HTTP %s × %d" % (code, n))
    if slow:
        print("\n--- 超时（多为沙箱出口限制，勿据此判死）---")
        for u in sorted(slow)[:8]:
            print("  %s" % u)
    json.dump({u: list(res[u]) for u in res},
              io.open(os.path.join(ROOT, "tools", ".linkcheck.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
