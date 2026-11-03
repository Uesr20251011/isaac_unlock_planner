param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$localDirectory = Join-Path $root '.local'

try {
    New-Item -ItemType Directory -Path $localDirectory -Force | Out-Null
    $configPath = Join-Path $localDirectory 'config.json'
    $config = if (Test-Path -LiteralPath $configPath) {
        Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } else { [pscustomobject]@{} }
    $port = if ($config.port) { [int]$config.port } else { 18789 }
    $address = "http://127.0.0.1:$port"

    function Test-PlannerReady {
        try {
            $health = Invoke-RestMethod -Uri "$address/api/health" -TimeoutSec 2
            return $health.app -eq 'isaac-unlock-planner'
        } catch { return $false }
    }

    if (-not (Test-PlannerReady)) {
        $nodePath = if ($config.nodePath) { $config.nodePath } else { (Get-Command node.exe -ErrorAction Stop).Source }
        $serverScript = Join-Path $PSScriptRoot 'local-server.cjs'
        $server = Start-Process -FilePath $nodePath -ArgumentList @('"' + $serverScript + '"') `
            -WorkingDirectory $root -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $localDirectory 'server.log') `
            -RedirectStandardError (Join-Path $localDirectory 'server.error.log')
        $ready = $false
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            if (Test-PlannerReady) { $ready = $true; break }
            if ($server.HasExited) { break }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw 'The planner could not start. Check .local/server.error.log or whether the configured port is in use.' }
    }
    if (-not $NoBrowser) { Start-Process "$address/#guide" }
    Write-Output $address
} catch {
    if ($NoBrowser) { throw }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Isaac Unlock Planner') | Out-Null
    exit 1
}
