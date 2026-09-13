#Requires -Version 5.1
<#
.SYNOPSIS
  Prepara PostgreSQL local (127.0.0.1:5433) e gera map_PostGree.dat — sem Docker.

.EXAMPLE
  $env:PGPASSWORD = 'sua_senha'
  .\scripts\setup_postgresql_local.ps1
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $env:PGHOST) { $env:PGHOST = "127.0.0.1" }
if (-not $env:PGPORT) { $env:PGPORT = "5433" }
if (-not $env:PGUSER) { $env:PGUSER = "postgres" }
if (-not $env:PGDATABASE) { $env:PGDATABASE = "map" }

if (-not $env:PGPASSWORD) {
  Write-Error "Defina PGPASSWORD (senha do PostgreSQL) antes de continuar."
}

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  $py = "python"
}

& $py (Join-Path $Root "scripts\setup_postgresql_local.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Proximos passos:"
Write-Host "  Copy-Item BackEnd\.env.example BackEnd\.env"
Write-Host "  # Em BackEnd\.env: REDMAPA_SGBD=postgresql, REDMAPA_CONFIG=map_PostGree, ERP_PROVIDER=mock"
Write-Host "  .\.venv\Scripts\python.exe -m BackEnd.app"
Write-Host "  cd FrontEnd; npm run dev"
