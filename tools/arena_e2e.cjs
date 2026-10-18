/* arena.html 端到端测试（jsdom 驱动真实 UI） */
const fs=require("fs"); const {JSDOM}=require("jsdom");
const F="/workspace/ccl/arena.html";
let fail=0; const ok=(c,m)=>{console.log((c?"  ✅ ":"  ❌ ")+m); if(!c)fail++;};

console.log("=== 1. 加载 ===");
const html=fs.readFileSync(F,"utf8");
const dom=new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url:"https://x.com/arena.html"});
const w=dom.window,d=dom.window.document;

setTimeout(()=>{
  console.log("=== 2. 引擎 ===");
  ok(!!w.LabEngine,"LabEngine 加载");
  ok(!!w.LabUI,"LabUI 加载");
  ok(w._labUIBound===1,"UI 绑定 DOM（_labUIBound="+w._labUIBound+"）");
  if(w._labInitErr){ console.log("     initErr: "+w._labInitErr); fail++; }
  ok(w.LabEngine.SCENARIOS.length===22,"实训场景 "+w.LabEngine.SCENARIOS.length+" 个");
  ok(Object.keys(w.LabEngine.COMPETITIONS||{}).length===5,"竞赛仿真 "+Object.keys(w.LabEngine.COMPETITIONS||{}).length+" 场");
  ok(!!w.LabEngine.extras,"extras 已装载（sysctl/iptables/wg/squid/postfix/x509）");

  console.log("=== 3. 全真卷 ===");
  const P=w.KC_PAPERS||{};
  ok(Object.keys(P).length===7,"试卷 "+Object.keys(P).length+" 套（期望 7）");
  const names=Object.keys(P).map(k=>P[k].name);
  console.log("     "+names.map(n=>n.slice(0,18)).join(" / "));
  d.getElementById("bd-paper").textContent=Object.keys(P).length+" 套全真卷";

  const cards=d.querySelectorAll("#papers .paper");
  ok(cards.length===7,"试卷卡片渲染 "+cards.length+" 张");
  const chks=d.querySelectorAll("#papers [data-pk]");
  ok(chks.length>100,"检查项渲染 "+chks.length+" 条");

  console.log("=== 4. 自评打勾与持久化 ===");
  ok(/已完成/.test(d.getElementById("p-stat").textContent),"统计行："+d.getElementById("p-stat").textContent);
  const before=d.getElementById("p-bar").style.width;
  chks[0].checked=true; chks[0].dispatchEvent(new w.Event("change",{bubbles:true}));
  ok(d.getElementById("p-bar").style.width!==before,"进度条前进："+before+" -> "+d.getElementById("p-bar").style.width);
  ok(w.localStorage.getItem("arena:papers:v1")!==null,"localStorage 已持久化");
  d.querySelector("#papers .paper-h").click();
  ok(d.querySelector("#papers .paper").classList.contains("open"),"试卷可展开");

  console.log("=== 5. 虚拟考场 ===");
  d.getElementById("goLab").click();
  setTimeout(()=>{
    ok(d.getElementById("termView").classList.contains("on"),"终端已打开");
    const inp=d.getElementById("tvIn");
    const t0=d.getElementById("tvScr").textContent;
    inp.value="whoami"; inp.dispatchEvent(new w.KeyboardEvent("keydown",{key:"Enter",bubbles:true}));
    ok(d.getElementById("tvScr").textContent!==t0,"命令有输出");
    ok(/root/.test(d.getElementById("tvScr").textContent),"whoami 返回 root");
    d.getElementById("tvGradeBtn").click();
    ok(d.getElementById("tvPanel").classList.contains("on"),"评分面板打开");

    console.log("=== 6. 竞赛仿真场 ===");
    w.closeLab();
    d.getElementById("goComp").click();
    setTimeout(()=>{
      ok(!!w.CompUI,"CompUI 可用");
      const cc=d.querySelectorAll("#labBody [data-comp]");
      ok(cc.length===5,"赛事卡片 "+cc.length+" 张");
      d.querySelector('#labBody [data-comp="ws-lyon24"]').click();
      setTimeout(()=>{
        const rows=d.querySelectorAll("#labBody .cl-row");
        ok(rows.length===52,"里昂2024 Module A 任务行 "+rows.length+" 行");
        const ids=[...d.querySelectorAll("#labBody .cl-id")].map(e=>e.textContent);
        ok(ids.includes("task_A01_01")&&ids.includes("task_A16_05"),"官方 task 编号原样呈现");

        console.log("=== 7. 自包含 ===");
        ok(!/<script[^>]+src=/.test(html),"无外部 <script src>");
        ok(!/<link[^>]+stylesheet/.test(html),"无外部 CSS");
        ok(!/https?:\/\/[^"']*\.(js|css)(?!\w)/.test(html.replace(/https?:\/\/[a-z0-9.-]*github[^"'\s]*/g,"")),"无远程 JS/CSS 引用");
        ok(html.length>300000,"单文件体积 "+(html.length/1024).toFixed(0)+"KB");

        console.log("");
        console.log(fail?("❌ "+fail+" 项失败"):"✅ arena.html 端到端：全部通过");
        process.exit(fail?1:0);
      },400);
    },400);
  },400);
},700);
