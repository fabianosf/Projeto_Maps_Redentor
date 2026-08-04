# Executa schema.sql no MariaDB local (Windows)
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$schemaFile = Join-Path $projectRoot "database\schema.sql"

$mysqlCandidates = @(
    "C:\Program Files\MariaDB 12.1\bin\mysql.exe",
    "C:\Program Files\MariaDB 11.4\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    "C:\xampp\mysql\bin\mysql.exe"
)

$mysql = $mysqlCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $mysql) {
    Write-Error "Cliente mysql/mariadb não encontrado. Instale o MariaDB ou ajuste o caminho no script."
}

$service = Get-Service -Name "MariaDB" -ErrorAction SilentlyContinue
if ($service -and $service.Status -ne "Running") {
    Write-Host "AVISO: serviço MariaDB está parado. Inicie em services.msc (como administrador) e execute novamente."
}

$user = Read-Host "Usuário MariaDB [root]"
if ([string]::IsNullOrWhiteSpace($user)) { $user = "root" }

$secure = Read-Host "Senha MariaDB (Enter se vazia)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$password = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)

$args = @("-u", $user)
if ($password) { $args += @("-p$password") }

Write-Host "Aplicando schema em database/schema.sql ..."
Get-Content $schemaFile | & $mysql @args
if ($LASTEXITCODE -eq 0) {
    Write-Host "Banco 'map' criado/atualizado com sucesso."
} else {
    Write-Error "Falha ao executar schema.sql (código $LASTEXITCODE)."
}
