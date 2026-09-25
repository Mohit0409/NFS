[CmdletBinding()]
param(
  [string]$SshHost = "redmi-host",
  [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$expectedPorts = @(8897, 8898, 8899, 8900)
$managedServices = @(
  "nfs-demo-admin",
  "nfs-demo-member",
  "nfs-demo-web",
  "nfs-demo-edge",
  "nfs-demo-ngrok"
)

function Invoke-Ssh {
  param([Parameter(Mandatory=$true)][string]$Command)
  $output = & ssh -o BatchMode=yes -o ConnectTimeout=8 $SshHost $Command 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "SSH command failed for $SshHost. $($output -join [Environment]::NewLine)"
  }
  return @($output)
}

function Assert-CleanGit {
  Push-Location $projectRoot
  try {
    $status = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "git status failed" }
    if ($status) {
      throw "Refusing owner-demo deployment from a dirty working tree."
    }
    $sha = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') {
      throw "Unable to resolve the deployment Git commit."
    }
    return $sha
  }
  finally {
    Pop-Location
  }
}

function Get-RemoteInspection {
  $script = @'
set -eu
printf 'USER=%s\n' "$(whoami)"
printf 'MODEL=%s\n' "$(getprop ro.product.model 2>/dev/null || true)"
printf 'DEVICE=%s\n' "$(getprop ro.product.device 2>/dev/null || true)"
printf 'MANUFACTURER=%s\n' "$(getprop ro.product.manufacturer 2>/dev/null || true)"
printf 'PREFIX=%s\n' "$(printenv PREFIX 2>/dev/null || true)"
printf 'HOME=%s\n' "$HOME"
printf 'FREE_KB=%s\n' "$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
printf 'NGROK=%s\n' "$(command -v ngrok 2>/dev/null || true)"
if command -v ngrok >/dev/null 2>&1 && ngrok config check >/dev/null 2>&1; then
  echo 'NGROK_AUTH=ok'
else
  echo 'NGROK_AUTH=not_ready'
fi
for port in 8897 8898 8899 8900; do
  if ss -ltnH 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"; then
    printf 'PORT_%s=busy\n' "$port"
  else
    printf 'PORT_%s=free\n' "$port"
  fi
done
for service in nfs-demo-admin nfs-demo-member nfs-demo-web nfs-demo-edge nfs-demo-ngrok; do
  target="$PREFIX/var/service/$service"
  if [ ! -e "$target" ]; then
    printf 'SERVICE_%s=absent\n' "$service"
  elif [ -f "$target/.nfs-owner-demo-managed" ]; then
    printf 'SERVICE_%s=managed\n' "$service"
  else
    printf 'SERVICE_%s=unmanaged\n' "$service"
  fi
done
'@
  $raw = Invoke-Ssh $script
  $result = @{}
  foreach ($line in $raw) {
    if ($line -match '^([^=]+)=(.*)$') {
      $result[$matches[1]] = $matches[2]
    }
  }
  return $result
}

function Get-InspectionValue {
  param(
    [Parameter(Mandatory=$true)][hashtable]$Inspection,
    [Parameter(Mandatory=$true)][string]$Key,
    [string]$Default = ""
  )
  if ($Inspection.ContainsKey($Key) -and $null -ne $Inspection[$Key]) {
    return [string]$Inspection[$Key]
  }
  return $Default
}

$sha = Assert-CleanGit
Write-Host "Need For Strength owner-demo candidate: $sha"

$inspection = Get-RemoteInspection
$model = Get-InspectionValue -Inspection $inspection -Key "MODEL"
$device = Get-InspectionValue -Inspection $inspection -Key "DEVICE"
$manufacturer = Get-InspectionValue -Inspection $inspection -Key "MANUFACTURER"
$user = Get-InspectionValue -Inspection $inspection -Key "USER"

if ($user -ne "u0_a304") {
  throw "Refusing target: expected Termux user u0_a304, found '$user'."
}
if ($manufacturer -notmatch '(?i)xiaomi|redmi' -or $model -notmatch '(?i)^(23124RN87I|Redmi 13C 5G)$') {
  throw "Refusing target: expected the configured Redmi 13C 5G / 23124RN87I. Manufacturer='$manufacturer' Model='$model' Device='$device'."
}

$freeKb = 0L
if (-not [long]::TryParse((Get-InspectionValue -Inspection $inspection -Key "FREE_KB" -Default "0"), [ref]$freeKb) -or $freeKb -lt 524288) {
  throw "Refusing target: at least 512 MB free storage is required for the isolated demo runtime."
}

