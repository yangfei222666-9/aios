# 批量添加版本号脚本
$skills = @(
    "agent-team-orchestration",
    "baidu-search",
    "gog",
    "hz-error-guard",
    "monitoring",
    "news-summary",
    "perplexity-search",
    "pls-agent-tools",
    "ripgrep",
    "screenshot",
    "server-health",
    "simple-monitor",
    "skill-creator",
    "sysadmin-toolbox",
    "tavily-search",
    "todoist",
    "token-monitor",
    "ui-automation",
    "ui-inspector",
    "ui-test-automation",
    "web-monitor",
    "windows-ui-automation"
)

$skillsDir = "C:\Users\A\.openclaw\workspace\skills"
$updated = 0
$skipped = 0

foreach ($skill in $skills) {
    $skillMd = Join-Path $skillsDir $skill "SKILL.md"
    
    if (-not (Test-Path $skillMd)) {
        Write-Host "[SKIP] $skill - SKILL.md not found"
        $skipped++
        continue
    }
    
    $content = Get-Content $skillMd -Raw -Encoding UTF8
    
    # 检查是否已有版本号
    if ($content -match "version:\s*\S+") {
        Write-Host "[SKIP] $skill - already has version"
        $skipped++
        continue
    }
    
    # 添加版本号（在 description 后面）
    if ($content -match "(?s)(---\s*name:\s*[^\n]+\s*description:\s*[^\n]+)(\s*---)" ) {
        $newContent = $content -replace "(?s)(---\s*name:\s*[^\n]+\s*description:\s*[^\n]+)(\s*---)", "`$1`nversion: 1.0.0`$2"
        Set-Content -Path $skillMd -Value $newContent -Encoding UTF8
        Write-Host "[OK] $skill - version added"
        $updated++
    } else {
        Write-Host "[FAIL] $skill - pattern not matched"
        $skipped++
    }
}

Write-Host "`n========================================="
Write-Host "Batch Update Complete"
Write-Host "========================================="
Write-Host "Updated: $updated"
Write-Host "Skipped: $skipped"
