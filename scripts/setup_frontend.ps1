# Reinstala as dependencias do FrontEnd em C:\RedMapaDev\FrontEnd (economia de disco no E:).
#
# Uso:
#   .\scripts\setup_frontend.ps1

$ErrorActionPreference = "Stop"
$projFront = Join-Path (Split-Path -Parent $PSScriptRoot) "FrontEnd"
$devRoot = "C:\RedMapaDev"
$devFront = Join-Path $devRoot "FrontEnd"

New-Item -ItemType Directory -Force -Path $devRoot | Out-Null

Write-Host "Copiando projeto FrontEnd para $devFront ..."
if (Test-Path $devFront) {
    # Preserva node_modules se existir; atualiza o restante
    robocopy $projFront $devFront /E /XD node_modules .expo dist /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
} else {
    robocopy $projFront $devFront /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
}
if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar (robocopy $LASTEXITCODE)" }

# Cache npm na rede (nao ocupa C:/E:)
npm config set cache "G:\RedMapaDeps\npm-cache" --location=user
npm config set fund false --location=user
npm config set audit false --location=user

Set-Location $devFront
Write-Host "npm install em $devFront ..."
npm install --no-fund --no-audit

Copy-Item (Join-Path $devFront "package-lock.json") (Join-Path $projFront "package-lock.json") -Force

Write-Host ""
Write-Host "OK. Proximo passo: .\scripts\dev_frontend.ps1"
Write-Host "C livres GB:" ([math]::Round((Get-PSDrive C).Free/1GB, 2))
