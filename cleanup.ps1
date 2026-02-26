# Windows System Cleanup Script

Write-Host "=== Starting Cleanup ===" -ForegroundColor Cyan

# 1. Clean temporary files
Write-Host "`n[1/5] Cleaning temporary files..." -ForegroundColor Yellow
$tempPaths = @(
    "$env:TEMP\*",
    "$env:LOCALAPPDATA\Temp\*",
    "C:\Windows\Temp\*"
)

$totalFreed = 0
foreach ($path in $tempPaths) {
    try {
        $parentPath = Split-Path $path
        $before = (Get-ChildItem -Path $parentPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $before) { $before = 0 }
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        $after = (Get-ChildItem -Path $parentPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $after) { $after = 0 }
        $freed = ($before - $after) / 1MB
        $totalFreed += $freed
        Write-Host "  Cleaned $parentPath : $([math]::Round($freed, 2)) MB" -ForegroundColor Green
    } catch {
        Write-Host "  Skipped $parentPath" -ForegroundColor Gray
    }
}

# 2. Clean Recycle Bin
Write-Host "`n[2/5] Emptying Recycle Bin..." -ForegroundColor Yellow
try {
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    Write-Host "  Recycle Bin emptied" -ForegroundColor Green
} catch {
    Write-Host "  Recycle Bin cleanup failed" -ForegroundColor Red
}

# 3. Clean Windows Update cache
Write-Host "`n[3/5] Cleaning Windows Update cache..." -ForegroundColor Yellow
try {
    Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
    $updatePath = "C:\Windows\SoftwareDistribution\Download"
    $before = (Get-ChildItem -Path $updatePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $before) { $before = 0 }
    Remove-Item -Path "$updatePath\*" -Recurse -Force -ErrorAction SilentlyContinue
    $after = (Get-ChildItem -Path $updatePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $after) { $after = 0 }
    $freed = ($before - $after) / 1MB
    $totalFreed += $freed
    Start-Service -Name wuauserv -ErrorAction SilentlyContinue
    Write-Host "  Cleaned update cache: $([math]::Round($freed, 2)) MB" -ForegroundColor Green
} catch {
    Write-Host "  Update cache cleanup failed" -ForegroundColor Red
}

# 4. Clean browser cache (Chrome)
Write-Host "`n[4/5] Cleaning browser cache..." -ForegroundColor Yellow
$chromePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $chromePath) {
    try {
        $before = (Get-ChildItem -Path $chromePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $before) { $before = 0 }
        Remove-Item -Path "$chromePath\*" -Recurse -Force -ErrorAction SilentlyContinue
        $after = (Get-ChildItem -Path $chromePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $after) { $after = 0 }
        $freed = ($before - $after) / 1MB
        $totalFreed += $freed
        Write-Host "  Cleaned Chrome cache: $([math]::Round($freed, 2)) MB" -ForegroundColor Green
    } catch {
        Write-Host "  Chrome cache cleanup failed" -ForegroundColor Red
    }
} else {
    Write-Host "  Chrome cache not found" -ForegroundColor Gray
}

# 5. Summary
Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host "Total freed: $([math]::Round($totalFreed, 2)) MB" -ForegroundColor Green

# Show current disk space
$disk = Get-PSDrive C
$free = [math]::Round($disk.Free / 1GB, 2)
$total = [math]::Round(($disk.Used + $disk.Free) / 1GB, 2)
Write-Host "C: drive free space: $free GB / $total GB" -ForegroundColor Cyan
