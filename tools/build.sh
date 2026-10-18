#!/bin/bash
# 构建顺序不能反：arena.html 先由引擎拼装，md2html 再把其中的 .md 链接改成 .html
set -e
cd "$(dirname "$0")/.."
echo "==> 1/3 生成 arena.html"
python3 tools/build_arena.py
echo "==> 2/3 生成 Markdown 的 HTML 版本并改写链接"
python3 tools/md2html.py | tail -3
echo "==> 3/3 质量体检"
python3 tools/qa.py | tail -3

# 可选：真浏览器验收（需 playwright，对线上地址跑）
#   npm i playwright && npx playwright install chromium
#   node tools/live/live_check.cjs
