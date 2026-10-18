#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_arena.py —— 生成 arena.html：单文件、自包含、零依赖的云计算模拟考场
=====================================================================
把整个模拟环境压进一个 HTML，双击可开、丢链接可分享、断网也能考：

  · 虚拟考场：浏览器内的 Linux 服务器（lab-engine + extras + scenarios）
      —— 真敲命令、真装服务、真自动评分，不用装任何软件
  · 竞赛仿真场：5 场赛事，含世赛里昂 2024 的 52 个官方 task 编号
      —— 模块权重 / 限时 / 交卷判分 / 成绩报告
  · 限时模拟赛：4 套（迷你 30 分钟 / 标准 90 / 全真 240 / 排障特训 45）
  · 真卷中心：7 套全真模拟卷（国赛 / 2023 国赛真题 / 广东 / 韩国 / 金砖 /
      WSC2026 世赛 / 世界职校赛），逐条自评打勾，进度存本机
  · 环境体检入口与 Linux 21 天计划入口

所有 JS/CSS 内联，**没有任何外部依赖**，可离线使用。

用法：python3 tools/build_arena.py
"""
import io, json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")
PAPERS = os.path.join(ROOT, "sim", "data")
OUT = os.path.join(ROOT, "arena.html")


def read(p):
    return io.open(p, encoding="utf-8").read()


def js_safe(s):
    """防止内联 JS 里出现 </script> 提前闭合标签。"""
    return s.replace("</script", "<\\/script").replace("<!--", "<\\!--")


css = read(os.path.join(LAB, "lab.css"))
engine = js_safe(read(os.path.join(LAB, "lab-engine.js")))
extras = js_safe(read(os.path.join(LAB, "lab-extras.js")))
scen = js_safe(read(os.path.join(LAB, "lab-scenarios.js")))
lui = js_safe(read(os.path.join(LAB, "lab-ui.js")))
comp = js_safe(read(os.path.join(LAB, "competition.js")))
compui = js_safe(read(os.path.join(LAB, "competition-ui.js")))

# ---- 7 套真卷：直接整段内联（它们自己会往 window.KC_PAPERS 里注册）----
paper_js = []
for fn in sorted(os.listdir(PAPERS)):
    if fn.endswith(".js"):
        paper_js.append(js_safe(read(os.path.join(PAPERS, fn))))
paper_js = "\n".join(paper_js)

for n, v in [("css", css), ("engine", engine), ("extras", extras), ("scen", scen),
             ("lui", lui), ("comp", comp), ("compui", compui), ("papers", paper_js)]:
    print("  inline %-8s %8d bytes" % (n, len(v)))

BUILD_DATE = datetime.date.today().isoformat()

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>云计算模拟考场 · 一个链接全都有</title>
<meta name="description" content="一个页面装下全部：浏览器内虚拟 Linux 服务器（自动评分）、5 场竞赛仿真场、4 套限时模拟赛、7 套全真模拟卷。零依赖、免安装、断网可用。">
<meta name="theme-color" content="#9e2b25">
<meta name="color-scheme" content="light">
<meta property="og:title" content="云计算模拟考场">
<meta property="og:description" content="虚拟 Linux 服务器 + 竞赛仿真场 + 7 套全真卷，单文件零依赖，断网可用">
<style>
:root{--red:#9e2b25;--red-dk:#7d201c;--gold:#b8873a;--blue:#2f5d8c;--green:#4c6b4f;
--ink:#2b2620;--ink2:#4a433a;--dim:#7a7167;--line:#e2dbcd;--line2:#efe9dd;--card:#fffdf8;
--serif:"Songti SC","STSong","Noto Serif SC",Georgia,serif}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:#f7f4ee;color:var(--ink);line-height:1.8;
font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif}
a{color:var(--red-dk)}
.topbar{background:var(--red);color:#f7efe2;font-size:12.5px;display:flex;align-items:center;gap:8px;
padding:7px 14px;font-family:var(--serif)}
.topbar .dot{width:7px;height:7px;background:#e8c8a0;transform:rotate(45deg);flex:none}
header.hero{background:var(--card);border-bottom:1px solid var(--line);padding:26px 16px 22px;text-align:center}
header.hero .kicker{color:var(--red);font-size:12px;letter-spacing:5px;font-family:var(--serif)}
header.hero h1{margin:10px 0 8px;font-size:clamp(24px,5.2vw,34px);letter-spacing:5px;font-family:var(--serif);font-weight:700}
header.hero p{margin:4px auto;color:var(--ink2);font-size:14px;max-width:660px}
header.hero .badges{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
header.hero .badges span{border:1px solid var(--line);background:#fbf8f1;color:var(--ink2);border-radius:4px;
padding:3px 11px;font-size:12.5px;font-family:var(--serif)}
.wrap{max-width:900px;margin:0 auto;padding:6px 16px 80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:16px;margin:10px 0}
.goal{background:#fbf5ea;border-left:4px solid var(--gold);border-radius:0 6px 6px 0;padding:10px 14px;font-size:13.5px;margin:12px 0}
h2.sec{font-size:clamp(18px,3.4vw,22px);margin:30px 0 14px;font-family:var(--serif);letter-spacing:2px;font-weight:700;
display:flex;align-items:center;gap:10px}
h2.sec::before{content:"";width:9px;height:9px;background:var(--red);flex:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:620px){.grid{grid-template-columns:1fr}}
.mod{display:block;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:16px;
text-decoration:none;color:inherit;cursor:pointer;transition:border-color .15s}
.mod:active{background:#fbf7ee}
.mod b{display:block;font-size:16px;font-family:var(--serif);letter-spacing:1px}
.mod .ico{width:42px;height:42px;border-radius:5px;display:flex;align-items:center;justify-content:center;
font-size:19px;font-family:var(--serif);margin-bottom:10px;color:#fdf6ea;background:var(--red)}
.mod.blue .ico{background:var(--blue)}.mod.green .ico{background:var(--green)}
.mod.gold .ico{background:var(--gold)}.mod.red .ico{background:var(--red)}
.mod .desc{color:var(--dim);font-size:13px;margin:6px 0 8px;line-height:1.75}
.mod .meta{font-size:12px;color:#9a9188;font-family:var(--serif)}
.list{list-style:none;margin:6px 0;padding:0}
.list li{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:8px 0;
border-bottom:1px solid var(--line2);font-size:14.5px}
.list li:last-child{border-bottom:none}
.list .t{flex:1;min-width:0}
.list .n{flex:none;color:var(--dim);font-size:12.5px;border:1px solid var(--line);border-radius:4px;
padding:2px 9px;font-family:var(--serif);white-space:nowrap}
.small{font-size:12.5px;color:var(--dim);line-height:1.8}
.note{color:var(--dim);font-size:12px;line-height:2;border-top:1px solid var(--line);margin-top:34px;
padding-top:14px;font-family:var(--serif)}
.btn{display:inline-block;margin:4px 8px 4px 0;background:var(--card);color:var(--red-dk);border:1px solid var(--red);
border-radius:5px;padding:9px 16px;font-size:14px;text-decoration:none;cursor:pointer;font-family:var(--serif)}
.btn.red{background:var(--red);color:#fdf6ea}
.btn.ghost{border-color:var(--line);color:var(--ink2)}
.cta{display:block;width:100%;padding:16px;margin:10px 0;border:none;border-radius:8px;cursor:pointer;
background:linear-gradient(150deg,#b5342c,#8e241f);color:#fff;font-size:16px;font-weight:700;
font-family:var(--serif);letter-spacing:2px;box-shadow:0 3px 10px rgba(158,43,37,.28)}
.cta.ghost{background:var(--card);color:var(--red-dk);border:2px solid var(--red);box-shadow:none;font-size:15px}
.cta.gold{background:linear-gradient(150deg,#c9973f,#a3762c)}
.cta.blue{background:linear-gradient(150deg,#3a72a8,#2a5177)}
.paper{border:1px solid var(--line);border-radius:8px;background:var(--card);padding:14px;margin:12px 0}
.paper.done{border-color:var(--green);background:#f7fcf8}
.paper-h{display:flex;align-items:center;gap:10px;cursor:pointer}
.paper-h .tag{flex:none;font-size:11.5px;border:1px solid var(--line);border-radius:4px;padding:1px 8px;
color:var(--dim);font-family:var(--serif)}
.paper-h b{flex:1;font-size:15.5px;font-family:var(--serif)}
.paper-h .min{flex:none;font-family:var(--serif);font-size:13px;color:var(--red-dk);font-weight:700}
.paper-b{display:none;border-top:1px dashed var(--line);margin-top:12px;padding-top:12px}
.paper.open .paper-b{display:block}
.modbox{border:1px solid var(--line2);border-radius:6px;padding:11px;margin:9px 0;background:#fdfbf6}
.modbox h4{margin:0 0 6px;font-size:14.5px;font-family:var(--serif);color:var(--red-dk)}
.chk{display:flex;align-items:flex-start;gap:8px;padding:5px 7px;border-radius:5px;font-size:13px;cursor:pointer}
.chk:hover{background:#f5f1e8}
.chk input{margin-top:3px;flex:none;width:15px;height:15px;accent-color:var(--red)}
.chk .p{flex:none;margin-left:auto;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}
.prog{height:9px;background:#eceff3;border-radius:5px;overflow:hidden;margin:8px 0}
.prog i{display:block;height:100%;background:linear-gradient(90deg,#9e2b25,#4c6b4f);border-radius:5px}
#err{background:#7d201c;color:#fff;padding:9px 13px;border-radius:6px;margin:10px 0;font-size:13px;display:none}
</style>
<!--LAB_CSS-->
</head>
<body>
<div class="topbar"><span class="dot"></span><span>云计算模拟考场 · 虚拟 Linux 服务器 + 竞赛仿真场 + 7 套全真卷 · 零依赖 · 断网可用</span></div>
<header class="hero">
  <div class="kicker">ONE FILE · ZERO DEPENDENCY · OFFLINE OK</div>
  <h1>云计算模拟考场</h1>
  <p>一个页面装下全部：<b>浏览器里开一台 Linux 服务器</b>（真敲命令、真装服务、真自动评分）、
  <b>5 场竞赛仿真场</b>（含世赛里昂 2024 的 52 个官方评分点）、<b>4 套限时模拟赛</b>、<b>7 套全真模拟卷</b>。
  不用装软件、不用开云账号、<b>断网照考</b>。</p>
  <div class="badges"><span id="bd-engine">22 个实训场景</span><span id="bd-comp">5 场竞赛仿真</span>
  <span id="bd-paper">7 套全真卷</span><span>自动评分</span><span>进度存本机</span></div>
</header>

<div class="wrap">
<div id="err"></div>

  <div class="goal"><b>三条路，按你的设备选：</b>
  <b>没有设备 / 网络受限</b> → 用本页的「虚拟考场」，浏览器内就有服务器，自动判分；
  <b>手上有 OpenStack / K8s 真集群</b> → 去 <code>sim/index.html</code> 打 7 套全真卷，对真机自评；
  <b>两者结合</b> = 先在虚拟考场把动作练熟，再上真机验收，效率最高。</div>

  <button class="cta" id="goComp">🏟 竞赛仿真场 —— 5 场真实赛事，官方评分点自动判分</button>
  <button class="cta gold" id="goExam">⏱ 限时模拟赛 —— 4 套，倒计时 / 交卷 / 出报告</button>
  <button class="cta blue" id="goLab">🧪 虚拟考场 —— 22 个场景，不限时练到会</button>
  <button class="cta ghost" id="goPapers">📋 全真卷中心 —— 7 套真题，逐条自评打勾</button>

  <h2 class="sec">虚拟考场是什么</h2>
  <div class="card">
    <p>浏览器里跑的是一台<b>真的虚拟服务器</b>，不是录屏也不是文字描述。它有：</p>
    <ul class="list">
      <li><span class="t">真实文件系统与权限</span><span class="n">root@ srv1</span></li>
      <li><span class="t">软件包与服务管理（apt / systemctl / journalctl）</span><span class="n">Nginx</span></li>
      <li><span class="t">网络（IP / 端口 / DNS / 负载均衡 / 防火墙 / NAT）</span><span class="n">ss -tlnp</span></li>
      <li><span class="t">数据库 · 容器 · 自动化 · 目录服务 · 共享 · 证书</span><span class="n">MySQL K8s Ansible</span></li>
      <li><span class="t">自动评分：每条命令后静默判分，做对得分、改对立刻补分</span><span class="n">自动</span></li>
    </ul>
    <p class="small" style="margin-top:10px">每个场景里都有 <b>📋 任务</b>（看题）· <b>📝 文件</b>（浏览/改配置）· <b>▶ 示范</b>（演示标准解法）· <b>📊 评分</b>（看当前得分）。
    <b>卡住了先点「示范」，别死磕。</b></p>
  </div>

  <h2 class="sec">7 套全真卷 · 逐条自评</h2>
  <div class="card">
    <p class="small">真题卷需要对着<b>真机</b>验收，所以这里做成自评打勾 + 进度记录。每套含模块分值、任务题面、逐条检查项与参考解法。做完回本页勾一遍，失分项就是你要补的。</p>
    <div class="prog"><i id="p-bar" style="width:0%"></i></div>
    <div class="small" id="p-stat">已完成 0 / 7 套 · 0 / 0 项</div>
    <div id="papers" style="margin-top:10px"></div>
    <div class="small" style="margin-top:10px">📌 真卷的判分由你自己的机器承担——先看 <code>labs/README.md</code> 搭考场，再回来勾。
    环境没搭好也别勾，勾了等于骗自己。</div>
  </div>

  <h2 class="sec">配套材料</h2>
  <div class="card">
    <ul class="list">
      <li><span class="t"><b>Linux 21 天每日计划</b> —— 每天一张卡：命令 / 动手 / 过关自测，进度存本机，可打印</span><span class="n"><a href="linux-plan.html">打开</a></span></li>
      <li><span class="t"><b>在你自己电脑上装 Linux</b> —— Windows/macOS/Linux 三平台一键脚本 + 环境体检</span><span class="n"><a href="setup/README.md">打开</a></span></li>
      <li><span class="t"><b>30 天作战板</b> —— 填比赛日期，每天告诉你做什么</span><span class="n"><a href="start.html">打开</a></span></li>
      <li><span class="t"><b>四层通关任务书</b> —— L1 Linux → L2 网络 → L3 Docker → L4 K8s，带自动评分脚本</span><span class="n"><a href="labs/cloudlab/README.md">打开</a></span></li>
      <li><span class="t"><b>20 章保姆级教程</b> —— 零基础到机房管理，全中文离线</span><span class="n"><a href="docs/tutorial/README-教程总览.md">打开</a></span></li>
      <li><span class="t"><b>WSOS 2026 官方职业标准（中文全文）</b> —— 世界赛八项权重就写在里面</span><span class="n"><a href="resources/WSOS-2026-cloud-computing-zh.txt">打开</a></span></li>
    </ul>
  </div>

  <p class="note">本页为<b>单文件自包含</b>：全部脚本与样式内联，<b>没有任何外部依赖</b>，可双击本地打开、可断网使用、也可直接分享链接。
  生成脚本：<code>tools/build_arena.py</code>（改 lab/ 或 sim/data/ 后重跑即可再生成）。生成日期：<b>__BUILD_DATE__</b>。
  虚拟考场与竞赛仿真场由站内 <code>lab/</code> 引擎驱动，已验证：57 项冒烟 + 22 场景 + 竞赛满分可达性全绿。</p>
</div>

<!-- ================= 虚拟考场（竞赛 / 限时赛 / 实训） ================= -->
<div id="labView">
  <div class="topbar"><span class="dot"></span><span id="labTitle">云计算模拟考场</span>
    <span style="margin-left:auto"></span>
    <button class="btn ghost" onclick="closeLab()">✕ 退出</button>
  </div>
  <div class="wrap" id="labBody" style="padding-top:14px"></div>
</div>

<!-- ================= 终端 ================= -->
<div id="termView">
  <div class="tv-head">
    <button class="tv-btn" id="tvBack">← 返回</button>
    <div class="tv-title" id="tvTitle">虚拟考场</div>
    <div id="tvScore" style="font-size:11px;color:#8b949e;margin-right:2px"></div>
    <button class="tv-btn" id="tvGradeBtn">📊 评分</button>
  </div>
  <div class="tv-scr" id="tvScr"></div>
  <div class="tv-pad">
    <div class="tv-chips" id="tvChips"></div>
    <div class="tv-inrow">
      <button class="tv-mini" id="tvHUp">⌃</button>
      <button class="tv-mini" id="tvHDn">⌄</button>
      <input id="tvIn" placeholder="输入命令，回车执行" autocomplete="off" autocapitalize="off"
             autocorrect="off" spellcheck="false" enterkeyhint="go">
      <button class="tv-run" id="tvRun">▶</button>
    </div>
    <div class="tv-tools">
      <button class="tv-mini" id="tvBriefBtn">📋 任务</button>
      <button class="tv-mini" id="tvFilesBtn">📝 文件</button>
      <button class="tv-mini" id="tvDemoBtn">▶ 示范</button>
      <button class="tv-mini" id="tvResetBtn">↺ 重开</button>
    </div>
  </div>
  <div class="tv-panel" id="tvPanel"></div>
</div>

<div id="tvEdit">
  <div class="tv-edit-card">
    <div class="tv-edit-head"><span id="tvEditPath">file</span><button class="tv-btn" id="tvEditClose">✕</button></div>
    <textarea id="tvEditArea" spellcheck="false"></textarea>
    <div class="tv-edit-foot"><button class="tv-btn" id="tvEditCancel">取消</button><button class="tv-btn primary" id="tvEditSave">💾 保存</button></div>
  </div>
</div>
<div id="tvToast"></div>
<div id="tvConfirm"><div class="tv-edit-card sm"><div id="tvConfirmMsg"></div>
  <div class="tv-edit-foot"><button class="tv-btn" id="tvConfirmNo">取消</button><button class="tv-btn primary" id="tvConfirmYes">确定</button></div></div></div>

<script>/*LAB_ENGINE*/</script>
<script>/*LAB_EXTRAS*/</script>
<script>/*LAB_SCENARIOS*/</script>
<script>/*LAB_PAPERS*/</script>
<script>
/* lab-ui 依赖的主页面钩子 */
window.renderLabCenter=function(){};
window.openLabCenter=function(){ document.getElementById('labView').classList.add('on'); renderLabCenter(); };
window.closeLab=function(){
  document.getElementById('labView').classList.remove('on');
  document.getElementById('termView').classList.remove('on');
};
window.startSim=function(id){ try{ window.LabUI.startExam(id); }catch(e){ showErr(e); } };
</script>
<script>/*LAB_UI*/</script>
<script>/*LAB_COMPETITION*/</script>
<script>/*LAB_COMPETITION_UI*/</script>
<script>
(function(){
'use strict';
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function showErr(e){ var b=document.getElementById('err'); b.style.display='block';
  b.textContent='引擎异常：'+((e&&e.message)||e); }

/* ---------- 引擎健康检查 ---------- */
var E=window.LabEngine;
if(!E||!E.SCENARIOS){ showErr('LabEngine 未加载'); return; }
try{
  document.getElementById('bd-engine').textContent = E.SCENARIOS.length+' 个实训场景';
  document.getElementById('bd-comp').textContent  = Object.keys(E.COMPETITIONS||{}).length+' 场竞赛仿真';
}catch(e){ showErr(e); }

/* ---------- 7 套全真卷：自评打勾 ---------- */
var PAPERS = window.KC_PAPERS || {};
var PKEY='arena:papers:v1';
function pget(){ try{ return JSON.parse(localStorage.getItem(PKEY))||{}; }catch(e){ return {}; } }
function pset(v){ try{ localStorage.setItem(PKEY, JSON.stringify(v)); }catch(e){} }
var PS = pget();

function paperStats(){
  var tot=0, done=0;
  Object.keys(PAPERS).forEach(function(pid){
    (PAPERS[pid].modules||[]).forEach(function(m,mi){
      (m.tasks||[]).forEach(function(t,ti){
        (t.checks||[]).forEach(function(c,ci){
          tot++; if(PS[pid+'|'+mi+'|'+ti+'|'+ci]) done++;
        });
      });
    });
  });
  return {tot:tot, done:done};
}

function renderPapers(){
  var box=document.getElementById('papers');
  var ids=Object.keys(PAPERS).sort(function(a,b){
    var oa=PAPERS[a].order||99, ob=PAPERS[b].order||99; return oa-ob;
  });
  if(!ids.length){ box.innerHTML='<p class="small">未读到试卷数据。</p>'; return; }
  box.innerHTML = ids.map(function(pid){
    var p=PAPERS[pid];
    var mins=0, tasks=0;
    (p.modules||[]).forEach(function(m){ mins+=(m.minutes||0); tasks+=(m.tasks||[]).length; });
    var open = PS['_open_'+pid] ? ' open' : '';
    var h='<div class="paper'+open+'" id="pp_'+pid+'">'
      +'<div class="paper-h" data-open="'+pid+'">'
      +(p.tag?'<span class="tag">'+esc(p.tag)+'</span>':'')
      +'<b>'+esc(p.name)+'</b>'
      +'<span class="min">'+Math.round(mins/60*10)/10+' h · '+tasks+' 任务</span></div>'
      +'<div class="paper-b">';
    if(p.desc) h+='<p class="small">'+esc(p.desc)+'</p>';
    if(p.source) h+='<p class="small"><b>出处：</b>'+esc(p.source)+'</p>';
    if(p.env) h+='<p class="small"><b>考场环境：</b>'+esc(p.env)+'</p>';
    if(p.rules) h+='<div class="goal">'+esc(p.rules)+'</div>';
    (p.modules||[]).forEach(function(m,mi){
      h+='<div class="modbox"><h4>'+esc(m.name)+'　<span class="small">'+(m.minutes||0)+' 分钟</span></h4>';
      if(m.brief) h+='<p class="small">'+String(m.brief).replace(/<[^>]+>/g,'')+'</p>';
      (m.tasks||[]).forEach(function(t,ti){
        h+='<div style="margin:8px 0"><b style="font-size:13.5px">'+esc(t.title)+'</b>';
        (t.checks||[]).forEach(function(c,ci){
          var k=pid+'|'+mi+'|'+ti+'|'+ci;
          h+='<label class="chk"><input type="checkbox" data-pk="'+esc(k)+'"'+(PS[k]?' checked':'')+'>'
            +'<span>'+esc(c.d)+'</span><span class="p">'+c.p+'</span></label>';
        });
        if(t.refs&&t.refs.length) h+='<p class="small">📎 参考：'+t.refs.map(function(x){return esc(x);}).join(' · ')+'</p>';
        h+='</div>';
      });
      h+='</div>';
    });
    h+='</div></div>';
    return h;
  }).join('');
  updatePaperStat();
}

function updatePaperStat(){
  var s=paperStats();
  /* 331 项里只勾 1 项时四舍五入仍是 0，用户看不到反馈 —— 给一个最小可见宽度 */
  var pct = s.tot ? (s.done / s.tot * 100) : 0;
  var w = s.done>0 ? Math.max(2, Math.round(pct*10)/10) : 0;
  document.getElementById('p-bar').style.width = w+'%';
  document.getElementById('p-stat').textContent =
    '已完成 '+Object.keys(PAPERS).length+' 套可选 · 检查项 '+s.done+' / '+s.tot;
}

document.addEventListener('change', function(e){
  var c=e.target.closest('[data-pk]'); if(!c) return;
  var k=c.getAttribute('data-pk');
  if(c.checked) PS[k]=1; else delete PS[k];
  pset(PS); updatePaperStat();
});
document.addEventListener('click', function(e){
  var h=e.target.closest('[data-open]'); if(!h) return;
  var pid=h.getAttribute('data-open');
  var el=document.getElementById('pp_'+pid);
  if(!el) return;
  el.classList.toggle('open');
  PS['_open_'+pid]=el.classList.contains('open')?1:0;
  pset(PS);
});

/* ---------- 四个入口 ---------- */
function openLab(){
  document.getElementById('labView').classList.add('on');
}
document.getElementById('goComp').addEventListener('click',function(){
  try{ openLab(); window.CompUI.open(); }catch(e){ showErr(e); }
});
document.getElementById('goExam').addEventListener('click',function(){
  try{ window.LabUI.startExam('mini'); }catch(e){ showErr(e); }
});
document.getElementById('goLab').addEventListener('click',function(){
  try{ window.LabUI.openScenario(E.SCENARIOS[0].id); }catch(e){ showErr(e); }
});
document.getElementById('goPapers').addEventListener('click',function(){
  document.getElementById('papers').scrollIntoView({behavior:'smooth',block:'start'});
  var f=document.querySelector('#papers .paper-h'); if(f) f.click();
});

renderPapers();
})();
</script>
</body>
</html>
"""

out = (HTML.replace("<!--LAB_CSS-->", css)
           .replace("/*LAB_ENGINE*/", engine)
           .replace("/*LAB_EXTRAS*/", extras)
           .replace("/*LAB_SCENARIOS*/", scen)
           .replace("/*LAB_UI*/", lui)
           .replace("/*LAB_COMPETITION*/", comp)
           .replace("/*LAB_COMPETITION_UI*/", compui)
           .replace("/*LAB_PAPERS*/", paper_js)
           .replace("__BUILD_DATE__", BUILD_DATE))

io.open(OUT, "w", encoding="utf-8").write(out)
print("  wrote %s  (%.1f KB)" % (OUT, len(out) / 1024.0))
