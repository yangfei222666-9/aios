$cpu = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1
$cpuUsage = [math]::Round($cpu.CounterSamples.CookedValue, 1)

$mem = Get-CimInstance Win32_OperatingSystem
$memUsed = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 1)
$memTotal = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 1)
$memPercent = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)

$disk = Get-PSDrive C
$diskUsed = [math]::Round($disk.Used / 1GB, 1)
$diskTotal = [math]::Round(($disk.Used + $disk.Free) / 1GB, 1)
$diskPercent = [math]::Round($disk.Used / ($disk.Used + $disk.Free) * 100, 1)

$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1

Write-Host "=== 系统状态 ==="
Write-Host "运行时间: $($mem.LastBootUpTime.ToString('yyyy-MM-dd HH:mm'))"
Write-Host ""
Write-Host "CPU: $cpuUsage%"
Write-Host "内存: $memUsed GB / $memTotal GB ($memPercent%)"
Write-Host "磁盘C: $diskUsed GB / $diskTotal GB ($diskPercent%)"
Write-Host "显卡: $($gpu.Name)"
