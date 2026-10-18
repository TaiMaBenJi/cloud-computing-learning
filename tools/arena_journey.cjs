/* arena.html 深度旅程测试：模拟真实用户的完整操作路径，找运行时错误 */
const fs=require("fs"); const {JSDOM}=require("jsdom");
const F="/workspace/ccl/arena.html";
let fail=0; const errs=[];
const ok=(c,m)=>{ if(!c){console.log("  ❌ "+m); fail++;} else console.log("  ✅ "+m); };

const html=fs.readFileSync(F,"utf8");
const dom=new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url:"https://x.com/arena.html"});
const w=dom.window,d=dom.window.document;
// 捕获未捕获异常 —— 这是 jsdom 之前漏掉的
w.addEventListener("error",e=>errs.push("window.onerror: "+(e.error&&e.error.message||e.message)));
w.onerror=(m,s,l)=>errs.push("onerror: "+m+" @"+l);

const wait=ms=>new Promise(r=>setTimeout(r,ms));
const vis=id=>d.getElementById(id).classList.contains("on");
function typeIn(cmd){
  const i=d.getElementById("tvIn");
  i.value=cmd;
  i.dispatchEvent(new w.KeyboardEvent("keydown",{key:"Enter",bubbles:true}));
}
function clickIn(sel){
  const el=d.querySelector(sel);
  if(!el){ errs.push("找不到元素: "+sel); return false; }
  el.dispatchEvent(new w.MouseEvent("click",{bubbles:true}));
  return true;
}

