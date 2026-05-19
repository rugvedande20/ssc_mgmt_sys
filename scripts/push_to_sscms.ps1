# Creates GitHub repo SSCMS (via browser) and pushes the full project.
# Requires: logged into github.com as rugvedande20 in your browser.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$remoteUrl = "git@github-rugvedande20:rugvedande20/SSCMS.git"
$createUrl = "https://github.com/new?name=SSCMS&description=School+Student+Success+and+Career+Management+System&private=true"

Write-Host "Remote will be: $remoteUrl"
Write-Host ""
Write-Host "Step 1: Create an EMPTY repo on GitHub (no README, no .gitignore)."
Write-Host "Opening: $createUrl"
Start-Process $createUrl

Read-Host "Press Enter after you have created the empty repo 'rugvedande20/SSCMS' on GitHub"

git remote set-url origin $remoteUrl

Write-Host "Checking repository access..."
$maxAttempts = 12
for ($i = 1; $i -le $maxAttempts; $i++) {
    git ls-remote origin 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Repository is reachable."
        break
    }
    if ($i -eq $maxAttempts) {
        Write-Error "Cannot access rugvedande20/SSCMS. Check SSH key and that the repo exists."
    }
    Write-Host "Waiting for repo... ($i/$maxAttempts)"
    Start-Sleep -Seconds 5
}

Write-Host "Pushing branch rugved/phase-4 as master..."
git push -u origin rugved/phase-4:master

Write-Host ""
Write-Host "Done. View at: https://github.com/rugvedande20/SSCMS"
