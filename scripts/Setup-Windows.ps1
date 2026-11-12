$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host "MedData Forensics - local Windows research environment" -ForegroundColor Cyan
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $PythonCmd = $null
    try { & py -3.11 --version | Out-Null; if ($LASTEXITCODE -eq 0) { $PythonCmd = "py" } } catch { }
    if ($PythonCmd -eq "py") {
        & py -3.11 -m venv .venv
    } else {
        & python -m venv .venv
    }
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed" }
Write-Host "Setup completed. Start the app with: powershell -ExecutionPolicy Bypass -File .\scripts\Start-Windows.ps1" -ForegroundColor Green
