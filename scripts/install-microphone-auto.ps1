$ErrorActionPreference = 'Stop'
$pythonExecutable = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    $pythonExecutable = (Get-Command pythonw.exe -ErrorAction Stop).Source
}
$bridgeScript = Join-Path $PSScriptRoot 'microphone_bridge.py'
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'Cage Microphone.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
if ((Test-Path -LiteralPath $shortcutPath) -and $shortcut.Arguments -notlike '*microphone_bridge.py*--watch*') {
    throw 'An unrelated startup shortcut already exists; it was not changed.'
}
$shortcut.TargetPath = $pythonExecutable
$shortcut.Arguments = '"' + $bridgeScript + '" --watch'
$shortcut.WorkingDirectory = Split-Path $PSScriptRoot -Parent
$shortcut.WindowStyle = 7
$shortcut.Description = 'Connect Realtek microphone automatically while Cage is running.'
$shortcut.Save()
Start-Process -FilePath $pythonExecutable -ArgumentList $shortcut.Arguments -WindowStyle Hidden
Write-Output 'Cage microphone automatic helper installed and started.'
