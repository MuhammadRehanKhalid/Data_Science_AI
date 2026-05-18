Set-Location $PSScriptRoot

$python = Get-Command python -ErrorAction Stop

Write-Host 'Installing build dependency: pyinstaller'
& $python.Source -m pip install --upgrade pip pyinstaller

Write-Host 'Building the GUI executable'
& $python.Source -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name HPLC_GCMS_Pipeline `
    --paths . `
    pipeline_gui.py

Write-Host ''
Write-Host 'Build finished.'
Write-Host 'Executable folder: dist\HPLC_GCMS_Pipeline'
Write-Host 'Run: dist\HPLC_GCMS_Pipeline\HPLC_GCMS_Pipeline.exe'