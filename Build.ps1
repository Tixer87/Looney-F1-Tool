$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if(-not(Get-Command uv -ErrorAction SilentlyContinue)){throw 'uv is required. Install uv first.'}
if(-not(Test-Path '.venv\Scripts\python.exe')){
    uv venv .venv --python 3.11
    if($LASTEXITCODE-ne 0){throw 'Python environment could not be created.'}
}
uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
if($LASTEXITCODE-ne 0){throw 'Dependencies could not be installed.'}
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath dist --workpath build LooneyF1Tool.spec
if($LASTEXITCODE-ne 0){throw 'Build failed.'}
Write-Host ''
Write-Host 'Build complete:'
Write-Host 'dist\LooneyF1Tool_1.9.1.exe'