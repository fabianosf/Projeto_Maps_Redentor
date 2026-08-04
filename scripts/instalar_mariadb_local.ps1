# Instala MariaDB local + aplica schemas do RedMapa.
# Preferir PowerShell como Administrador.
# Uso: .\scripts\instalar_mariadb_local.ps1

param(
    [string]$RootPassword = "senha",
    [string]$ServiceName = "MariaDB",
    [int]$Port = 3306
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectRoot "database\instalar_mariadb_local.log"
$MsiUrl = "https://downloads.mariadb.org/rest-api/mariadb/12.3.2/mariadb-12.3.2-winx64.msi"
$MsiPath = Join-Path $env:TEMP "mariadb-12.3.2-winx64.msi"

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

Write-Log "=== Início instalar_mariadb_local ==="
Write-Log "ProjectRoot=$ProjectRoot"

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Log "AVISO: não está como Administrador — instalação MSI pode falhar."
}

$mysqlExisting = Get-ChildItem "C:\Program Files\MariaDB*\bin\mysql.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName

if (-not $mysqlExisting) {
    Write-Log "Baixando MSI MariaDB 12.3.2..."
    Invoke-WebRequest -Uri $MsiUrl -OutFile $MsiPath -UseBasicParsing
    Write-Log "Instalando MSI (serviço=$ServiceName porta=$Port)..."
    $installArgs = "/i `"$MsiPath`" SERVICENAME=$ServiceName PASSWORD=$RootPassword PORT=$Port UTF8=1 /qn /norestart"
    $p = Start-Process msiexec.exe -ArgumentList $installArgs -Wait -PassThru
    Write-Log "msiexec exit=$($p.ExitCode)"
    if ($p.ExitCode -ne 0 -and $p.ExitCode -ne 3010) {
        throw "Instalação MariaDB falhou com código $($p.ExitCode)"
    }
    Start-Sleep -Seconds 8
} else {
    Write-Log "MariaDB já instalado: $mysqlExisting"
}

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    # Alguns installs usam nome com versão
    $svc = Get-Service | Where-Object { $_.Name -match 'MariaDB' } | Select-Object -First 1
}
if ($svc) {
    Write-Log "Serviço encontrado: $($svc.Name) status=$($svc.Status)"
    if ($svc.Status -ne "Running") {
        Set-Service -Name $svc.Name -StartupType Automatic -ErrorAction SilentlyContinue
        Start-Service -Name $svc.Name
        Start-Sleep -Seconds 6
    }
} else {
    Write-Log "AVISO: serviço MariaDB não encontrado após instalação."
}

$mysql = Get-ChildItem "C:\Program Files\MariaDB*\bin\mysql.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $mysql) { throw "mysql.exe não encontrado após instalação." }
Write-Log "mysql=$mysql"

# Aguarda porta
$okPort = $false
for ($i = 1; $i -le 30; $i++) {
    $tn = Test-NetConnection 127.0.0.1 -Port $Port -WarningAction SilentlyContinue
    if ($tn.TcpTestSucceeded) { $okPort = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $okPort) { throw "Porta $Port não abriu após instalação." }
Write-Log "Porta $Port OK"

$files = @(
    (Join-Path $ProjectRoot "database\schema.sql"),
    (Join-Path $ProjectRoot "database\schema_operacional.sql"),
    (Join-Path $ProjectRoot "database\schema_seed.sql")
)
foreach ($file in $files) {
    if (-not (Test-Path $file)) { throw "Arquivo não encontrado: $file" }
    Write-Log "Aplicando $file"
    Get-Content $file -Raw -Encoding UTF8 | & $mysql -u root "-p$RootPassword" --protocol=tcp -P $Port
    if ($LASTEXITCODE -ne 0) { throw "Falha ao aplicar $file (exit $LASTEXITCODE)" }
}

Write-Log "Regenerando configs criptografadas"
Set-Location $ProjectRoot
python scripts\gerar_configs_map.py

Write-Log "Teste usumap"
& $mysql -u usumap "-p$RootPassword" --protocol=tcp -P $Port -e "USE map; SELECT matricula, trocar_senha FROM tb_usuario;"
if ($LASTEXITCODE -ne 0) { throw "Teste usumap falhou" }

Write-Log "=== Concluído com sucesso ==="
Write-Host ""
Write-Host "Próximo: reinicie o Backend (python -m BackEnd.app)"
Write-Host "Login teste: 1001 / 12345"
