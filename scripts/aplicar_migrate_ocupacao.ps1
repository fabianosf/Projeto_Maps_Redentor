# Aplica migration de ocupação em tb_item_map (idempotente).
# Preferencial (usa map.dat / DAL, sem mysql.exe):
#   python scripts\aplicar_migrate_ocupacao.py
#   .\scripts\aplicar_migrate_ocupacao.ps1
#
# Alternativa com mysql.exe:
#   .\scripts\aplicar_migrate_ocupacao.ps1 -UseDal:$false

param(
    [string]$RootUser = "root",
    [string]$RootPassword = "senha",
    [string]$Database = "map",
    [switch]$UseDal = $true
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

if ($UseDal) {
    Write-Host "Aplicando via DAL (python scripts\aplicar_migrate_ocupacao.py)..."
    Push-Location $projectRoot
    try {
        $env:PYTHONPATH = $projectRoot
        python scripts\aplicar_migrate_ocupacao.py
        if ($LASTEXITCODE -ne 0) { throw "Falha na migration via DAL (exit $LASTEXITCODE)" }
    } finally {
        Pop-Location
    }
    Write-Host "Reinicie o backend: python -m BackEnd.app"
    exit 0
}

$migrateFile = Join-Path $projectRoot "database\schema_migrate_tb_item_map_ocupacao_completa.sql"

if (-not (Test-Path $migrateFile)) {
    throw "Arquivo não encontrado: $migrateFile"
}

$mysql = Get-ChildItem "C:\Program Files\MariaDB*\bin\mysql.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $mysql) {
    $fallbacks = @(
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        "C:\xampp\mysql\bin\mysql.exe"
    )
    $mysql = $fallbacks | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $mysql) {
    throw "mysql.exe não encontrado. Use: python scripts\aplicar_migrate_ocupacao.py"
}

$svc = Get-Service -Name "MariaDB" -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -ne "Running") {
    Write-Host "Iniciando serviço MariaDB..."
    Start-Service MariaDB
    Start-Sleep -Seconds 4
}

Write-Host "Aplicando $migrateFile em database=$Database ..."
Get-Content $migrateFile -Raw -Encoding UTF8 | & $mysql -u $RootUser "-p$RootPassword" $Database
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao aplicar migration (exit $LASTEXITCODE)"
}

Write-Host "OK. Verificando coluna status_escala..."
& $mysql -u $RootUser "-p$RootPassword" $Database -e "SHOW COLUMNS FROM tb_item_map LIKE 'status_escala';"
Write-Host "Reinicie o backend: python -m BackEnd.app"
