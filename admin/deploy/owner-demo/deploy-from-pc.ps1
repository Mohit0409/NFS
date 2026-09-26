[CmdletBinding()]
param(
  [string]$SshHost = "redmi-host",
  [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$preflightScript = Join-Path $PSScriptRoot "usb-termux-preflight.sh"
$bootstrapScript = Join-Path $PSScriptRoot "usb-bootstrap-owner-demo.sh"

function Invoke-Ssh {
  param([Parameter(Mandatory=$true)][string]$Command)
  $output = & ssh -o BatchMode=yes -o ConnectTimeout=8 $SshHost $Command 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "SSH command failed for $SshHost. $($output -join [Environment]::NewLine)"
  }
  return @($output)
}

function Invoke-Scp {
  param(
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [Parameter(Mandatory=$true)][string]$RemotePath
  )
  $target = $SshHost + ":" + $RemotePath
  & scp -q -o BatchMode=yes -o ConnectTimeout=8 $LocalPath $target
  if ($LASTEXITCODE -ne 0) {
    throw ("SCP failed: " + $LocalPath + " -> " + $target)
  }
}

function Get-CleanCommit {
  Push-Location $projectRoot
  try {
    $status = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "git status failed" }
    if ($status) { throw "Refusing owner-demo deployment from a dirty working tree." }

    $sha = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') {
      throw "Unable to resolve a full Git commit."
    }
    return $sha
  }
  finally {
    Pop-Location
  }
}

function Assert-TargetIdentity {
  $identityCommand = 'echo "USER=$(whoami)"; echo "MODEL=$(getprop ro.product.model 2>/dev/null || true)"; echo "MANUFACTURER=$(getprop ro.product.manufacturer 2>/dev/null || true)"'
  $raw = Invoke-Ssh $identityCommand
  $values = @{}
  foreach ($line in $raw) {
    if ($line -match '^([^=]+)=(.*)$') { $values[$matches[1]] = $matches[2] }
  }

  if (-not $values.ContainsKey("USER") -or $values["USER"] -ne "u0_a304") {
    throw "Refusing target: expected Termux user u0_a304."
  }
  if (-not $values.ContainsKey("MODEL") -or $values["MODEL"] -ne "23124RN87I") {
    throw "Refusing target: expected Redmi model 23124RN87I."
  }
  if (-not $values.ContainsKey("MANUFACTURER") -or $values["MANUFACTURER"] -notmatch '(?i)xiaomi|redmi') {
    throw "Refusing target: manufacturer is not Xiaomi/Redmi."
  }

  Write-Host "Target verified: $($values['MANUFACTURER']) $($values['MODEL']) / $($values['USER'])"
}

$sha = Get-CleanCommit
Write-Host "Need For Strength owner-demo candidate: $sha"
Assert-TargetIdentity

$remoteBase = "/data/data/com.termux/files/home/staging/need-for-strength-owner-demo/$sha"
Invoke-Ssh "mkdir -p '$remoteBase'"

if ($PreflightOnly) {
  $remotePreflight = "$remoteBase/usb-termux-preflight.sh"
  Invoke-Scp -LocalPath $preflightScript -RemotePath $remotePreflight
  $result = Invoke-Ssh "bash '$remotePreflight' '$remoteBase/preflight.txt'"
  $result | ForEach-Object { Write-Host $_ }
  Write-Host "PREFLIGHT_ONLY=PASS"
  exit 0
}

$tempDir = Join-Path $env:TEMP ("nfs-owner-demo-" + $sha)
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Force $tempDir | Out-Null

$archive = Join-Path $tempDir "need-for-strength-owner-demo.tar.gz"
$hashFile = Join-Path $tempDir "need-for-strength-owner-demo.sha256"
$commitFile = Join-Path $tempDir "need-for-strength-owner-demo.commit"

try {
  Push-Location $projectRoot
  try {
    & git archive --format=tar.gz -o $archive HEAD
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $archive)) {
      throw "Failed to create owner-demo Git archive."
    }
  }
  finally {
    Pop-Location
  }

  $hash = (Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant()
  [IO.File]::WriteAllText($hashFile, $hash + [Environment]::NewLine)
  [IO.File]::WriteAllText($commitFile, $sha + [Environment]::NewLine)

  $remoteArchive = "$remoteBase/need-for-strength-owner-demo.tar.gz"
  $remoteHash = "$remoteBase/need-for-strength-owner-demo.sha256"
  $remoteCommit = "$remoteBase/need-for-strength-owner-demo.commit"
  $remoteBootstrap = "$remoteBase/usb-bootstrap-owner-demo.sh"
  $remoteResult = "$remoteBase/result.txt"

  Invoke-Scp -LocalPath $archive -RemotePath $remoteArchive
  Invoke-Scp -LocalPath $hashFile -RemotePath $remoteHash
  Invoke-Scp -LocalPath $commitFile -RemotePath $remoteCommit
  Invoke-Scp -LocalPath $bootstrapScript -RemotePath $remoteBootstrap

  $command = "bash '$remoteBootstrap' '$remoteArchive' '$remoteHash' '$remoteCommit' '$remoteResult'"
  $result = Invoke-Ssh $command
  $result | ForEach-Object { Write-Host $_ }

  $customer = $result | Where-Object { $_ -match '^Customer site:' } | Select-Object -Last 1
  $admin = $result | Where-Object { $_ -match '^Admin portal:' } | Select-Object -Last 1
  if (-not $customer -or -not $admin) {
    throw "Bootstrap completed without returning both owner-demo URLs."
  }

  Write-Host ""
  Write-Host "OWNER_DEMO_DEPLOYMENT=PASS"
  Write-Host $customer
  Write-Host $admin
}
finally {
  Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
}
