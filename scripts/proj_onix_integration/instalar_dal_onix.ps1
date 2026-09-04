# Instala integração DAL no PROJ_ONIX (C:\PROJ_ONIX)
# Uso (PowerShell como Admin, se junction falhar):
#   .\scripts\proj_onix_integration\instalar_dal_onix.ps1

$ErrorActionPreference = "Stop"
$MapRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$OnixRoot = "C:\PROJ_ONIX"
$Templates = Join-Path $PSScriptRoot "templates"
$DalSource = Join-Path $MapRoot "DAL"

if (-not (Test-Path $OnixRoot)) {
    throw "PROJ_ONIX não encontrado em $OnixRoot"
}

Write-Host "PROJ_MAP : $MapRoot"
Write-Host "PROJ_ONIX: $OnixRoot"

# 1) Junction DAL -> PROJ_MAP\DAL (economiza espaço em C:)
$OnixDal = Join-Path $OnixRoot "DAL"
if (Test-Path $OnixDal) {
    Write-Host "DAL já existe em PROJ_ONIX (mantido)."
} else {
    cmd /c mklink /J `"$OnixDal`" `"$DalSource`"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar junction DAL" }
    Write-Host "Junction criado: $OnixDal -> $DalSource"
}

# 2) LOG local (leve)
$LogDest = Join-Path $OnixRoot "LOG"
Copy-Item (Join-Path $Templates "LOG") $LogDest -Recurse -Force

# 3) dal_factory + bridge
Copy-Item (Join-Path $Templates "dal_factory.py") (Join-Path $OnixRoot "dal_factory.py") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $OnixRoot "scripts") | Out-Null
Copy-Item (Join-Path $Templates "scripts\dal_bridge.py") (Join-Path $OnixRoot "scripts\dal_bridge.py") -Force
Copy-Item (Join-Path $PSScriptRoot "requirements-onix.txt") (Join-Path $OnixRoot "requirements.txt") -Force

# 4) ClDAL.vb
Copy-Item (Join-Path $Templates "PROJ_ONIX\ClDAL.vb") (Join-Path $OnixRoot "PROJ_ONIX\ClDAL.vb") -Force

# 5) crip.dat (usa chave de PROJ_MAP\DAL\arquivos_crip)
py -3 (Join-Path $PSScriptRoot "gerar_config_crip.py")
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar crip.dat" }

# 6) Dependências Python
py -3 -m pip install -r (Join-Path $OnixRoot "requirements.txt")

# 7) Teste conexão
Set-Location $OnixRoot
py -3 -c "from dal_factory import get_dal_instance; d=get_dal_instance(); print(d.connection_string); assert d.test_connection(); print('OK crip')"

Write-Host "`nInstalação concluída."
Write-Host "Adicione ClDAL.vb ao PROJ_ONIX.vbproj e PackageReference Newtonsoft.Json se necessário."
