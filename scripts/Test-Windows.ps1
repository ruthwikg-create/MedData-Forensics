$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run Setup-Windows.ps1 first." }
& $Python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Test dependencies failed" }
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed; do not report a successful build." }
Write-Host "Running Python syntax check..." -ForegroundColor Cyan
& $Python -m compileall -q backend scripts
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed" }
$Node = Get-Command node -ErrorAction SilentlyContinue
if ($Node) {
    Write-Host "Running frontend routing tests..." -ForegroundColor Cyan
    & node --test tests/test_frontend_routes.cjs tests/test_import_progress.cjs tests/test_notifications.cjs
    if ($LASTEXITCODE -ne 0) { throw "Frontend navigation tests failed" }
} else {
    Write-Warning "Node.js is not installed. Frontend routing tests were NOT run."
}
Write-Host "Automated local checks passed. Scientific validation and external security review remain separate." -ForegroundColor Green
