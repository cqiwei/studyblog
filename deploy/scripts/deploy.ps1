# One-command deploy: build locally, ship to the VPS, switch the symlink.
#
#   .\deploy\scripts\deploy.ps1 -Target root@1.2.3.4
#
# First time? run  ssh root@1.2.3.4  manually once to accept the host key.
# Config can also come from env vars: BLOG_TARGET, BLOG_SITE.

[CmdletBinding()]
param(
    [string]$Target = $env:BLOG_TARGET,
    [string]$Site = $env:BLOG_SITE,
    [string]$RemoteRoot = "/var/www/blog",
    [string]$Identity = $env:BLOG_IDENTITY,
    [string]$KnownHosts = $env:BLOG_KNOWN_HOSTS,
    [switch]$SkipBuild,
    [switch]$SkipPurge,
    [string]$EnvFile = $env:BLOG_ENV_FILE
)

$ErrorActionPreference = "Stop"

# --- 0. optional local env file (gitignored) -------------------------------
# 把 CLOUDFLARE_API_TOKEN / BLOG_IDENTITY / BLOG_KNOWN_HOSTS 写进 .deploy\cf.env，
# 每行 KEY=VALUE，就不用每次 set 环境变量；已存在的环境变量优先级更高。
$siteRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $EnvFile) { $EnvFile = Join-Path $siteRoot ".deploy\cf.env" }
if (Test-Path $EnvFile) {
    foreach ($line in (Get-Content $EnvFile -Encoding UTF8)) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $k = $Matches[1]
            $v = $Matches[2].Trim('"').Trim("'")
            if (-not [Environment]::GetEnvironmentVariable($k)) { Set-Item -Path "env:$k" -Value $v }
        }
    }
}
if (-not $Identity) { $Identity = $env:BLOG_IDENTITY }
if (-not $KnownHosts) { $KnownHosts = $env:BLOG_KNOWN_HOSTS }
if (-not $Target) { $Target = $env:BLOG_TARGET }

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# default: the repo root, two levels above deploy\scripts
if (-not $Site) { $Site = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }

if (-not $Target) { Fail "missing -Target (e.g. root@1.2.3.4) or BLOG_TARGET" }
if (-not (Test-Path $Site)) { Fail "site directory not found: $Site" }

# 共用的 ssh 选项：非默认私钥、或者主机指纹还没进 known_hosts 时需要
#   -Identity   C:\Users\me\.ssh\id_ed25519
#   -KnownHosts D:\AI_Project\blog\.ssh_known_hosts
$sshOpts = @("-o", "ConnectTimeout=10")
if ($KnownHosts) { $sshOpts += @("-o", "UserKnownHostsFile=$KnownHosts", "-o", "StrictHostKeyChecking=accept-new") }
if ($Identity) { $sshOpts += @("-o", "IdentitiesOnly=yes", "-i", $Identity) }

# --- 1. locate hugo -------------------------------------------------------
$hugo = Join-Path $Site ".tools\hugo.exe"
if (-not (Test-Path $hugo)) {
    $cmd = Get-Command hugo -ErrorAction SilentlyContinue
    if (-not $cmd) { Fail "hugo not found. Put hugo.exe in $Site\.tools\ or add it to PATH." }
    $hugo = $cmd.Source
}

# --- 2. build -------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "==> building with $hugo" -ForegroundColor Cyan
    Push-Location $Site
    try {
        & $hugo --minify --gc --cleanDestinationDir
        if ($LASTEXITCODE -ne 0) { Fail "hugo build failed" }
    } finally { Pop-Location }
}

$public = Join-Path $Site "public"
if (-not (Test-Path (Join-Path $public "index.html"))) { Fail "public/index.html missing, build failed?" }

# --- 3. pack --------------------------------------------------------------
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$stage = Join-Path $Site ".deploy"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$archive = Join-Path $stage "blog-$ts.tar.gz"

Write-Host "==> packing release $ts" -ForegroundColor Cyan
tar -czf $archive -C $public .
if ($LASTEXITCODE -ne 0) { Fail "tar failed" }

$size = [math]::Round((Get-Item $archive).Length / 1MB, 2)
Write-Host "    $size MB" -ForegroundColor DarkGray

# --- 4. upload ------------------------------------------------------------
$remoteTmp = "/tmp/blog-$ts.tar.gz"
Write-Host "==> uploading to ${Target}:$remoteTmp" -ForegroundColor Cyan
scp -q @sshOpts $archive "${Target}:$remoteTmp"
if ($LASTEXITCODE -ne 0) { Fail "scp failed" }

# --- 5. activate ----------------------------------------------------------
Write-Host "==> activating" -ForegroundColor Cyan
$remoteScript = Get-Content (Join-Path $PSScriptRoot "remote-release.sh") -Raw
# 远端会把 nginx -t 的信息写到 stderr，而 EAP=Stop 会把原生命令的 stderr 当成异常，
# 所以这一段临时放开，只看退出码。
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$remoteScript | ssh @sshOpts $Target "bash -s -- $ts $remoteTmp"
$remoteCode = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($remoteCode -ne 0) { Fail "remote activation failed (site left on the previous release)" }

Remove-Item $archive -Force

# --- 6. purge Cloudflare edge cache (optional) ----------------------------
# 需要的前提：站点走了 Cloudflare 代理（橙色云朵）+ 边缘缓存了 HTML。
# 不清理的话，新文章要等到边缘 TTL 过期才可见。
# 设置 CLOUDFLARE_API_TOKEN（Zone -> Cache Purge -> Purge）即可自动执行。
if (-not $SkipPurge -and $env:CLOUDFLARE_API_TOKEN) {
    $py = $env:BLOG_PYTHON
    if (-not $py) { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }
    if (-not $py -and (Test-Path "D:\tools\python\python.exe")) { $py = "D:\tools\python\python.exe" }
    if (-not $py) {
        Write-Warning "找不到 python，跳过缓存清理（新内容要等边缘 TTL 过期才可见）"
    } else {
        Write-Host "==> purging Cloudflare cache" -ForegroundColor Cyan
        & $py (Join-Path $PSScriptRoot "purge-cache.py")
        if ($LASTEXITCODE -ne 0) { Write-Warning "缓存清理失败，页面可能仍是旧内容（部署本身已成功）" }
    }
}

Write-Host ""
Write-Host "OK  release $ts is live" -ForegroundColor Green
Write-Host "rollback: ssh $Target 'ln -sfn $RemoteRoot/releases/<old-id> $RemoteRoot/current && systemctl reload nginx'" -ForegroundColor DarkGray