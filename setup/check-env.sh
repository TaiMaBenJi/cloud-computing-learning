#!/usr/bin/env bash
# =============================================================================
#  check-env.sh —— 环境体检：告诉我这台 Linux 机器到底行不行
# -----------------------------------------------------------------------------
#  用法：  bash setup/check-env.sh          普通检查
#          bash setup/check-env.sh -v       逐项显示判断依据
#  退出码：0 = 全部通过；1 = 有阻塞项
# =============================================================================
set -uo pipefail

VERBOSE=0
[ "${1:-}" = "-v" ] || [ "${1:-}" = "--verbose" ] && VERBOSE=1

PASS=0; WARN=0; BAD=0
declare -a FAILED=()

hdr()  { printf '\n\033[1;36m%s\033[0m\n' "$1"; }
pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; WARN=$((WARN+1)); FAILED+=("WARN: $1"); }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; BAD=$((BAD+1));  FAILED+=("BAD:  $1"); }
detail() { [ "$VERBOSE" = "1" ] && printf '      \033[2m%s\033[0m\n' "$1"; return 0; }

printf '\033[1m════════ 云计算练习环境体检 ════════\033[0m\n'

# ---------------------------------------------------------------- 0. 系统
hdr "0. 系统信息"
[ -r /etc/os-release ] && . /etc/os-release
printf '  发行版：%s\n' "${PRETTY_NAME:-未知}"
printf '  内核  ：%s\n' "$(uname -r)"
printf '  架构  ：%s\n' "$(uname -m)"
printf '  时间  ：%s\n' "$(date '+%F %T %Z')"

MEM_GB=$(awk '/MemTotal/{printf "%d", $2/1048576}' /proc/meminfo 2>/dev/null || echo 0)
if [ -z "$MEM_GB" ] || [ "$MEM_GB" -eq 0 ] 2>/dev/null; then
  MEM_GB=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%d",$1/1073741824}')
fi
CPU=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)
FREE=$(df -BG . 2>/dev/null | awk 'NR==2{gsub("G","",$4); print $4}')
printf '  资源  ：%s 核 / %s GB 内存 / 可用磁盘 %s GB\n' "$CPU" "${MEM_GB:-?}" "${FREE:-?}"

if [ "${MEM_GB:-0}" -ge 8 ] 2>/dev/null; then pass "内存 ≥ 8GB（可跑 Docker + K8s）"
elif [ "${MEM_GB:-0}" -ge 4 ] 2>/dev/null; then warn "内存 ${MEM_GB}GB：L1-L3 够用，K8s 会吃力"
else bad "内存 ${MEM_GB:-0}GB：低于 4GB，建议扩容"; fi

# ---------------------------------------------------------------- 1. 系统管理
hdr "1. 系统管理（init 系统）"
PS1C=$(ps -p 1 -o comm= 2>/dev/null | head -1 | tr -d ' ')
if command -v systemctl >/dev/null 2>&1 && [ "$PS1C" = "systemd" ]; then
  pass "systemd 正在运行（PID 1 = systemd）"
elif command -v systemctl >/dev/null 2>&1; then
  warn "有 systemctl 但 PID 1 是 '$PS1C'"
  detail "WSL 用户执行：wsl --shutdown 后重开终端；容器内建议 --privileged 或改用宿主"
else
  bad "没有 systemd —— 实训场的 systemctl 全部不可用"
fi
if command -v crontab >/dev/null 2>&1; then pass "crontab 可用（定时任务）"; else warn "crontab 不可用"; fi

# ---------------------------------------------------------------- 2. 核心命令
hdr "2. 基础命令（赛场天天用）"
for c in ls cd pwd cat nano vim grep find awk sed head tail \
         chmod chown mkdir rm cp mv tar ps top df free \
         ip ping dig nslookup curl wget ss netstat nc \
         systemctl service crontab journalctl; do
  if command -v "$c" >/dev/null 2>&1; then
    pass "$c"
  else
    warn "$c 缺失"
    case "$c" in
      dig|nslookup) detail "apt install dnsutils / dnf install bind-utils" ;;
      nc)           detail "apt install netcat-openbsd / dnf install nmap-ncat" ;;
      ss)           detail "apt install iproute2 / dnf install iproute" ;;
      crontab)      detail "apt install cron / dnf install cronie" ;;
      journalctl)   detail "apt install systemd / dnf install systemd" ;;
      *)            detail "apt install <包> 或 dnf install <包>" ;;
    esac
  fi
