# Get CPU usage
$cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue

# Get Memory usage
$os = Get-CimInstance Win32_OperatingSystem
$memory = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 2)

# Get Disk usage
$disk = Get-PSDrive C
$diskUsage = [math]::Round((($disk.Used / ($disk.Used + $disk.Free)) * 100), 2)

# Get Python process count
$pythonCount = (Get-Process | Where-Object {$_.ProcessName -like '*python*'}).Count
if ($null -eq $pythonCount) { $pythonCount = 0 }

# Create JSON output
$result = @{
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    cpu_usage_percent = [math]::Round($cpu, 2)
    memory_usage_percent = $memory
    disk_usage_percent = $diskUsage
    python_process_count = $pythonCount
}

$result | ConvertTo-Json
