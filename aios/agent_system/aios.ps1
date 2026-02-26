#!/usr/bin/env pwsh
# AIOS Interactive CLI
param(
    [Parameter(Mandatory=$false)]
    [string]$Instruction
)

$pythonPath = "C:\Program Files\Python312\python.exe"
$orchestratorPath = "orchestrator.py"
$demoPath = "demo.ps1"

if ($Instruction) {
    # Single execution mode
    Write-Host "AIOS Orchestrator" -ForegroundColor Cyan
    & $pythonPath -X utf8 $orchestratorPath $Instruction
    Write-Host ""
    Write-Host "Executing tasks..." -ForegroundColor Yellow
    & .\$demoPath
} else {
    # Interactive mode
    Write-Host "AIOS Interactive CLI" -ForegroundColor Cyan
    Write-Host "Enter instructions, Ctrl+C to exit" -ForegroundColor Gray
    Write-Host ""
    
    while ($true) {
        Write-Host "You: " -NoNewline -ForegroundColor Green
        $input = Read-Host
        
        if ([string]::IsNullOrWhiteSpace($input)) {
            continue
        }
        
        Write-Host ""
        & $pythonPath -X utf8 $orchestratorPath $input
        Write-Host ""
        Write-Host "Executing tasks..." -ForegroundColor Yellow
        & .\$demoPath
        Write-Host ""
    }
}
