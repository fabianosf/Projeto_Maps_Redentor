# Aplica schema + operacional + seed no MariaDB local (não interativo).
# Pré-requisito: serviço MariaDB rodando na porta 3306.
# Uso (PowerShell como Admin, se necessário):
#   .\scripts\aplicar_schema_map.ps1
#   .\scripts\aplicar_schema_map.ps1 -RootPassword senha

param(
    [string]$RootUser = "root",
    [string]$RootPassword = "senha"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

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
    throw "mysql.exe não encontrado. Instale o MariaDB (scripts\reinstalar_mariadb.ps1 como Administrador)."
}

$svc = Get-Service -Name "MariaDB" -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -ne "Running") {
    Write-Host "Iniciando serviço MariaDB..."
    Start-Service MariaDB
    Start-Sleep -Seconds 4
}

$files = @(
    (Join-Path $projectRoot "database\schema.sql"),
    (Join-Path $projectRoot "database\schema_operacional.sql"),
    (Join-Path $projectRoot "database\schema_seed.sql")
)

foreach ($file in $files) {
    if (-not (Test-Path $file)) { throw "Arquivo não encontrado: $file" }
    Write-Host "Aplicando $file ..."
    Get-Content $file -Raw | & $mysql -u $RootUser "-p$RootPassword"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao aplicar $file (exit $LASTEXITCODE)" }
}

Write-Host "OK. Teste: matrícula 1001 / senha 12345"
Write-Host "Health: http://127.0.0.1:5000/api/v1/health"
