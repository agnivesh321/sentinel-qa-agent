$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
python "$Root\sentinel_qa_agent.py" demo --input "$Root\demo_input\sample_change.json" --output-dir "$Root\demo_output"
