/* 真浏览器验收：直接打线上地址，抓控制台报错 + 截图 + 点一遍 + 验样式 */
const { chromium } = require("playwright");
const fs = require("fs");

const SITE = "https://taimabenji.github.io/cloud-computing-learning";
const SHOT = "/workspace/_shots";
fs.mkdirSync(SHOT, { recursive: true });

const fails = [];
const ok = (c, m) => { console.log((c ? "  ✅ " : "  ❌ ") + m); if (!c) fails.push(m); };

(async () => {
  // 沙箱出口是自签 CA 的 HTTPS 中间人代理，Chromium 默认不信任 → 显式放行
  const browser = await chromium.launch({ args: ["--ignore-certificate-errors"] });
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  const consoleErrs = [], pageErrs = [], failedReq = [];
  page.on("console", m => { if (m.type() === "error") consoleErrs.push(m.text().slice(0, 160)); });
  page.on("pageerror", e => pageErrs.push(String(e.message).slice(0, 160)));
  page.on("requestfailed", r => failedReq.push(r.url().slice(0, 90) + " :: " + (r.failure()||{}).errorText));
  page.on("response", r => { if (r.status() >= 400) failedReq.push(r.status() + " " + r.url().slice(0, 90)); });

  console.log("=== 1. 打开线上 arena.html ===");
  const resp = await page.goto(SITE + "/arena.html", { waitUntil: "load", timeout: 60000 });
  console.log("  HTTP", resp.status());
  ok(resp.status() === 200, "页面返回 200");
  await page.waitForTimeout(1200);

  console.log("=== 2. 控制台 / 资源报错 ===");
  ok(consoleErrs.length === 0, "控制台无 error（" + consoleErrs.length + "）");
  consoleErrs.slice(0, 5).forEach(e => console.log("      " + e));
  ok(pageErrs.length === 0, "无未捕获异常（" + pageErrs.length + "）");
  pageErrs.slice(0, 5).forEach(e => console.log("      " + e));
  ok(failedReq.length === 0, "无失败请求（" + failedReq.length + "）");
  failedReq.slice(0, 6).forEach(e => console.log("      " + e));

  console.log("=== 3. 样式真的生效了吗（computed style）===");
  const st = await page.evaluate(() => {
    const g = (sel, prop) => {
      const el = document.querySelector(sel);
      return el ? getComputedStyle(el)[prop] : null;
    };
    return {
      bodyBg: g("body", "backgroundColor"),
      bodyFont: g("body", "fontFamily").slice(0, 22),
      heroPad: g("header.hero", "paddingTop"),
      heroH: document.querySelector("header.hero")?.getBoundingClientRect().height || 0,
      ctaW: document.querySelector("#goLab")?.getBoundingClientRect().width || 0,
      ctaBg: g("#goLab", "backgroundColor"),
      topbarBg: g(".topbar", "backgroundColor"),
      wrapW: document.querySelector(".wrap")?.getBoundingClientRect().width || 0,
      papers: document.querySelectorAll("#papers .paper").length,
      bodyFontSize: g("body", "fontSize"),
      styledSheets: document.styleSheets.length,
      cssRules: (() => { try { return document.styleSheets[0].cssRules.length; } catch (e) { return -1; } })(),
    };
  });
  console.log("   ", JSON.stringify(st));
  ok(st.styledSheets >= 1 && st.cssRules > 100, "样式表已加载（规则数 " + st.cssRules + "）");
  ok(st.bodyBg && st.bodyBg !== "rgba(0, 0, 0, 0)" && st.bodyBg !== "transparent", "body 有背景色 " + st.bodyBg);
  ok(parseFloat(st.heroH) > 120, "标题区有实际高度 " + Math.round(st.heroH) + "px（未被 CSS 撑坏）");
  ok(st.ctaW > 300, "主按钮有宽度 " + Math.round(st.ctaW) + "px");
  ok(st.papers === 7, "试卷卡片 7 张");

  // 关键：正文不能是 CSS 源码
  // 注意：必须在**活的 DOM** 上取 innerText。cloneNode 出来的游离节点不套用 CSS，
  // 隐藏的试卷正文会被算进来，导致长度虚高。
  const bodyText = await page.evaluate(() =>
    document.body.innerText.replace(/\s+/g, " ").trim());
  ok(bodyText.length > 200 && bodyText.length < 4000,
     "可见正文长度合理 " + bodyText.length + " 字符（<4000 才说明没把隐藏内容当正文）");
  ok(!/display:|position:fixed|border-radius:|\.qz-item\{/.test(bodyText), "正文里没有 CSS 源码泄漏");
  ok(!/�/.test(bodyText), "正文无乱码");
  console.log("    正文开头：" + bodyText.slice(0, 70));

  await page.screenshot({ path: SHOT + "/01-home.png", fullPage: false });
  console.log("   📷 截图 01-home.png");

  console.log("=== 4. 点「先玩一下」进虚拟考场 ===");
  await page.click("#goLab");
  await page.waitForTimeout(900);
  const termOn = await page.evaluate(() => document.getElementById("termView").classList.contains("on"));
  ok(termOn, "终端打开");
  const termText = await page.evaluate(() => document.getElementById("tvScr").innerText);
  ok(termText.length > 20, "终端有输出：" + JSON.stringify(termText.slice(-60)));
  const termStyle = await page.evaluate(() => {
    const s = getComputedStyle(document.getElementById("termView"));
    return { bg: s.backgroundColor, disp: s.display, z: s.zIndex };
  });
  console.log("   ", JSON.stringify(termStyle));
  ok(termStyle.disp === "flex", "终端是 flex 布局（CSS 生效）");

  // 真的敲命令
  await page.click("#tvIn");
  await page.keyboard.type("whoami");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(400);
  await page.keyboard.type("ip a");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(400);
  const after = await page.evaluate(() => document.getElementById("tvScr").innerText);
  ok(/root/.test(after), "whoami 真的执行了");
  ok(/inet|eth0|127\./.test(after), "ip a 真的执行了");
  await page.screenshot({ path: SHOT + "/02-terminal.png" });
  console.log("   📷 截图 02-terminal.png");

  await page.click("#tvBack");
  await page.waitForTimeout(400);

  console.log("=== 5. 竞赛仿真场 + 里昂 52 评分点 ===");
  await page.click("#goComp");
  await page.waitForTimeout(800);
  const comps = await page.evaluate(() => document.querySelectorAll("#labBody [data-comp]").length);
  ok(comps === 5, "赛事卡片 " + comps + " 张");
  await page.click('#labBody [data-comp="ws-lyon24"]');
  await page.waitForTimeout(700);
  const rows = await page.evaluate(() => document.querySelectorAll("#labBody .cl-row").length);
  ok(rows === 52, "Module A 任务行 " + rows + " 行");
  const tid = await page.evaluate(() => document.querySelector("#labBody .cl-id")?.textContent);
  ok(tid === "task_A01_01", "首个编号 " + tid);
  await page.screenshot({ path: SHOT + "/03-competition.png" });
  console.log("   📷 截图 03-competition.png");

  console.log("=== 6. 限时模拟赛（真点确认框）===");
  await page.evaluate(() => window.closeLab());
  await page.waitForTimeout(300);
  await page.click("#goExam");
  await page.waitForTimeout(500);
  const confirmOn = await page.evaluate(() => document.getElementById("tvConfirm").classList.contains("on"));
  ok(confirmOn, "确认框弹出");
  await page.click("#tvConfirmYes");
  await page.waitForTimeout(800);
  const clock = await page.evaluate(() => { const e = document.getElementById("examClock"); return e ? e.textContent : null; });
  ok(/^\d\d:\d\d$/.test(clock || ""), "倒计时 " + clock);
  const c1 = clock;
  await page.waitForTimeout(2200);
  const c2 = await page.evaluate(() => document.getElementById("examClock")?.textContent);
  ok(c2 !== c1, "倒计时在走 " + c1 + " → " + c2);
  await page.screenshot({ path: SHOT + "/04-exam.png" });
  console.log("   📷 截图 04-exam.png");

  console.log("=== 7. 全真卷自评 ===");
  await page.evaluate(() => window.closeLab());
  await page.waitForTimeout(300);
  const chks = await page.evaluate(() => document.querySelectorAll("#papers [data-pk]").length);
  ok(chks === 331, "检查项 " + chks + " 条");
  await page.click("#papers .paper-h");
  await page.waitForTimeout(300);
  await page.evaluate(() => { const c = document.querySelectorAll("#papers [data-pk]")[0]; c.checked = true; c.dispatchEvent(new Event("change", { bubbles: true })); });
  await page.waitForTimeout(200);
  const w = await page.evaluate(() => document.getElementById("p-bar").style.width);
  ok(w && w !== "0%", "进度条动了 " + w);
  await page.screenshot({ path: SHOT + "/05-papers.png", fullPage: false });
  console.log("   📷 截图 05-papers.png");

  console.log("=== 8. 手机视口（iPhone 尺寸）===");
  const m = await ctx.newPage();
  await m.setViewportSize({ width: 390, height: 844 });
  await m.goto(SITE + "/arena.html", { waitUntil: "load", timeout: 60000 });
  await m.waitForTimeout(1000);
  const mv = await m.evaluate(() => {
    const b = document.body;
    return {
      overflowX: b.scrollWidth > window.innerWidth + 2 ? b.scrollWidth - window.innerWidth : 0,
      ctaW: document.querySelector("#goLab")?.getBoundingClientRect().width || 0,
      fontSize: getComputedStyle(document.body).fontSize,
      vis: (() => { const c = b.cloneNode(true); c.querySelectorAll("script,style").forEach(x => x.remove()); return c.innerText.replace(/\s+/g, " ").trim().slice(0, 50); })(),
    };
  });
  console.log("   ", JSON.stringify(mv));
  ok(mv.overflowX === 0, "无横向溢出（多出 " + mv.overflowX + "px）");
  ok(mv.ctaW > 300, "按钮在手机上仍是全宽 " + Math.round(mv.ctaW) + "px");
  ok(!/�/.test(mv.vis), "手机端无乱码");
  await m.screenshot({ path: SHOT + "/06-mobile.png" });
  console.log("   📷 截图 06-mobile.png");

  // 手机上进终端
  await m.click("#goLab"); await m.waitForTimeout(900);
  const mterm = await m.evaluate(() => {
    const t = document.getElementById("termView");
    const inp = document.getElementById("tvIn");
    return { on: t.classList.contains("on"), inpH: inp.getBoundingClientRect().height,
             fs: getComputedStyle(inp).fontSize, bottom: t.getBoundingClientRect().bottom };
  });
  console.log("   手机终端:", JSON.stringify(mterm));
  ok(mterm.on, "手机端终端可打开");
  ok(parseFloat(mterm.fs) >= 16, "输入框字号 " + mterm.fs + "（≥16px，iOS 不会自动放大）");
  ok(mterm.inpH >= 32, "输入框高度 " + Math.round(mterm.inpH) + "px，触控可用");
  await m.screenshot({ path: SHOT + "/07-mobile-terminal.png" });
  console.log("   📷 截图 07-mobile-terminal.png");

  console.log("=== 9. 其它页面（真浏览器逐页开）===");
  for (const p of ["index.html", "start.html", "linux-plan.html", "sim/index.html",
                   "setup/README.html", "labs/README.html", "week1.html", "sprint.html"]) {
    const e2 = [], ce = [];
    const pg = await ctx.newPage();
    pg.on("pageerror", x => e2.push(String(x.message).slice(0, 90)));
    pg.on("console", c => { if (c.type() === "error") ce.push(c.text().slice(0, 90)); });
    try {
      const r = await pg.goto(SITE + "/" + p, { waitUntil: "load", timeout: 45000 });
      await pg.waitForTimeout(700);
      const info = await pg.evaluate(() => {
        const b = document.body.cloneNode(true);
        b.querySelectorAll("script,style").forEach(x => x.remove());
        return { vis: b.innerText.replace(/\s+/g, " ").trim().length, bad: document.body.innerHTML.includes("�") };
      });
      const clean = e2.length === 0 && ce.length === 0 && info.vis > 30 && !info.bad;
      ok(clean, (p + "  HTTP " + r.status() + " 文本 " + info.vis + (e2.length ? " 异常:" + e2[0] : "") + (ce.length ? " 控制台:" + ce[0] : "")));
      await pg.screenshot({ path: SHOT + "/page-" + p.replace(/[\/\.]/g, "_") + ".png" });
    } catch (ex) {
      ok(false, p + " 打开失败：" + ex.message.slice(0, 60));
    }
    await pg.close();
  }

  await browser.close();
  console.log("\n" + "=".repeat(60));
  console.log(fails.length ? "❌ 真浏览器验收：" + fails.length + " 项失败" : "✅ 真浏览器验收：全部通过");
  fails.forEach(f => console.log("   - " + f));
  process.exit(fails.length ? 1 : 0);
})();
