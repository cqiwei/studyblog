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
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

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
$remoteScript | ssh @sshOpts $Target "bash -s -- $ts $remoteTmp"
if ($LASTEXITCODE -ne 0) { Fail "remote activation failed (site left on the previous release)" }

Remove-Item $archive -Force

Write-Host ""
Write-Host "OK  release $ts is live" -ForegroundColor Green
Write-Host "rollback: ssh $Target 'ln -sfn $RemoteRoot/releases/<old-id> $RemoteRoot/current && systemctl reload nginx'" -ForegroundColor DarkGray