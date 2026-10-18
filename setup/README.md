# 在你自己的电脑上把 Linux 环境装起来

> 三条命令，从零到能练。整个过程 **免费**，装完断网也能继续学。

---

## 你是什么系统？照下面走

### 🪟 Windows（最常见）

**第 1 步 · 用管理员身份打开终端**

按 `Win` 键 → 输入 `powershell` → 在「Windows PowerShell」上**右键 → 以管理员身份运行**

**第 2 步 · 执行一键脚本**

在弹出的窗口里粘贴这一行回车：

```powershell
irm https://raw.githubusercontent.com/TaiMaBenJi/cloud-computing-learning/main/setup/setup-windows.ps1 | iex
```

**会发生什么**：

1. 启用 WSL2 与虚拟机平台
2. 安装 Ubuntu 24.04 LTS
3. **打开 systemd**（这一步是关键，见下方说明）
4. 克隆本仓库并安装练习依赖
5. 弹出提示：首次启用 WSL 需要重启 → **重启后再执行一遍同一条命令**（第二步会自动跳过）

**第 3 步 · 体检**

重启后打开「Windows Terminal」，选 Ubuntu 标签（或输入 `wsl`），执行：

```bash
cd ~/cloud-computing-learning
bash setup/check-env.sh
```

看到「通过 N」且没有红色 ✗ 就可以开始了。

> ⚠️ **卡在 `irm` 报错 / 提示脚本禁止运行**：说明 PowerShell 限制了脚本执行。
> 改用：先下载 `setup-windows.ps1` 到本地，再执行
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\setup-windows.ps1
> ```

> ⚠️ **卡在「无法加载文件…未经数字签名」**：执行
> ```powershell
> Get-ExecutionPolicy -List
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

---

### 🍎 macOS

系统自带 Linux 环境，**不需要装虚拟机**。

```bash
# 1) 装 Homebrew（没装过才需要）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2) 装依赖
brew install curl wget git vim netcat socat rsync tree htop jq

# 3) 装本仓库并初始化
git clone https://github.com/TaiMaBenJi/cloud-computing-learning.git
cd cloud-computing-learning
bash setup/setup-linux.sh

# 4) 体检
bash setup/check-env.sh
```

> macOS 没有 systemd，`systemctl` 相关练习要在 Linux VM 或容器里做。
> 建议用 **Parallels / VMware Fusion / UTM** 装一台 Ubuntu 当练习机——
> 本仓库的所有评分脚本都以 Linux 为准。

---

### 🐧 已经有 Linux / WSL

```bash
git clone https://github.com/TaiMaBenJi/cloud-computing-learning.git
cd cloud-computing-learning
bash setup/setup-linux.sh      # 装依赖
bash setup/check-env.sh        # 体检
```

---

## 为什么要折腾 systemd

`systemctl` 是赛场的基本功——启服务、看日志、改开机自启，全靠它。

而 **WSL 默认是没有 systemd 的**，PID 1 是个小程序，`systemctl status` 会直接报错。
所以 `setup-windows.ps1` 专门做了这一步：往 `/etc/wsl.conf` 写入

```ini
[boot]
systemd=true
```

再 `wsl --shutdown` 让它生效。**跳过这步，后面所有服务操作都做不了。**

验证有没有成功：

```bash
ps -p 1 -o comm=
```

输出 `systemd` 就对了。

---

## 硬件要多少

| 阶段 | 内存 | 说明 |
|---|---|---|
| L1 Linux / L2 网络服务 | **4 GB** 够 | 只跑命令和配置练习 |
| L3 Docker | **8 GB** 舒服 | Docker 本身不重 |
| L4 Kubernetes（minikube） | **8 GB** 最低，**16 GB** 舒服 | 官方推荐 ≥ 4 核 |
| OpenStack allinone | **16 GB** 最低 | 内核要调大，见下 |

磁盘预留 **60 GB** 以上。

OpenStack 如果内存不够，追加内核参数（`/etc/security/limits.conf` 与 sysctl）：

```bash
echo 'vm.max_map_count = 2097152' | sudo tee -a /etc/sysctl.conf
sudo sysctl -w vm.max_map_count=2097152
sudo systemctl restart libvirtd docker
```

---

## 装完之后

1. **学计划**：浏览器打开 [`linux-plan.html`](../linux-plan.html)（21 天，每天一张卡）
2. **练环境**：[`labs/cloudlab/`](../labs/cloudlab/README.md) 四层通关任务书 + 自动评分
3. **打比赛**：[`sim/index.html`](../sim/index.html) 7 套全真卷，计时交卷

---

## 脚本参数

| 脚本 | 参数 | 作用 |
|---|---|---|
| `setup/setup-linux.sh` | `NO_DOCKER=1` | 跳过 Docker |
| | `NO_K8S=1` | 跳过 minikube / kubectl |
| | `DOCKER_CHANNEL=test` | 用 Docker 测试版通道 |
| `setup/check-env.sh` | `-v` | 逐项显示判断依据 |

全部脚本**幂等**：重复执行安全，已装的会跳过。

---

## 常见问题

| 症状 | 原因与解法 |
|---|---|
| `wsl` 提示「找不到命令」 | 没装 WSL，跑一次 `setup-windows.ps1` 后重启 |
| `systemctl` 报 `System has not been booted with systemd` | `/etc/wsl.conf` 没写或没重启：`echo '[boot]' > /etc/wsl.conf && echo 'systemd=true' >> /etc/wsl.conf && wsl --shutdown` |
| `apt update` 很慢或超时 | 换国内源：见 `labs/README.md`，或用 `sed` 把 sources 换成清华/阿里镜像 |
| Docker 起来了但 `docker info` 报权限错 | `sudo usermod -aG docker $USER` 后**重新登录** |
| WSL 占太多 C 盘空间 | 把发行版导出后迁到 D 盘：`wsl --export`、`wsl --import` |
| 内存不够被 OOM Kill | WSL 默认只用一半内存：`.wslconfig` 里写 `[wsl2] memory=16GB` |
| 虚拟化嵌套失败（VMware 里装 KVM） | BIOS 里开启 VT-x / AMD-V |
