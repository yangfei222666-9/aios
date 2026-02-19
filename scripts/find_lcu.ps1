$p = Get-Process LeagueClientUx -ErrorAction SilentlyContinue
if ($p) {
    Write-Output "PID: $($p.Id)"
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
    Write-Output "CMD: $cmd"
} else {
    Write-Output "LeagueClientUx not found"
}
