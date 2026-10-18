#!/usr/bin/env bash
# =============================================================================
#  setup-linux.sh —— 在你自己的电脑上把 Linux 练习环境一次装好
# -----------------------------------------------------------------------------
#  用法（Windows 首选）：
#    1) 右键「开始」→ 终端(管理员) 或 PowerShell(管理员)
#    2) 把本仓库 clone 或下载到本地，进入该目录
#    3) 在 WSL 里执行：  bash setup/setup-linux.sh
#    （如果你现在还在 Windows、还没装 WSL，先用 setup/setup-windows.ps1）
#
#  用途：为「零基础 → 世赛云计算」这条线准备一台本地 Linux 练习机
#  特性：
#    · 幂等：可重复执行，已装的跳过，不重复刷屏
#    · 离线优先：先装包管理器依赖，网络失败不阻断
#    · 只装练习用得到的东西，不装多余服务
#    · 结束时自动跑自检，告诉你环境到底行不行
#
#  可选环境变量：
#    NO_DOCKER=1    跳过 Docker 安装
#    NO_K8S=1       跳过 minikube / kubectl / helm
#    DOCKER_CHANNEL=stable | test
# =============================================================================
set -uo pipefail

BOLD='\033[1m'; DIM='\033[2m'; R='\033[0m'
OK='\033[32m'; WARN='\033[33m'; ERR='\033[31m'; CYAN='\033[36m'
step()  { echo -e "\n${BOLD}${CYAN}==> $1${R}"; }
info()  { echo -e "    $1"; }
ok()    { echo -e "    ${OK}✓${R} $1"; }
warn()  { echo -e "    ${WARN}!${R} $1"; }
die()   { echo -e "    ${ERR}✗ $1${R}"; exit 1; }

# ---------------------------------------------------------------- 0. 前置检查
step "0/8 检查当前环境"
if [ "$(uname)" = "Darwin" ]; then
  PLAT="macOS"; PKG="brew"
elif grep -qi microsoft /proc/version 2>/dev/null; then
  PLAT="WSL(Windows)"; PKG="apt"
elif grep -qiE 'debian|ubuntu' /etc/os-release 2>/dev/null; then
  PLAT="Linux(Debian系)"; PKG="apt"
elif grep -qiE 'rocky|centos|rhel|alma|anolis|openeuler' /etc/os-release 2>/dev/null; then
  PLAT="Linux(RHEL系)"; PKG="dnf"
else
  PLAT="未知"; PKG=""
fi
info "平台：${BOLD}${PLAT}${R}   包管理器：${PKG:-无}"
[ -z "$PKG" ] && die "认不出包管理器，请确认这是 Linux / macOS / WSL 终端"
ok "发行版：$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-$PLAT}" || echo "$PLAT")"

# 内存与磁盘体检（OpenStack/K8s 对硬件有要求，先把话说在前面）
MEM_GB=$(awk '/MemTotal/{printf "%d", $2/1048576}' /proc/meminfo 2>/dev/null || echo 0)
if [ -z "$MEM_GB" ] || [ "$MEM_GB" -eq 0 ] 2>/dev/null; then MEM_GB=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%d",$1/1073741824}'); fi
DISK_GB=$(df -BG . 2>/dev/null | awk 'NR==2{gsub("G","",$4); print $4}')
info "内存：${MEM_GB} GB    可用磁盘：${DISK_GB:-?} GB"
if [ "${MEM_GB:-0}" -lt 4 ] 2>/dev/null; then
  warn "内存不足 4GB。练习 Linux/网络够用，但跑 Docker+K8s 会吃力"
fi

