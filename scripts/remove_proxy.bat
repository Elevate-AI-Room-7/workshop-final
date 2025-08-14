@echo off
echo Removing proxy settings...

REM Unset proxy environment variables
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
set NO_PROXY=
set no_proxy=

echo.
echo Proxy variables cleared for current session.
echo.
echo To remove permanently from Windows:
echo 1. Open System Properties (Win + Pause)
echo 2. Click "Advanced system settings"
echo 3. Click "Environment Variables"
echo 4. Remove HTTP_PROXY, HTTPS_PROXY, http_proxy, https_proxy from both User and System variables
echo.
echo Or run these commands in Administrator PowerShell:
echo [System.Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "User")
echo [System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "User")
echo [System.Environment]::SetEnvironmentVariable("http_proxy", $null, "User")
echo [System.Environment]::SetEnvironmentVariable("https_proxy", $null, "User")
echo [System.Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "Machine")
echo [System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "Machine")
echo [System.Environment]::SetEnvironmentVariable("http_proxy", $null, "Machine")
echo [System.Environment]::SetEnvironmentVariable("https_proxy", $null, "Machine")
echo.
pause