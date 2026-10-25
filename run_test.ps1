# Script de prueba rápida para Everything MCP
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$env:PYTHONPATH = "$scriptDir\src"
& "$scriptDir\.venv\Scripts\python.exe" "$scriptDir\tests\test_searcher.py"
Write-Host "`nPresiona cualquier tecla para salir..." -ForegroundColor Cyan
[void][System.Console]::ReadKey($true)
