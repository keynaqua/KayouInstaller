$ErrorActionPreference = 'Stop'

$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python 3.13 est introuvable : $python"
}

& $python -m PyInstaller --noconfirm --clean KayouInstaller.spec
if ($LASTEXITCODE -ne 0) {
    throw "La compilation PyInstaller a échoué (code $LASTEXITCODE)."
}

$payload = Join-Path $PSScriptRoot 'dist\KayouInstaller.runtime.exe'
$output = Join-Path $PSScriptRoot 'dist\KayouInstaller.exe'
Move-Item -LiteralPath $output -Destination $payload -Force

$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    throw "Le compilateur Windows C# est introuvable : $compiler"
}

& $compiler /nologo /target:winexe /optimize+ /reference:System.Windows.Forms.dll `
    "/win32icon:$PSScriptRoot\assets\icons\loveball.ico" `
    "/resource:$payload,KayouInstaller.Payload" `
    "/out:$output" `
    "$PSScriptRoot\bootstrap\Program.cs"
if ($LASTEXITCODE -ne 0) {
    throw "La compilation du bootstrap a échoué (code $LASTEXITCODE)."
}

Remove-Item -LiteralPath $payload -Force
Write-Host 'Build terminé : dist\KayouInstaller.exe (bootstrap autonome)'
