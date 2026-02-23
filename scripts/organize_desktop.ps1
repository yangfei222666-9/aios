# Desktop Icon Organizer
$desktop = [Environment]::GetFolderPath("Desktop")

# Create category folders
$categories = @{
    "Games" = @("Steam", "WeGame", "Epic", "LOL", "Genshin", "Honkai", "QQ", "NetEase", "Huya", "Douyu", "Douyin", "Kuaishou", "KuGou", "Nexus")
    "Office" = @("Word", "Excel", "PowerPoint", "OneNote", "Teams", "DingTalk", "Feishu", "WeCom", "WPS")
    "Communication" = @("Weixin", "QQ", "Telegram", "Discord", "Skype", "DingTalk", "WeChat")
    "DevTools" = @("Code", "Studio", "PyCharm", "Git", "Docker", "Postman", "Navicat", "DBeaver", "KANALI")
    "SystemTools" = @("Task", "Control", "Registry", "CMD", "PowerShell", "Remote", "Whisper", "Lively")
    "Media" = @("QQMusic", "CloudMusic", "KuGou", "Spotify", "iQiyi", "Tencent", "Bilibili", "Douyin", "Rainmeter", "Wallpaper")
    "Browsers" = @("Chrome", "Edge", "Firefox", "360", "Sogou")
}

# Create folders
foreach ($cat in $categories.Keys) {
    $path = Join-Path $desktop $cat
    if (-not (Test-Path $path)) {
        New-Item -Path $path -ItemType Directory -Force | Out-Null
        Write-Host "Created: $cat"
    }
}

# Get all shortcuts
$shortcuts = Get-ChildItem $desktop -Filter "*.lnk"
$moved = 0

# Categorize and move
foreach ($shortcut in $shortcuts) {
    $name = $shortcut.BaseName
    $matched = $false
    
    foreach ($cat in $categories.Keys) {
        foreach ($keyword in $categories[$cat]) {
            if ($name -like "*$keyword*") {
                $targetPath = Join-Path (Join-Path $desktop $cat) $shortcut.Name
                Move-Item $shortcut.FullName $targetPath -Force -ErrorAction SilentlyContinue
                Write-Host "Moved: $name -> $cat"
                $moved++
                $matched = $true
                break
            }
        }
        if ($matched) { break }
    }
}

Write-Host "`nOrganized $moved shortcuts"