done

# ---------------------------------------------------------------- 3. 开发与脚本
hdr "3. 开发与脚本"
for c in git python3 pip3 jq htop shellcheck rsync socat tree; do
  if command -v "$c" >/dev/null 2>&1; then
    v=$($c --version 2>&1 | head -1 | cut -c1-40); pass "$c  ${v}"
  else warn "$c 缺失"; fi
done
if command -v ssh >/dev/null 2>&1; then pass "SSH 客户端（ssh / scp）"; else warn "SSH 客户端缺失"; fi
if [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ecdsa ] || [ -f ~/.ssh/id_dsa ]; then
  pass "SSH 密钥对已生成"
else warn "没有 SSH 密钥对：ssh-keygen -t ed25519"; fi

# ---------------------------------------------------------------- 4. 云与容器
hdr "4. 云平台与容器"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then pass "Docker 运行中：$(docker --version 2>/dev/null | cut -d, -f1)"
  else warn "Docker 装了但没运行：systemctl start docker（容器内可能需特权）"; fi
else warn "Docker 未安装"; fi
if command -v podman >/dev/null 2>&1; then pass "Podman：$(podman --version 2>/dev/null)"; fi
for c in kubectl minikube helm k3s kind; do
  command -v "$c" >/dev/null 2>&1 && pass "$c（$($c version --client 2>/dev/null | head -1 | cut -c1-34)）" || true
done
for c in openstack keystone nova neutron glance cinder; do
  command -v "$c" >/dev/null 2>&1 && pass "$c CLI（OpenStack）" || true
done

# ---------------------------------------------------------------- 5. 服务与组件
hdr "5. 常见服务组件（装不装都能学，缺了再补）"
declare -A SVC=( [nginx]=nginx [mariadb|mysql]=mariadb [haproxy]=haproxy
                 [keepalived]=keepalived [slapd]=slapd [smbd]=smbd
                 [docker]=docker [sshd|ssh]=ssh )
for k in "${!SVC[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${k}\.service"; then
    st=$(systemctl is-active "$k" 2>/dev/null || echo inactive)
    printf '  \033[2m·\033[0m %-12s 已安装 · 当前 %s\n' "$k" "$st"
    PASS=$((PASS+1))
  fi
done

hdr "6. 可选组件"
for c in mysql mariadb nginx haproxy keepalived ldapsearch testparm slapd docker; do
  command -v "$c" >/dev/null 2>&1 && pass "$c 已安装" || warn "$c 未安装（用到再装）"
done

# ---------------------------------------------------------------- 7. 练习目录
hdr "7. 练习工作区"
if [ -d "$HOME/cloud-lab" ]; then pass "工作区 ~/cloud-lab 存在"
else warn "工作区未建：bash setup/setup-linux.sh 会自动创建"; fi
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
if [ -d "$REPO_DIR/labs/cloudlab" ]; then pass "实训场任务书：$REPO_DIR/labs/cloudlab"
else warn "未找到 labs/cloudlab（确认你在仓库根目录执行）"; fi
if [ -f "$REPO_DIR/labs/cloudlab/grade/grade_l1.sh" ]; then
  pass "评分脚本就绪：sudo bash labs/cloudlab/grade/grade_l1.sh"
else warn "评分脚本缺失"; fi

# ---------------------------------------------------------------- 结论
printf '\n\033[1m════════ 结论 ════════\033[0m\n'
printf '  通过 \033[32m%d\033[0m   提醒 \033[33m%d\033[0m   阻塞 \033[31m%d\033[0m\n\n' "$PASS" "$WARN" "$BAD"

if [ "$BAD" -gt 0 ]; then
  echo "  阻塞项（必须解决）："
  for f in "${FAILED[@]}"; do case "$f" in BAD:*) echo "    $f";; esac; done
  echo ""
  echo "  解决办法：重新执行  bash setup/setup-linux.sh"
else
  echo -e "  \033[32m环境可用，现在去 labs/cloudlab/tasks/L1-Linux.md 开始。\033[0m"
fi
if [ "$WARN" -gt 0 ]; then
  echo ""
  echo "  提醒项（用到再补，不影响开练）："
  for f in "${FAILED[@]}"; do case "$f" in WARN:*) echo "    $f";; esac; done
fi
echo ""

[ "$BAD" -gt 0 ] && exit 1 || exit 0
