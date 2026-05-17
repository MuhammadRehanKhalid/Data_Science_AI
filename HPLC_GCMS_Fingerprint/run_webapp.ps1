Set-Location $PSScriptRoot

$backendDir = Join-Path $PSScriptRoot 'webapp\backend'
$frontendDir = Join-Path $PSScriptRoot 'webapp\frontend'
$npmAvailable = $null -ne (Get-Command npm -ErrorAction SilentlyContinue)
$preferredPorts = 8000..8010
$backendPort = $preferredPorts | Where-Object {
    -not (Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue)
} | Select-Object -First 1

if (-not $backendPort) {
    throw 'No free backend port found in the 8000-8010 range.'
}

Write-Host 'Starting backend in a new PowerShell window...'
Start-Process powershell -WorkingDirectory $backendDir -ArgumentList @(
    '-NoExit',
    '-Command',
    "python -m pip install -r requirements.txt; uvicorn main:app --reload --port $backendPort"
)

Start-Process "http://localhost:$backendPort"

if ($npmAvailable) {
    Write-Host 'Starting frontend in a new PowerShell window...'
    Start-Process powershell -WorkingDirectory $frontendDir -ArgumentList @(
        '-NoExit',
        '-Command',
        "`$env:VITE_API_BASE_URL='http://127.0.0.1:$backendPort'; npm install; npm run dev"
    )
} else {
    Write-Host 'npm is not installed, so the built-in backend UI will be used instead.'
}

Write-Host ''
Write-Host 'The webapp is starting.'
Write-Host "Backend:  http://localhost:$backendPort"
if ($npmAvailable) {
    Write-Host 'Frontend: usually http://localhost:5173'
} else {
    Write-Host "Open http://localhost:$backendPort for the standalone UI."
}
Write-Host ''
Write-Host 'Close the opened window(s) to stop the app.'