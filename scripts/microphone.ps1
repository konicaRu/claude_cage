param([ValidateSet('start', 'stop')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
$pythonExecutable = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    $pythonExecutable = (Get-Command pythonw.exe -ErrorAction Stop).Source
}
$bridgeScript = Join-Path $PSScriptRoot 'microphone_bridge.py'
$bridgeArgs = @(('"' + $bridgeScript + '"'))
if ($Action -eq 'stop') { $bridgeArgs += '--stop' }
Start-Process -FilePath $pythonExecutable -ArgumentList $bridgeArgs -WindowStyle Hidden
