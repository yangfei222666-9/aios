$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$destDir = Join-Path $env:USERPROFILE "Desktop\autolearn_backups"
$archive = Join-Path $destDir "autolearn_backup_$ts.zip"
$tmpDir = Join-Path $env:TEMP "backup_$ts"
$ws = Join-Path $env:USERPROFILE ".openclaw\workspace"
$aram = Join-Path $env:USERPROFILE "Desktop\ARAM-Helper"

New-Item -ItemType Directory -Force -Path $destDir | Out-Null
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

if (Test-Path (Join-Path $ws "memory")) {
    Copy-Item -Path (Join-Path $ws "memory") -Destination (Join-Path $tmpDir "memory") -Recurse
}

foreach ($f in @("MEMORY.md","AGENTS.md","SOUL.md","USER.md","HEARTBEAT.md","TOOLS.md","IDENTITY.md")) {
    $src = Join-Path $ws $f
    if (Test-Path $src) { Copy-Item $src (Join-Path $tmpDir $f) }
}

if (Test-Path $aram) {
    $ad = Join-Path $tmpDir "aram"
    New-Item -ItemType Directory -Force -Path $ad | Out-Null
    foreach ($f in @("aram_data.json","champions_raw.json","items_cn.json")) {
        $src = Join-Path $aram $f
        if (Test-Path $src) { Copy-Item $src (Join-Path $ad $f) }
    }
}

$aiosData = Join-Path $ws "aios\data"
if (Test-Path $aiosData) {
    Copy-Item -Path $aiosData -Destination (Join-Path $tmpDir "aios_data") -Recurse
}

$autolearnData = Join-Path $ws "autolearn\data"
if (Test-Path $autolearnData) {
    Copy-Item -Path $autolearnData -Destination (Join-Path $tmpDir "autolearn_data") -Recurse
}

Compress-Archive -Path (Join-Path $tmpDir "*") -DestinationPath $archive -Force
Remove-Item -Path $tmpDir -Recurse -Force

Get-ChildItem $destDir -Filter "autolearn_backup_*.zip" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
    Remove-Item -Force

$size = [math]::Round((Get-Item $archive).Length / 1MB, 2)
Write-Host "backup done: $archive ($size MB)"