(async()=>{
  await wait(800);
  console.log("=== A. 落地页初始状态 ===");
  ok(d.querySelectorAll("#papers .paper").length===7,"7 张试卷卡片");
  ok(d.getElementById("err").style.display!=="block","无初始错误："+d.getElementById("err").textContent.slice(0,60));
  ok(!vis("labView"),"考场面板默认关闭");
  ok(!vis("termView"),"终端默认关闭");

  console.log("=== B. 虚拟考场：连续 3 个场景往返 ===");
  const scns=["web1","dns1","ha1"];
  for(const id of scns){
    w.LabUI.openScenario(id);
    await wait(150);
    ok(vis("termView"),"打开场景 "+id);
    const scr=d.getElementById("tvScr").textContent;
    ok(scr.length>20,"场景 "+id+" 有环境输出");
    typeIn("whoami"); await wait(80);
    typeIn("id"); await wait(80);
    ok(/root/.test(d.getElementById("tvScr").textContent),"场景 "+id+" 能敲命令");
    d.getElementById("tvBack").click(); await wait(150);
    ok(!vis("termView"),"从 "+id+" 返回后终端关闭");
  }

  console.log("=== C. 任务/文件/示范/重开 四个工具按钮 ===");
  w.LabUI.openScenario("web1"); await wait(150);
  d.getElementById("tvBriefBtn").click(); await wait(100);
  ok(d.getElementById("tvPanel").classList.contains("on"),"📋 任务面板打开");
  ok(d.getElementById("tvPanel").textContent.length>10,"任务面板有内容");
  d.getElementById("tvBriefBtn").click(); await wait(100);
  ok(!d.getElementById("tvPanel").classList.contains("on"),"再次点击关闭任务面板");
  d.getElementById("tvFilesBtn").click(); await wait(100);
  ok(d.getElementById("tvPanel").classList.contains("on"),"📝 文件面板打开");
  d.getElementById("tvFilesBtn").click(); await wait(100);
  d.getElementById("tvDemoBtn").click(); await wait(400);
  ok(d.getElementById("tvScr").textContent.length>60,"▶ 示范有输出");
  d.getElementById("tvResetBtn").click(); await wait(150);
  ok(d.getElementById("tvConfirm").classList.contains("on"),"↺ 重开弹出确认");
  d.getElementById("tvConfirmYes").click(); await wait(200);
  ok(!d.getElementById("tvConfirm").classList.contains("on"),"确认后重置");

  console.log("=== D. 限时模拟赛完整流程 ===");
  d.getElementById("tvBack").click(); await wait(150);
  d.getElementById("goExam").click(); await wait(200);
  ok(d.getElementById("tvConfirm").classList.contains("on"),"开考有确认框");
  d.getElementById("tvConfirmYes").click(); await wait(400);
  ok(vis("labView"),"考试面板打开");
  const clock=d.getElementById("examClock");
  ok(!!clock && /^\d\d:\d\d$/.test(clock.textContent.trim()),"倒计时："+(clock?clock.textContent:"无"));
  const t1=clock.textContent;
  await wait(2100);
  ok(d.getElementById("examClock").textContent!==t1,"倒计时在走动："+t1+" -> "+d.getElementById("examClock").textContent);
  ok(d.getElementById("tvExamClock")!==null,"终端标题栏也有倒计时");
  // 进入任务
  const taskBtn=d.querySelector("#labBody [data-open], #labBody .qz-item button, #labBody [data-scn]");
  if(taskBtn){ taskBtn.dispatchEvent(new w.MouseEvent("click",{bubbles:true})); await wait(300); }
  ok(vis("termView"),"考试中可进入任务终端");
  typeIn("uptime"); await wait(100);

  console.log("=== E. 竞赛仿真场：三模块切换 + 报告 ===");
  w.closeLab(); await wait(150);
  d.getElementById("goComp").click(); await wait(400);
  ok(vis("labView"),"仿真场打开");
  d.querySelector('#labBody [data-comp="cn-prov"]').click(); await wait(400);
  const tabs=d.querySelectorAll("#labBody [data-tab]");
  ok(tabs.length>=3,"模块 tab "+tabs.length+" 个");
  for(let i=0;i<tabs.length;i++){
    d.querySelectorAll("#labBody [data-tab]")[i].click(); await wait(200);
    ok(d.getElementById("labBody").textContent.length>50,"切到模块 "+(i+1)+" 有内容");
  }
  clickIn('#labBody [data-act="report"]'); await wait(300);
  const rep=d.getElementById("labBody").textContent;
  ok(/成绩报告/.test(rep),"报告页渲染");
  ok(/WSOS/.test(rep),"含 WSOS 对照");
  ok(/失分点|全部达标/.test(rep),"含失分点或满分提示");
  // 报告页必须能回到考场（这是真实用户最容易卡死的点）
  ok(d.getElementById("lvBackReport")!==null,"报告页有「返回考场」");
  ok(d.getElementById("lvGoT1")!==null,"报告页有计时开关");
  clickIn('#lvGoT1'); await wait(300);
  ok(d.getElementById("lvBackReport")!==null,"报告页内开关计时后仍停在报告页");
  ok(/暂停计时/.test(d.getElementById("labBody").textContent),"报告页按钮已切为「暂停计时」");
  clickIn('#lvBackReport'); await wait(300);
  ok(d.querySelectorAll("#labBody [data-tab]").length>0,"返回后模块 tab 回来了（不再是死胡同）");
  ok(d.getElementById("compClock")!==null,"考场内时钟显示："+(d.getElementById("compClock")?d.getElementById("compClock").textContent:"无"));
  clickIn('#labBody [data-act="timer"]'); await wait(300);
  ok(d.getElementById("compClock")===null,"再点计时器=停止，时钟消失");
  clickIn('#labBody [data-act="report"]'); await wait(250);
  ok(/开始计时/.test(d.getElementById("labBody").textContent),"报告页状态与考场一致（已停）");

  console.log("=== F. 真卷：逐套展开 + 打勾 ===");
  w.closeLab(); await wait(150);
  const heads=d.querySelectorAll("#papers .paper-h");
  ok(heads.length===7,"7 个试卷头");
  let opened=0;
  for(let i=0;i<heads.length;i++){
    heads[i].dispatchEvent(new w.MouseEvent("click",{bubbles:true})); await wait(60);
    const card=d.querySelectorAll("#papers .paper")[i];
    if(card.classList.contains("open")) opened++;
    const txt=card.querySelector(".paper-b").textContent;
    if(txt.length<50) errs.push("试卷 "+i+" 展开后内容过少: "+txt.length);
  }
  ok(opened===7,"7 套全部可展开（"+opened+"/7）");
  const allChk=d.querySelectorAll("#papers [data-pk]");
  ok(allChk.length===331,"检查项 331 条（实际 "+allChk.length+"）");
  // 全选第一套
  let n=0;
  allChk.forEach((c,i)=>{ if(i<40){ c.checked=true; c.dispatchEvent(new w.Event("change",{bubbles:true})); n++; } });
  await wait(100);
  ok(d.getElementById("p-bar").style.width!=="0%","批量勾选后进度条前进："+d.getElementById("p-bar").style.width);

  console.log("=== G. 关闭与再开 ===");
  w.closeLab(); await wait(150);
  ok(!vis("labView"),"closeLab 关闭面板");
  d.getElementById("goLab").click(); await wait(250);
  ok(vis("termView"),"关闭后可再打开考场");

  console.log("");
  console.log("=== 运行时错误 ===");
  if(errs.length){ errs.slice(0,10).forEach(e=>console.log("  ⚠ "+e)); }
  ok(errs.length===0,"无未捕获异常（"+errs.length+" 个）");
  ok(d.getElementById("err").style.display!=="block","页面无错误横幅："+d.getElementById("err").textContent.slice(0,80));

  console.log("");
  console.log(fail?("❌ 深度旅程："+fail+" 项失败"):"✅ 深度旅程：全部通过");
  process.exit(fail?1:0);
})().catch(e=>{ console.log("测试脚本自身异常:",e.message); process.exit(2); });
