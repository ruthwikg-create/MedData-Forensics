$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment missing. Run scripts\Setup-Windows.ps1 first." }
Write-Host "Starting MedData Forensics at http://127.0.0.1:8765" -ForegroundColor Cyan
Write-Host "Research only. No medical diagnosis or clinical validation." -ForegroundColor Yellow
& $Python start.py
