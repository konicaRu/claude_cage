<#
Keeps the "Cage" SSH alias (used by VS Code Remote-SSH) in sync with the running Cage VM.

After every Cage/VM restart the forwarded SSH port and the guest host key can change.
This script reads the current port from the Lima-generated ssh.config, fetches the guest
ED25519 host key through that trusted Lima channel, and rewrites only:
  - the "Port" line in ~/.ssh/cage.config
  - the pinned key in ~/.ssh/cage_known_hosts
Strict host key checking stays enabled. Nothing is written when values are already current.

Usage:
  .\sync-cage-ssh.ps1            one-shot sync
  .\sync-cage-ssh.ps1 -Watch     keep running and re-sync whenever the VM changes
#>
param(
    [switch]$Watch,
    [int]$IntervalSeconds = 5,
    [string]$LimaRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) '.local\CageData\state\lima'),
    [string]$SshConfigPath = (Join-Path $env:USERPROFILE '.ssh\cage.config'),
    [string]$KnownHostsPath = (Join-Path $env:USERPROFILE '.ssh\cage_known_hosts'),
    [string]$HostKeyAlias = 'cage-linux',
    [string]$LogPath = (Join-Path (Split-Path $PSScriptRoot -Parent) '.local\ssh-sync.log')
)
$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Log([string]$Message) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    if ($Watch) {
        try { [IO.File]::AppendAllText($LogPath, $line + [Environment]::NewLine, $utf8NoBom) } catch { }
    } else {
        Write-Host $line
    }
}

function Write-FileAtomic([string]$Path, [string]$Content) {
    $tmp = "$Path.tmp"
    [IO.File]::WriteAllText($tmp, $Content, $utf8NoBom)
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

# Returns $true when something was changed, $false when already current or VM not ready.
function Sync-CageSsh {
    $limaConfig = Get-ChildItem -Path $LimaRoot -Directory -Filter 'claude-cage-workspace-*' -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName 'ssh.config' } |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
    if (-not $limaConfig) { return $false }

    $content = Get-Content -LiteralPath $limaConfig -Encoding UTF8
    $hostAlias = ($content | Where-Object { $_ -match '^Host\s+(\S+)' } | Select-Object -First 1) -replace '^Host\s+', ''
    $portLine = $content | Where-Object { $_ -match '^\s*Port\s+(\d+)\s*$' } | Select-Object -First 1
    if (-not $hostAlias -or -not $portLine) { return $false }
    $port = [int](($portLine -replace '\D', ''))

    # VM must be accepting connections on the forwarded port.
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect('127.0.0.1', $port, $null, $null)
        if (-not $connect.AsyncWaitHandle.WaitOne(2000) -or -not $client.Connected) { return $false }
    } catch { return $false } finally { $client.Close() }

    # Host key via the Lima channel (key-based, no password), not via the user's pinned alias.
    $out = & ssh.exe -F $limaConfig -o ConnectTimeout=10 $hostAlias 'cat /etc/ssh/ssh_host_ed25519_key.pub' 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $false }
    $keyLine = ($out | Where-Object { $_ -match '^ssh-ed25519\s+[A-Za-z0-9+/=]+' } | Select-Object -First 1)
    if (-not $keyLine) { return $false }
    $parts = $keyLine.Trim() -split '\s+'
    $wantKnownHosts = "$HostKeyAlias $($parts[0]) $($parts[1])`n"

    $changed = $false

    # Port line in cage.config (only the Port value is touched).
    $cfg = [IO.File]::ReadAllText($SshConfigPath)
    if ($cfg -notmatch '(?m)^\s*Port\s+\d+') { throw "No Port line in $SshConfigPath" }
    $newCfg = [regex]::Replace($cfg, '(?m)^(\s*Port\s+)\d+', { param($m) $m.Groups[1].Value + $port })
    if ($newCfg -ne $cfg) {
        Write-FileAtomic $SshConfigPath $newCfg
        Write-Log "Updated Port in $(Split-Path $SshConfigPath -Leaf) to $port"
        $changed = $true
    }

    # Pinned host key.
    $curKnown = if (Test-Path -LiteralPath $KnownHostsPath) { [IO.File]::ReadAllText($KnownHostsPath) } else { '' }
    if ($curKnown -ne $wantKnownHosts) {
        Write-FileAtomic $KnownHostsPath $wantKnownHosts
        Write-Log "Updated pinned host key in $(Split-Path $KnownHostsPath -Leaf)"
        $changed = $true
    }
    return $changed
}

if (-not $Watch) {
    if (Sync-CageSsh) { Write-Log 'Done.' }
    else { Write-Log 'Nothing changed (already current, or Cage VM is not ready).' }
    return
}

# Watch mode: single instance, poll, log only changes.
$mutex = New-Object System.Threading.Mutex($false, 'Local\CageSshSync')
if (-not $mutex.WaitOne(0)) { return }
try {
    New-Item -ItemType Directory -Force -Path (Split-Path $LogPath -Parent) | Out-Null
    Write-Log 'Watcher started.'
    while ($true) {
        try { [void](Sync-CageSsh) } catch { Write-Log "Error: $($_.Exception.Message)" }
        Start-Sleep -Seconds $IntervalSeconds
    }
} finally {
    $mutex.ReleaseMutex()
}
