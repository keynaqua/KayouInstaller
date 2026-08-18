$ErrorActionPreference = 'Stop'

$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python 3.13 est introuvable : $python"
}

& $python -m PyInstaller --noconfirm --clean KayouInstaller.spec
if ($LASTEXITCODE -ne 0) {
    throw "La compilation PyInstaller a échoué (code $LASTEXITCODE)."
}

Write-Host 'Build terminé : dist\KayouInstaller.exe'
