$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
python "$root\sentinel_release_guard.py" demo --input "$root\demo_input\sample_change.json" --output-dir "$root\demo_output"
Write-Host ""
Write-Host "Open demo dashboard:"
Write-Host "$root\demo_output\dashboard.html"
