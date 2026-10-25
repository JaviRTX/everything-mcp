# Script para ejecutar el servidor MCP en modo stdio
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$env:PYTHONPATH = "$scriptDir\src"
& "$scriptDir\.venv\Scripts\python.exe" -m everything_mcp.server
