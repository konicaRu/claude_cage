$ErrorActionPreference = 'Stop'
$powershellExecutable = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$syncScript = Join-Path $PSScriptRoot 'sync-cage-ssh.ps1'
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'Cage SSH Sync.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
if ((Test-Path -LiteralPath $shortcutPath) -and $shortcut.Arguments -notlike '*sync-cage-ssh.ps1*-Watch*') {
    throw 'An unrelated startup shortcut already exists; it was not changed.'
}
$shortcut.TargetPath = $powershellExecutable
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $syncScript + '" -Watch'
$shortcut.WorkingDirectory = Split-Path $PSScriptRoot -Parent
$shortcut.WindowStyle = 7
$shortcut.Description = 'Keep the Cage SSH alias (port and host key) in sync for VS Code Remote-SSH.'
$shortcut.Save()
Start-Process -FilePath $powershellExecutable -ArgumentList $shortcut.Arguments -WindowStyle Hidden
Write-Output 'Cage SSH sync helper installed and started.'
