# 真机实验室 · 环境搭建指南

> 比赛不会等你装环境。先把"考场"搭出来，再谈分数。
> 三条路线按硬件条件选，全部免费。原则：**环境一次搭好，快照保存；每次模拟从快照开新机。**

## 路线 A · 纯云（零硬件，世赛线首选）

**适合**：韩国世赛真题卷（AWS 全线）、WSC2026 模考、公有云模块。

| 方案 | 白嫖姿势 | 限制 |
|---|---|---|
| AWS Free Tier | 新账号 12 个月免费额度 + 部分永久免费 | 需信用卡验证；**设好 Billing 告警 $1** |
| AWS Academy Learner Lab | 学校开课免费拿 $100 额度，可重置 | 部分服务受限 |
| 华为云 / 阿里云学生免费 | 学生认证送服务器/代金券 | 规格较小 |

**纪律**：每次模拟前清空资源（韩国卷原文要求："比赛开始前删除所有默认服务"）；模拟完立刻销毁。

## 路线 B · 双机虚拟机（省赛/国赛/金砖标准考场）

**硬件底线**：16GB 内存（勉强）/ 32GB（舒适），4 核 CPU，120GB 磁盘。

1. 装 VMware Workstation（个人免费）或 VirtualBox（Windows）／KVM（Linux）。
2. 建两台 VM：`controller`（4C8G 60G）与 `compute`（2C8G 60G），双网卡：NAT（外网）+ 内部网络（管理网 192.168.100.0/24）。
3. 系统：CentOS 7.9 或 openEuler 22.03（赛项常用）。
4. **装完立刻打快照** `base-干净系统`，之后每次模拟从快照克隆。
5. 偷懒法：一台 8G 机跑 all-in-one OpenStack（搭建练习够用）。

## 路线 C · 一键脚本（最快进考场）

```bash
# 双机 OpenStack（控制节点执行，计算节点按提示预配置）
bash openstack-train-allinone.sh controller   # 控制节点
bash openstack-train-allinone.sh compute      # 计算节点

# K8s 三节点（master 执行，node 用输出的 join 命令）
bash k8s-cluster.sh master
bash k8s-cluster.sh node "<join 命令>"
```

- 脚本幂等：可重复执行；卡住看终端最后报错行，90% 是源/网络/内存三件事。
- 搭完用模拟卷对应任务逐项自验，全绿后**打快照** `ready-for-contest`。

## 四层通关任务书（配套日常训练）

见 [`cloudlab/README.md`](cloudlab/README.md)：L1 Linux → L2 网络服务 → L3 Docker → L4 Kubernetes，
每层任务书 + **自动评分脚本**（做对得分）+ L1 故障注入排错。与模拟卷配套食用。

## 考场纪律（每次模拟必做）

1. 从快照开新机 / 清空云账号。
2. 计时交给模拟执行器（`../sim/sim.html`），不要自己心算。
3. 按真实规则约束自己：只查本卷允许的资料。
4. 交卷后 24 小时内写复盘：失分项 → 对应教程章节 → 下次怎么防。

## 常见故障速查

| 症状 | 90% 的原因 |
|---|---|
| VM 起不来/极卡 | 内存不足（OpenStack 至少 8G）；关掉其他大程序 |
| keystone 认证 401 | admin-openrc 没 source / 密码大小写 |
| nova-compute down | 免密没配 / rabbitmq 没起 / 时间不同步 |
| k8s node NotReady | CNI 没装 / swap 没关 / containerd pause 镜像不通 |
| 卷创建卡住 | cinder-volume 服务 down；卷后端配置路径错 |