foreach ($service in $managedServices) {
  $state = Get-InspectionValue -Inspection $inspection -Key ("SERVICE_" + $service) -Default "unknown"
  if ($state -eq "unmanaged" -or $state -eq "unknown") {
    throw "Refusing target: service '$service' exists but is not marked as Need For Strength owner-demo managed."
  }
}

$portOwners = @{
  8897 = "nfs-demo-admin"
  8898 = "nfs-demo-member"
  8899 = "nfs-demo-web"
  8900 = "nfs-demo-edge"
}
foreach ($port in $expectedPorts) {
  $state = Get-InspectionValue -Inspection $inspection -Key ("PORT_" + $port) -Default "unknown"
  if ($state -eq "unknown") {
    throw "Refusing target: could not determine TCP port $port state."
  }
  if ($state -eq "busy") {
    $ownerService = $portOwners[$port]
    $ownerState = Get-InspectionValue -Inspection $inspection -Key ("SERVICE_" + $ownerService) -Default "unknown"
    if ($ownerState -ne "managed") {
      throw "Refusing target: TCP port $port is busy but matching service '$ownerService' is not an existing managed owner-demo service."
    }
  }
}

if ((Get-InspectionValue -Inspection $inspection -Key "NGROK_AUTH") -ne "ok") {
  throw "Redmi ngrok is not installed/authenticated. Configure ngrok on the Redmi before deployment."
}

Write-Host "Target verified: $manufacturer $model ($device), user $user"
Write-Host "Free storage: $([math]::Round($freeKb / 1024, 0)) MB"
Write-Host "Ports 8897-8900: safe for isolated owner demo"
Write-Host "ngrok: authenticated"

if ($PreflightOnly) {
  Write-Host "PREFLIGHT_ONLY=PASS"
  exit 0
}

$stageRoot = "/data/data/com.termux/files/home/staging/need-for-strength-owner-demo"
$appRoot = "/data/data/com.termux/files/home/apps/need-for-strength-owner-demo"
$remoteStage = "$stageRoot/$sha"
$remoteApp = "$appRoot/$sha"
$tempArchive = Join-Path $env:TEMP "need-for-strength-owner-demo-$sha.tar.gz"

Push-Location $projectRoot
try {
  if (Test-Path $tempArchive) { Remove-Item -Force $tempArchive }
  & git archive --format=tar.gz -o $tempArchive HEAD
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tempArchive)) {
    throw "Failed to create the owner-demo Git archive."
  }
}
finally {
  Pop-Location
}

try {
  Invoke-Ssh "mkdir -p '$remoteStage' '$appRoot'"
  $scpTarget = $SshHost + ":" + $remoteStage + "/source.tar.gz"
  & scp -q $tempArchive $scpTarget
  if ($LASTEXITCODE -ne 0) { throw "Failed to upload the owner-demo archive." }

  $remoteInstall = @'
set -euo pipefail
archive='__ARCHIVE__'
app='__APP__'
test -f "$archive"
rm -rf "$app.tmp"
mkdir -p "$app.tmp"
tar -xzf "$archive" -C "$app.tmp"
if [ -e "$app" ]; then
  if [ -f "$app/.nfs-owner-demo-release" ]; then
    rm -rf "$app"
  else
    echo "Refusing to replace unmanaged owner-demo app directory: $app" >&2
    exit 1
  fi
fi
mv "$app.tmp" "$app"
printf '%s\n' '__SHA__' > "$app/.nfs-owner-demo-release"
cd "$app"
bash admin/deploy/owner-demo/install-owner-demo.sh
'@
  $remoteInstall = $remoteInstall.Replace("__ARCHIVE__", $remoteStage + "/source.tar.gz")
  $remoteInstall = $remoteInstall.Replace("__APP__", $remoteApp)
  $remoteInstall = $remoteInstall.Replace("__SHA__", $sha)

  $result = Invoke-Ssh $remoteInstall
  $result | ForEach-Object { Write-Host $_ }

  $customer = $result | Where-Object { $_ -match '^Customer site:' } | Select-Object -Last 1
  $admin = $result | Where-Object { $_ -match '^Admin portal:' } | Select-Object -Last 1
  if (-not $customer -or -not $admin) {
    throw "Demo services started but the ngrok URLs were not returned by the installer."
  }

  Write-Host ""
  Write-Host "OWNER_DEMO_DEPLOYMENT=PASS"
  Write-Host $customer
  Write-Host $admin
}
finally {
  Remove-Item -Force $tempArchive -ErrorAction SilentlyContinue
}
