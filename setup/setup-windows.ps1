<#
.SYNOPSIS
  在 Windows 电脑上一次性装好 Linux 练习环境（WSL2 + Ubuntu + systemd + 练习依赖）

.DESCRIPTION
  这是给「零基础 → 世赛云计算」准备的 Windows 一键脚本，做四件事：
    1. 启用 WSL2 与虚拟机平台
    2. 安装 Ubuntu 24.04 LTS
    3. 打开 systemd（关键！没有它 systemctl 全废，实训场跑不起来）
    4. 拉取本仓库并在里面执行 setup/setup-linux.sh 装练习依赖

  幂等：重复执行安全，已装过的跳过。

.EXAMPLE
  右键「开始」→ 终端(管理员)，粘贴执行：
    irm https://raw.githubusercontent.com/TaiMaBenJi/cloud-computing-learning/main/setup/setup-windows.ps1 | iex

  或下载后本地执行：
    powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1

.NOTES
  硬件建议：16GB 内存起步（跑 Docker+K8s 舒服），8GB 能跑基础练习。
  磁盘：预留 60GB 以上。
#>

#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$UserName = "",
    [switch]$SkipDeps,
    [switch]$SkipRepo
)

$ErrorActionPreference = "Continue"
$Bold = ""
$Dim = ""
$Ok = ""
$Warn = ""
$Err = ""
$Reset = ""

function Write-Step($m) { Write-Host "" ; Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Info($m) { Write-Host "    $m" -ForegroundColor Gray }
function Write-Ok($m)   { Write-Host "    [OK] $m" -ForegroundColor Green }
function Write-Warn($m) { Write-Host "    [!]  $m" -ForegroundColor Yellow }
function Write-Err($m)  { Write-Host "    [X]  $m" -ForegroundColor Red }

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ---------------------------------------------------------------- 0. 管理员检查
Write-Step "0/5 检查权限"
if (-not (Test-Admin)) {
    Write-Err "这个脚本需要管理员权限。"
    Write-Info "请右键「开始」→ 终端(管理员) 或 PowerShell(管理员) 后重新执行。"
    Write-Info "或者在终端里先执行：Start-Process powershell -Verb RunAs"
    exit 1
}
Write-Ok "管理员权限正常"

# ---------------------------------------------------------------- 1. 硬件体检
Write-Step "1/5 硬件体检"
$cs = Get-CimInstance Win32_ComputerSystem
$memGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
$cpuCores = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
$disk = Get-PSDrive -Name C | Select-Object -ExpandProperty Used
$freeGB = [math]::Round((Get-PSDrive -Name C).Free / 1GB, 1)
Write-Info "内存 $memGB GB · 逻辑核心 $cpuCores · C 盘可用 $freeGB GB"
if ($memGB -lt 8) { Write-Warn "内存 < 8GB：L1-L3 练习没问题，Docker/K8s 会吃力" }
if ($freeGB -lt 40) { Write-Warn "C 盘可用 < 40GB：WSL2 镜像 + 容器可能不够" }

# ---------------------------------------------------------------- 2. WSL2
Write-Step "2/5 启用 WSL2 与虚拟机平台"
$alreadyWsl = $false
try {
    $wslOut = & wsl.exe --status 2>&1
    if ($LASTEXITCODE -eq 0) { $alreadyWsl = $true }
} catch { }

if ($alreadyWsl) {
    Write-Ok "WSL 已安装"
    Write-Info ($wslOut | Out-String).Trim()
} else {
    Write-Info "正在启用 WSL 可选功能（可能需要 1-3 分钟）..."
    try {
        $r = Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux `
             -All -NoRestart -ErrorAction Stop
        Write-Ok "WSL 功能已启用"
    } catch { Write-Warn "WSL 功能启用异常：$($_.Exception.Message)" }

    try {
        $r = Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform `
             -All -NoRestart -ErrorAction Stop
        Write-Ok "虚拟机平台已启用"
    } catch { Write-Warn "虚拟机平台启用异常：$($_.Exception.Message)" }

    Write-Info "正在安装 WSL2 内核..."
    try {
        & wsl.exe --update --no-distribution 2>&1 | Out-Null
        Write-Ok "WSL2 内核已更新"
    } catch { Write-Warn "WSL 内核更新失败，可稍后重试：wsl --update" }

    Write-Host ""
    Write-Warn "首次启用 WSL 后通常需要重启一次。"
    Write-Info "请重启电脑，然后重新执行本脚本（第二步会跳过，直接进第三步）。"
    Write-Host ""
    Read-Host "按回车退出（也可以现在就去重启）" | Out-Null
    Write-Host "如果你选择重启，现在执行：Restart-Computer"
    exit 0
}

# ---------------------------------------------------------------- 3. 发行版
Write-Step "3/5 安装 Linux 发行版"
$distros = (& wsl.exe --list --quiet 2>$null) | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$have = $false
foreach ($d in $distros) { if ($d -match [regex]::Escape($Distro)) { $have = $true } }

if ($have) {
    Write-Ok "$Distro 已安装"
} else {
    Write-Info "正在安装 $Distro ..."
    try {
        & wsl.exe --install -d $Distro --no-launch 2>&1 | Out-Null
        Write-Ok "$Distro 安装完成"
    } catch {
        Write-Warn "自动安装失败（微软商店不可用时常见），请手动执行："
        Write-Info "  wsl --install -d $Distro"
        Write-Info "或从 https://aka.ms/wslstorepage 手动下载安装。"
    }
}

# 设为默认
try {
    & wsl.exe --set-default $Distro 2>&1 | Out-Null
    Write-Ok "已设为默认发行版"
} catch { Write-Warn "设置默认发行版失败（可忽略）" }

# ---------------------------------------------------------------- 4. systemd
Write-Step "4/5 开启 systemd（实训场强依赖这一步）"
$distroName = ($Distro -split '-')[0].ToLower()

$enableSystemd = @"
set -e
if [ ! -f /etc/wsl.conf ] || ! grep -q '^\[boot\]' /etc/wsl.conf 2>/dev/null; then
  printf '[boot]\nsystemd=true\n\n[user]\ndefault=$UserName\n' > /etc/wsl.conf
else
  sed -i '/^systemd=/d' /etc/wsl.conf
  sed -i '/^\[boot\]/a systemd=true' /etc/wsl.conf
  grep -q '^\[user\]' /etc/wsl.conf || printf '\n[user]\ndefault=$UserName\n' >> /etc/wsl.conf
  [ -n "$UserName" ] || sed -i '/^default=/d' /etc/wsl.conf
fi
cat /etc/wsl.conf
"@

$inner = if ($UserName) { $enableSystemd -replace '\$UserName', $UserName }
          else { ($enableSystemd -replace '\$UserName', '') -replace "printf '\[boot\]\\nsystemd=true\\n\\n\[user\]\\ndefault=\\n'", "printf '[boot]\\nsystemd=true\\n'" }

Write-Info "写入 /etc/wsl.conf ..."
& wsl.exe -d $Distro -u root -- bash -lc "$inner" 2>&1 | Out-String | Write-Host
Write-Ok "systemd 已配置"

Write-Warn "必须执行一次 wsl --shutdown 让配置生效，正在做..."
& wsl.exe --shutdown 2>&1 | Out-Null
Start-Sleep -Seconds 3

# 验证
$sysd = & wsl.exe -d $Distro -u root -- bash -lc "ps -p 1 -o comm= 2>/dev/null | head -1" 2>$null
if ("$sysd" -match "systemd") {
    Write-Ok "systemd 运行中（PID 1 = systemd）"
} else {
    Write-Warn "systemd 未生效。如果下面练习 systemctl 报错，执行 wsl --shutdown 后重开终端再试。"
}

# ---------------------------------------------------------------- 5. 依赖
Write-Step "5/5 拉取项目并安装练习依赖"
$repoUrl = "https://github.com/TaiMaBenJi/cloud-computing-learning.git"
$target = if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "cloud-computing-learning" } else { "$HOME/cloud-computing-learning" }

