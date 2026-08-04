# Sincroniza o codigo do FrontEnd (E:) para C:\RedMapaDev\FrontEnd e inicia o Expo.
# node_modules fica em C: (unico disco local com espaco suficiente).
#
# Uso (celular fisico, mesma Wi-Fi):
#   $env:EXPO_PUBLIC_API_URL = "http://SEU_IP:5000/api/v1"
#   .\scripts\dev_frontend.ps1

$ErrorActionPreference = "Stop"
$projFront = Join-Path (Split-Path -Parent $PSScriptRoot) "FrontEnd"
$devFront = "C:\RedMapaDev\FrontEnd"

if (-not (Test-Path (Join-Path $devFront "node_modules"))) {
    Write-Error "Dependencias nao encontradas em $devFront. Execute: .\scripts\setup_frontend.ps1"
}

Write-Host "Sincronizando codigo E: -> C:\RedMapaDev\FrontEnd ..."
robocopy $projFront $devFront /E /XD node_modules .expo dist /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Falha ao sincronizar (robocopy $LASTEXITCODE)" }

Set-Location $devFront
Write-Host "Expo em $devFront"
Write-Host "Abra o Expo Go no celular e escaneie o QR code."
Write-Host "API: $env:EXPO_PUBLIC_API_URL"
Write-Host ""

npx expo start
