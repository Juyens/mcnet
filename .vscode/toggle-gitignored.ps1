# Flips "explorer.excludeGitIgnore" in .vscode/settings.json.
# Bound to a task so the Explorer can be toggled with a single keystroke.

$ErrorActionPreference = 'Stop'

$path = Join-Path $PSScriptRoot 'settings.json'
$text = [System.IO.File]::ReadAllText($path)

$pattern = '("explorer\.excludeGitIgnore"\s*:\s*)(true|false)'
$current = [regex]::Match($text, $pattern)

if ($current.Success) {
    $next = if ($current.Groups[2].Value -eq 'true') { 'false' } else { 'true' }
    $text = [regex]::Replace($text, $pattern, "`${1}$next")
} else {
    $next = 'true'
    $text = [regex]::Replace($text, '^\s*\{', "{`n  `"explorer.excludeGitIgnore`": true,")
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($path, $text, $utf8NoBom)

if ($next -eq 'true') {
    Write-Host 'gitignored files hidden'
} else {
    Write-Host 'gitignored files visible'
}
