# PowerShell script to permanently remove proxy settings
# Run as Administrator

Write-Host "Removing proxy environment variables permanently..." -ForegroundColor Yellow

# Remove from User environment variables
[System.Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "User")
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "User")
[System.Environment]::SetEnvironmentVariable("http_proxy", $null, "User")
[System.Environment]::SetEnvironmentVariable("https_proxy", $null, "User")
[System.Environment]::SetEnvironmentVariable("NO_PROXY", $null, "User")
[System.Environment]::SetEnvironmentVariable("no_proxy", $null, "User")

Write-Host "✓ Removed proxy settings from User variables" -ForegroundColor Green

# Remove from System environment variables (requires Admin)
try {
    [System.Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "Machine")
    [System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "Machine")
    [System.Environment]::SetEnvironmentVariable("http_proxy", $null, "Machine")
    [System.Environment]::SetEnvironmentVariable("https_proxy", $null, "Machine")
    [System.Environment]::SetEnvironmentVariable("NO_PROXY", $null, "Machine")
    [System.Environment]::SetEnvironmentVariable("no_proxy", $null, "Machine")
    Write-Host "✓ Removed proxy settings from System variables" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not remove System variables (need Administrator rights)" -ForegroundColor Yellow
}

# Also remove from current session
Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
Remove-Item Env:NO_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:no_proxy -ErrorAction SilentlyContinue

Write-Host "✓ Removed proxy settings from current session" -ForegroundColor Green

# Check if Git has proxy settings
$gitHttpProxy = git config --global --get http.proxy 2>$null
$gitHttpsProxy = git config --global --get https.proxy 2>$null

if ($gitHttpProxy -or $gitHttpsProxy) {
    Write-Host "`nFound Git proxy settings. Removing..." -ForegroundColor Yellow
    git config --global --unset http.proxy
    git config --global --unset https.proxy
    Write-Host "✓ Removed Git proxy settings" -ForegroundColor Green
}

# Check npm proxy settings
$npmProxy = npm config get proxy 2>$null
$npmHttpsProxy = npm config get https-proxy 2>$null

if ($npmProxy -ne "null" -or $npmHttpsProxy -ne "null") {
    Write-Host "`nFound npm proxy settings. Removing..." -ForegroundColor Yellow
    npm config delete proxy
    npm config delete https-proxy
    Write-Host "✓ Removed npm proxy settings" -ForegroundColor Green
}

Write-Host "`n✅ All proxy settings have been removed!" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE for changes to take full effect." -ForegroundColor Cyan