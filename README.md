# 云计算 · 竞赛学习项目

> **零基础 → 省赛 → 国赛 → 世赛**，一条能直接照着跑的云计算备赛线。
> 30 天作战板 · 7 套全真模拟卷 · 21 套公开真题 · 一键实验环境 · 20 章保姆级教程

<p>
<img alt="零基础可入" src="https://img.shields.io/badge/零基础-可入-2b5cd9">
<img alt="7 套全真卷" src="https://img.shields.io/badge/全真模拟卷-7 套-0f9d6c">
<img alt="21 套真题" src="https://img.shields.io/badge/公开真题-21 套-b26a00">
<img alt="完全离线" src="https://img.shields.io/badge/内容-完全离线-9e2b25">
</p>

---

## 这是什么

不是资料堆，是一套**能直接执行**的云计算学习项目：

- 🎯 **给第一次参赛的人**：填上比赛日期，30 天作战板每天告诉你「今天做什么」
- 📝 **给要拿分的人**：7 套全真模拟卷 + 计时执行器 + 逐项评分，像真比赛一样打
- 🧪 **给要动手的人**：OpenStack / Kubernetes 一键实验脚本 + 四层通关任务书
- 📚 **给想系统学的人**：20 章保姆级教程 + 官方职业标准中文版 + 21 套真题题库

## 🚀 三步开始

1. **打开 [30 天作战板](start.html)** —— 填上你的比赛日期，看今天该做什么
2. **照 Day 1 做** —— 装一台 Linux（Ubuntu/CentOS 虚拟机或云主机都行）
3. **每周末打一卷** —— 打开 [模拟中心](sim/index.html)，计时、评分、复盘

> 不想装环境？直接看 [教程](docs/tutorial/README-教程总览.md) 和 [真题题库](papers/真题题库-21套.md)，纸上也能先入门。

## 📁 目录结构

| 目录 / 文件 | 内容 |
|---|---|
| [`start.html`](start.html) | **首赛倒计时 · 30 天作战板**（倒计时 + 逐日任务 + 打勾进度） |
| [`week1.html`](week1.html) | 七天开蒙卡（零基础第一周） |
| [`sprint.html`](sprint.html) | 30 天冲刺手册（完整版方法论） |
| [`sim/`](sim/index.html) | **全赛模拟中心**：7 套全真卷 + [计时执行器](sim/sim.html) |
| [`labs/`](labs/README.md) | 真机考场：环境三路线 + OpenStack/K8s 一键脚本 |
| [`labs/cloudlab/`](labs/cloudlab/README.md) | 四层通关任务书（L1 Linux → L4 K8s）+ 自动评分脚本 |
| [`docs/tutorial/`](docs/tutorial/README-教程总览.md) | 20 章保姆级教程（Linux/网络/服务/Docker/K8s/AWS/排障/安全…） |
| [`papers/`](papers/真题题库-21套.md) | **21 套公开真题题库** + 韩国世赛真题中译（2021–2025） |
| [`papers/korea-zh/`](papers/korea-zh/) | 韩国全国技能大赛云计算真题（题面 + 评分标准，中译） |
| [`resources/`](resources/) | 官方标准：WSOS 2026 中文全文 · TD53 中文导读与英文原件 · 金砖规程 |

## 🏆 7 套全真模拟卷（`sim/`）

| 卷 | 依据 | 适合 |
|---|---|---|
| 省赛真题卷 · 2024 广东样题① | 公开赛卷原文 | 第一套全真 |
| 国赛结构卷 · GZ075 三模块 | 2023 国赛公开分值结构 | 主赛道 |
| **国赛真题卷 · 2023 赛卷 1** | 公开赛卷原文收录 | 冲金 |
| 世职赛团队卷 | 2025 教育部赛制 | 团队赛 |
| 金砖卷 · BRICS-FS-11 | 2024 规程原件 | 金砖线 |
| **韩国世赛真题卷 2025** | 真题原文中译（AWS 全线） | 世赛线 |
| **WSC2026 上海世赛四日模考** | 官方 TD53 + WSOS 权重原创命题 | 世赛冲刺 |

> 每卷都标注了命题依据：真题原文 / 官方标准 / 同构原创——**不含编造的"真题"**。

## 🧪 实验环境（`labs/`）

- **路线 A · 纯云**：AWS Free Tier / AWS Academy / 华为云·阿里云学生机
- **路线 B · 双机虚拟机**：16–32G 内存，VMware/VirtualBox，CentOS 7.9 / openEuler
- **路线 C · 一键脚本**：`labs/openstack-train-allinone.sh` + `labs/k8s-cluster.sh`（幂等可重跑）

## 🧭 30 天路线（摘要）

| 周 | 主攻 | 验收 |
|---|---|---|
| W1 | Linux / 网络 / 网站服务 / Docker 入门 | 闭卷搭「静态站 + MySQL」 |
| W2 | DNS / HTTPS / 负载均衡 / Shell | 一条龙闭卷跑通 |
| W3 | **私有云**：OpenStack 搭建链 → 运维 → 脚本 | 搭建链 90 分钟闭卷 |
| W4 | **容器云**：kubeadm / 部署 / CI-CD / 排错 | 省赛卷容器模块限时 |
| W5 | 公有云 + 全真模拟 + 错题回炉 | 两套整卷限时模拟 |

详细每日任务见 [`start.html`](start.html)。

## 📖 来源与合规

- 真题文本来自公开渠道（CSDN 等，多为 CC BY-SA），保留来源链接，**仅供学习研究**，请勿去除出处二次分发。
- 官方标准文件（WSOS / TD53 / 金砖规程）版权归 WorldSkills、金砖组委会等原机构，此处仅作学习引用。
- 本项目的完整版（含 62 集视频课、50 个世赛赛项、全站资源库）见姊妹项目 **[知识公社 knowledge-commons](https://github.com/TaiMaBenJi/knowledge-commons)**（在线版：<https://taimabenji.github.io/knowledge-commons/>）。

## 🤝 贡献

欢迎提交 Issue / PR：补充真题、修正任务书、优化脚本。内容以「可验证、可复现」为准，引用请注明来源。

---

<p align="center"><b>比赛不是背出来的，是一套一套卷打出来的。</b><br>从 Day 1 开始。💪</p>