# ---------------------------------------------------------------- 1. 系统更新
step "1/8 更新系统与基础工具"
if [ "$PKG" = "apt" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq || warn "apt update 失败（可能是网络受限），继续"
  $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl wget git vim net-tools \
      iproute2 iputils-ping dnsutils netcat-openbsd socat rsync tree unzip htop jq \
      openssh-client openssh-server ca-certificates gnupg lsb-release cron logrotate || warn "部分包安装失败"
elif [ "$PKG" = "dnf" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO dnf -y -q update || warn "dnf update 失败，继续"
  $SUDO dnf -y -q install curl wget git vim net-tools iproute iputils bind-utils \
      nmap-ncat socat rsync tree unzip htop jq openssh-clients openssh-server \
      ca-certificates dnf-plugins-core logrotate cronie || warn "部分包安装失败"
elif [ "$PKG" = "brew" ]; then
  SUDO=""
  command -v brew >/dev/null || { warn "没装 Homebrew，先装：https://brew.sh"; brew_cmd=0; }
  command -v brew >/dev/null && brew update -qq 2>/dev/null; brew install -q curl wget git vim \
      netcat socat rsync tree htop jq 2>/dev/null || warn "brew 安装部分失败"
fi
ok "基础工具就绪"

# ---------------------------------------------------------------- 2. SSH
step "2/8 配置 SSH（世赛纪律：远程登录是基本功）"
if [ "$PKG" != "brew" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  if $SUDO systemctl enable --now ssh 2>/dev/null || $SUDO systemctl enable --now sshd 2>/dev/null; then
    ok "SSH 服务已启动并设为开机自启"
  else
    warn "SSH 服务启动失败（非交互环境常见），练习时可手动：systemctl start ssh"
  fi
  if ! ls ~/.ssh/id_ed25519 >/dev/null 2>&1 && ! ls ~/.ssh/id_rsa >/dev/null 2>&1; then
    ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 -q <<< "y" >/dev/null 2>&1 && ok "已生成 SSH 密钥对（~/.ssh/id_ed25519）"
  else
    ok "SSH 密钥已存在"
  fi
else
  warn "macOS 远程登录需在「系统设置 → 通用 → 共享」里手动打开"
fi

# ---------------------------------------------------------------- 3. 时区与时钟同步
step "3/8 时钟同步（nova/rabbitmq 对时间极其敏感，同步失败会连环报错）"
if [ "$PKG" = "apt" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO timedatectl set-timezone Asia/Shanghai 2>/dev/null && ok "时区设为 Asia/Shanghai" || warn "时区设置失败"
  $SUDO timedatectl set-ntp true 2>/dev/null && ok "NTP 已开启" || warn "NTP 不可用（容器/嵌套虚拟化常见）"
elif [ "$PKG" = "dnf" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO timedatectl set-timezone Asia/Shanghai 2>/dev/null && ok "时区设为 Asia/Shanghai" || warn "时区设置失败"
  $SUDO systemctl enable --now chronyd 2>/dev/null && ok "chronyd 已启动" || warn "chronyd 未安装"
fi
info "当前时间：$(date '+%F %T %Z')"

# ---------------------------------------------------------------- 4. 常用服务依赖
step "4/8 装练习必用的软件仓库与依赖"
if [ "$PKG" = "apt" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      build-essential python3 python3-pip python3-venv \
      mariadb-server mariadb-client redis-tools \
      nginx apache2-utils slapd ldap-utils \
      samba cifs-utils \
      haproxy keepalived \
      snmpd snmp-mibs-downloader dnsutils whois libpcap-dev \
      libvirt-daemon-system qemu-kvm libvirt-clients virtinst \
      shellcheck 2>/dev/null || $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      build-essential python3 python3-pip mariadb-server mariadb-client nginx \
      apache2-utils slapd ldap-utils samba haproxy keepalived shellcheck || warn "部分依赖安装失败"
  ok "依赖安装完成"
elif [ "$PKG" = "dnf" ]; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO dnf -y -q groupinstall "Development Tools" 2>/dev/null
  $SUDO dnf -y -q install python3 python3-pip MariaDB-server MariaDB-client \
      nginx httpd-tools openldap openldap-clients openldap-server \
      samba samba-client haproxy keepalived chrony shellcheck \
      libvirt-daemon-kv qemu-kvm virt-install || warn "部分依赖安装失败"
  ok "依赖安装完成"
fi
info "说明：MariaDB / nginx / slapd / samba / haproxy 只装不启，避免和你本机已有服务抢端口"

# ---------------------------------------------------------------- 5. Docker
step "5/8 Docker（容器云模块用）"
if [ "${NO_DOCKER:-0}" = "1" ]; then
  warn "按 NO_DOCKER=1 跳过"
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  ok "Docker 已就绪：$(docker --version | cut -d, -f1)"
elif [ "$PKG" = "brew" ]; then
  warn "macOS 请装 Docker Desktop：https://www.docker.com/products/docker-desktop/"
else
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  okk=0
  if command -v docker >/dev/null 2>&1; then
    $SUDO systemctl enable --now docker >/dev/null 2>&1 && okk=1
  fi
  if [ "$okk" = "0" ]; then
    warn "Docker 引擎不可用。"
    info "Ubuntu/Debian 可执行官方脚本：curl -fsSL https://get.docker.com | sh"
    info "RHEL 系：$SUDO dnf -y install podman && sudo systemctl enable --now podman.socket"
    info "（练习容器部分也可以先跳过，用 labs/cloudlab/tasks/L3-Docker.md 里的等效练习顶上）"
  else
    ok "Docker 已启动"
  fi
fi

# ---------------------------------------------------------------- 6. Kubernetes 工具链
step "6/8 Kubernetes 工具链（minikube / kubectl / helm）"
if [ "${NO_K8S:-0}" = "1" ]; then
  warn "按 NO_K8S=1 跳过"
else
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  ARCH=$(uname -m); case "$ARCH" in x86_64) A=amd64;; aarch64|arm64) A=arm64;; *) A=amd64;; esac
  if ! command -v kubectl >/dev/null 2>&1; then
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL -o /tmp/kubectl "https://dl.k8s.io/release/v1.31.0/bin/${PLAT%%(*)}/${A}/kubectl" 2>/dev/null \
        && $SUDO install -o root -g root -m 0755 /tmp/kubectl /usr/local/bin/kubectl 2>/dev/null \
        && ok "kubectl v1.31.0 已安装" || warn "kubectl 下载失败（网络受限），可稍后再装"
    fi
  else
    ok "kubectl 已存在：$(kubectl version --client 2>/dev/null | head -1 | cut -d' ' -f1-3)"
  fi
  if ! command -v minikube >/dev/null 2>&1; then
    warn "minikube 未安装。安装命令（联网时执行）："
    info "curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-${PLAT%%(*)}-${A}"
    info "$SUDO install -o root -g root -m 0755 minikube /usr/local/bin/minikube"
  else
    ok "minikube 已存在：$(minikube version --short 2>/dev/null)"
  fi
fi

# ---------------------------------------------------------------- 7. 练习目录
step "7/8 建练习工作区"
WORK="${HOME}/cloud-lab"
mkdir -p "$WORK"/{tasks,work,scripts,backup,logs,docs} && ok "练习目录：$WORK"
cat > "$WORK/README.txt" <<EOF
云计算练习工作区 · $(date '+%F')
================================
tasks/    放任务书（从 labs/cloudlab/tasks/ 拷过来）
work/     你的实操产物（配置、代码、脚本）
scripts/  你写的自动化脚本（Ansible playbook 等）
backup/   备份产物
logs/     排障时的日志留档
docs/     你自己的笔记

每天收工前做三件事：
1. git init 一次，之后每天 commit 一次（赛场要交变更文档）
2. 重要节点打快照（VMware/VirtualBox）或打包（tar czf backup/环境-$(date +%F).tgz .）
3. 把今天卡住的问题写进 logs/ 下，一句话就够
EOF
ok "已生成 $WORK/README.txt"

# ---------------------------------------------------------------- 8. 自检
step "8/8 环境自检"
pass=0; failn=0
chk() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$name"; pass=$((pass+1));
  else warn "$name"; failn=$((failn+1)); fi
}
chk "Linux 内核可读"            uname -a
chk "whoami / id 可用"          id
chk "ip 命令可用"               ip -V
chk "ping 可用"                 ping -V
chk "SSH 客户端可用"            ssh -V
chk "curl 可用"                 curl --version
chk "Git 可用"                  git --version
chk "Python3 可用"              python3 --version
chk "jq 可用"                   jq --version
chk "htop 可用"                 htop --version
chk "shellcheck 可用"           shellcheck --version
chk "mariadb 客户端可用"        mysql --version
chk "nginx 可用"                nginx -v
chk "haproxy 可用"              haproxy -v
chk "samba 工具可用"            testparm --version
chk "ldapsearch 可用"           ldapsearch -VV
chk "rsync 可用"                rsync --version
chk "工作区存在"                test -d "$WORK"

echo ""
echo -e "${BOLD}════════ 自检结果 ════════${R}"
echo -e "    通过 ${OK}${pass}${R} 项，待补 ${WARN}${failn}${R} 项"
echo -e ""
if [ "$failn" -gt 0 ]; then
  info "待补项多是「装不上」而非「用不了」，不影响开始学。"
  info "先做 labs/cloudlab/tasks/L1-Linux.md，评分脚本会告诉你缺什么。"
fi
cat <<EOF

${BOLD}下一步（按顺序）${R}
  1) 读任务书：labs/cloudlab/tasks/L1-Linux.md
  2) 在本机动手做完
  3) 验收打分：sudo bash labs/cloudlab/grade/grade_l1.sh
     复盘模式：sudo bash labs/cloudlab/grade/grade_l1.sh -v
  4) 全绿 → 打快照，进 L2
  5) 学习计划：打开 start.html 的「Linux 每日计划」

${CYAN}环境装好了。现在真正开始的是「每天敲命令」那一步。${R}
EOF