if (-not $SkipRepo) {
    $escaped = $target -replace "'", "'\\''"
    & wsl.exe -d $Distro -u root -- bash -lc @"
set -e
if [ -d '$escaped/.git' ]; then
  echo '  [OK] 仓库已存在，尝试更新'
  cd '$escaped' && git pull --ff-only 2>/dev/null || echo '  [!] 更新失败，用本地版本继续'
else
  echo '  [*] 克隆仓库 ...'
  if command -v git >/dev/null 2>&1; then
    git clone --depth 1 $repoUrl '$escaped' 2>/dev/null || {
      echo '  [!] 克隆失败（网络受限）。可手动下载后解压到：$escaped'; exit 0; }
  else
    echo '  [!] 未安装 git。请先 apt update && apt install -y git'
  fi
fi
cd '$escaped' && ls -1 | head -20
"@ 2>&1 | Out-String | Write-Host
}

if (-not $SkipDeps) {
    $depsScript = "cd '$target' && bash setup/setup-linux.sh 2>&1"
    & wsl.exe -d $Distro -u root -- bash -lc $depsScript 2>&1 | Out-String | Write-Host
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 环境安装流程结束" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " 现在做这三件事：" -ForegroundColor Yellow
Write-Host "   1. 打开 Windows Terminal -> wsl            （进入 Linux）"
Write-Host "   2. 检查环境：bash $target/setup/check-env.sh"
Write-Host "   3. 学计划：浏览器打开 start.html 的「Linux 每日计划」"
Write-Host ""
Write-Host " 常用命令（记这几个就够开始）："
Write-Host "   pwd / ls / cd / cat / nano / mkdir / cp / mv / rm / grep / ps / top"
Write-Host "   systemctl status nginx / systemctl restart nginx"
Write-Host "   ip a / ping / curl -I / ss -tlnp"
Write-Host ""
