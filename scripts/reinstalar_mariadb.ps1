# Reinstala MariaDB — requer execução elevada (Administrador)
$ErrorActionPreference = "Stop"

$RootPassword = "senha"
$ServiceName = "MariaDB"
$ProductCodeOld = "{BA0C1296-950D-4856-B795-65EBCCCBF2D2}"
$MsiUrl = "https://downloads.mariadb.org/rest-api/mariadb/12.3.2/mariadb-12.3.2-winx64.msi"
$MsiPath = Join-Path $env:TEMP "mariadb-12.3.2-winx64.msi"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SchemaFile = Join-Path $ProjectRoot "database\schema.sql"
$LogFile = Join-Path $ProjectRoot "database\reinstalar_mariadb.log"

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

Write-Log "=== Início reinstalação MariaDB ==="

# Remover serviço órfão
$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc) {
    Write-Log "Removendo serviço órfão $ServiceName"
    sc.exe stop $ServiceName | Out-Null
    Start-Sleep -Seconds 2
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

# Desinstalar MSI antigo se existir
Write-Log "Desinstalando MSI anterior (se existir)"
$p = Start-Process msiexec.exe -ArgumentList "/x $ProductCodeOld CLEANUPDATA=1 /qn /norestart" -Wait -PassThru
Write-Log "Uninstall exit: $($p.ExitCode)"

Start-Sleep -Seconds 5

# Baixar e instalar
Write-Log "Baixando MSI"
Invoke-WebRequest -Uri $MsiUrl -OutFile $MsiPath -UseBasicParsing

Write-Log "Instalando MariaDB 12.3.2"
$installArgs = "/i `"$MsiPath`" SERVICENAME=$ServiceName PASSWORD=$RootPassword PORT=3306 UTF8=1 /qn /norestart"
$p = Start-Process msiexec.exe -ArgumentList $installArgs -Wait -PassThru
Write-Log "Install exit: $($p.ExitCode)"
if ($p.ExitCode -ne 0) { throw "Instalação falhou com código $($p.ExitCode)" }

Start-Sleep -Seconds 10

Write-Log "Iniciando serviço"
Set-Service -Name $ServiceName -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service -Name $ServiceName
Start-Sleep -Seconds 6

$mysql = Get-ChildItem "C:\Program Files\MariaDB*\bin\mysql.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $mysql) { throw "mysql.exe não encontrado" }
Write-Log "mysql: $mysql"

Write-Log "Aplicando schema.sql"
Get-Content $SchemaFile -Raw | & $mysql -u root "-p$RootPassword"
if ($LASTEXITCODE -ne 0) { throw "schema.sql falhou" }

Write-Log "Regenerando map_MariaDB.dat"
Set-Location $ProjectRoot
python scripts\gerar_configs_map.py

Write-Log "Testando usumap"
& $mysql -u usumap "-p$RootPassword" -e "USE map; SHOW TABLES;"
if ($LASTEXITCODE -ne 0) { throw "Teste usumap falhou" }

Write-Log "=== Concluído com sucesso ==="
