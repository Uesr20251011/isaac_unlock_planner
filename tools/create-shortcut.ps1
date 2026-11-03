param([string]$Name = 'Isaac Unlock Planner')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$localDirectory = Join-Path $root '.local'
New-Item -ItemType Directory -Path $localDirectory -Force | Out-Null

Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::new((Join-Path $root 'assets/icon.png'))
$icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
$iconPath = Join-Path $localDirectory 'planner.ico'
$stream = [System.IO.File]::Create($iconPath)
try { $icon.Save($stream) } finally { $stream.Dispose(); $icon.Dispose(); $bitmap.Dispose() }

$shell = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) "$Name.lnk"
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $PSScriptRoot 'start-planner.ps1') + '"'
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = 'Open the local Isaac unlock planner and synchronize the bound save.'
$shortcut.WindowStyle = 7
$shortcut.Save()
Write-Output $shortcutPath
