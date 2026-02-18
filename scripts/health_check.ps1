# health_check.ps1 - OpenClaw System Health Check
# Checks: Node.js, Python, Ports, Config, Providers
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\scripts\health_check.ps1"

$ErrorActionPreference = "SilentlyContinue"
$pass = 0; $fail = 0; $warn = 0; $results = @()
$startTime = Get-Date

function Check($name, $status, $detail) {
    $script:results += [PSCustomObject]@{ Name=$name; Status=$status; Detail=$detail }
    switch ($status) { "PASS" { $script:pass++ } "FAIL" { $script:fail++ } "WARN" { $script:warn++ } }
    $icon = switch ($status) { "PASS" { "[OK]" } "FAIL" { "[FAIL]" } "WARN" { "[WARN]" } }
    Write-Host "$icon $name - $detail"
}

Write-Host "========================================="
Write-Host "  OpenClaw Health Check"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================="
Write-Host ""

# --- Node.js ---
$node = & node --version 2>&1
if ($LASTEXITCODE -eq 0) { Check "Node.js" "PASS" $node.ToString().Trim() }
else { Check "Node.js" "FAIL" "Not found in PATH" }

# --- npm ---
$npm = & npm --version 2>&1
if ($LASTEXITCODE -eq 0) { Check "npm" "PASS" "v$($npm.ToString().Trim())" }
else { Check "npm" "FAIL" "Not found in PATH" }

# --- Python (check known paths + PATH) ---
$pyPaths = @(
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)
$pyFound = $false
foreach ($pp in $pyPaths) {
    if (Test-Path $pp) {
        $pyVer = & $pp --version 2>&1
        Check "Python" "PASS" "$($pyVer.ToString().Trim()) ($pp)"
        $pyFound = $true; break
    }
}
if (-not $pyFound) {
    $py = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) { Check "Python" "PASS" $py.ToString().Trim() }
    else { Check "Python" "FAIL" "Not found (checked PATH + common locations)" }
}

# --- pip ---
$pipFound = $false
foreach ($pp in $pyPaths) {
    $pipPath = Join-Path (Split-Path $pp) "Scripts\pip.exe"
    if (Test-Path $pipPath) {
        $pipVer = & $pipPath --version 2>&1
        Check "pip" "PASS" $pipVer.ToString().Trim().Split(" ")[1]
        $pipFound = $true; break
    }
}
if (-not $pipFound) {
    $pip = & pip --version 2>&1
    if ($LASTEXITCODE -eq 0) { Check "pip" "PASS" $pip.ToString().Trim().Split(" ")[1] }
    else { Check "pip" "WARN" "Not found" }
}

# --- OpenClaw Gateway (check by port + process) ---
$gwPort = Get-NetTCPConnection -LocalPort 3007 -State Listen 2>$null
if (-not $gwPort) { $gwPort = Get-NetTCPConnection -LocalPort 3008 -State Listen 2>$null }
if ($gwPort) {
    $gwPid = $gwPort[0].OwningProcess
    $gwProc = (Get-Process -Id $gwPid 2>$null).ProcessName
    Check "OpenClaw Gateway" "PASS" "Running (PID $gwPid $gwProc, port $($gwPort[0].LocalPort))"
} else {
    $nodeProcs = Get-Process -Name "node" 2>$null | Where-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" 2>$null).CommandLine
        $cmd -and $cmd -match "openclaw|gateway"
    }
    if ($nodeProcs) { Check "OpenClaw Gateway" "PASS" "Running (PID $($nodeProcs[0].Id))" }
    else { Check "OpenClaw Gateway" "WARN" "Process not detected (may use different port)" }
}

# --- Config file ---
$configDir = "$env:USERPROFILE\.openclaw"
$configFound = $false
foreach ($cf in @("config.yaml","config.yml","config.json")) {
    $cfPath = Join-Path $configDir $cf
    if (Test-Path $cfPath) {
        $size = (Get-Item $cfPath).Length
        Check "Config" "PASS" "$cf ($size bytes)"
        $configFound = $true; break
    }
}
if (-not $configFound) { Check "Config" "WARN" "No config file in $configDir" }

# --- Workspace ---
$wsPath = "$env:USERPROFILE\.openclaw\workspace"
if (Test-Path $wsPath) {
    $fileCount = (Get-ChildItem $wsPath -Recurse -File 2>$null).Count
    Check "Workspace" "PASS" "$fileCount files in workspace"
} else { Check "Workspace" "WARN" "Workspace dir not found" }

# --- Memory ---
$os = Get-CimInstance Win32_OperatingSystem
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$pct = [math]::Round(($totalGB - $freeGB) / $totalGB * 100)
if ($pct -lt 80) { Check "Memory" "PASS" "${pct}% used (${freeGB}GB free / ${totalGB}GB)" }
elseif ($pct -lt 90) { Check "Memory" "WARN" "${pct}% used (${freeGB}GB free / ${totalGB}GB)" }
else { Check "Memory" "FAIL" "${pct}% used - CRITICAL (${freeGB}GB free / ${totalGB}GB)" }

# --- Disks ---
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $freeG = [math]::Round($_.FreeSpace/1GB, 1)
    $totalG = [math]::Round($_.Size/1GB, 1)
    $name = "Disk $($_.DeviceID)"
    if ($freeG -gt 20) { Check $name "PASS" "${freeG}GB / ${totalG}GB free" }
    elseif ($freeG -gt 5) { Check $name "WARN" "${freeG}GB free (low)" }
    else { Check $name "FAIL" "${freeG}GB free (critical)" }
}

# --- GPU ---
$gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }
if ($gpu) { Check "NVIDIA GPU" "PASS" "$($gpu.Name) - Driver $($gpu.DriverVersion) - $($gpu.Status)" }
else { Check "NVIDIA GPU" "WARN" "Not detected via WMI" }

# --- Provider connectivity ---
$providers = @(
    @{Name="Anthropic API"; Host="api.anthropic.com"},
    @{Name="OpenAI API"; Host="api.openai.com"},
    @{Name="Telegram API"; Host="api.telegram.org"}
)
foreach ($prov in $providers) {
    try {
        $dns = [System.Net.Dns]::GetHostAddresses($prov.Host)
        if ($dns.Count -gt 0) { Check $prov.Name "PASS" "Reachable ($($dns[0]))" }
        else { Check $prov.Name "FAIL" "DNS resolve failed" }
    } catch { Check $prov.Name "FAIL" "Unreachable" }
}

# --- Summary ---
$elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
$total = $pass + $fail + $warn
Write-Host ""
Write-Host "========================================="
Write-Host "  Results: $pass PASS / $warn WARN / $fail FAIL  ($total checks in ${elapsed}s)"
if ($fail -eq 0 -and $warn -eq 0) { Write-Host "  Status: ALL GREEN" }
elseif ($fail -eq 0) { Write-Host "  Status: MOSTLY OK (warnings)" }
else { Write-Host "  Status: ISSUES FOUND" }
Write-Host "========================================="

if ($fail -gt 0) { exit 1 } else { exit 0 }
