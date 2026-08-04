# Ativa / executa o BackEnd RedMapa.
# Usa o Python do sistema (pacotes ja instalados) — sem venv local (economia de disco).
#
# Uso:
#   .\scripts\dev_backend.ps1

$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot
Set-Location $proj

Write-Host "RedMapa BackEnd — http://0.0.0.0:5000"
Write-Host "Projeto: $proj"
Write-Host "Descubra o IP do PC (para o celular): ipconfig"
Write-Host ""

$env:FLASK_DEBUG = "1"
python -m BackEnd.app
