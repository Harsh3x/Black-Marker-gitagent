#!/bin/bash

# 1. Log everything to a file so we can see what goes wrong
exec 2> redact_error.log
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# MAGIC FIX: Use $1 for manual testing, or stdin for GitClaw
if [ -n "$1" ]; then
    INPUT="$1"
else
    INPUT=$(cat /dev/stdin)
fi

PDF_PATH=$(python3 -c "import sys, json; raw = sys.argv[1]; data = json.loads(raw) if raw.startswith('{') else {}; print(data.get('pdf_path', raw))" "$INPUT")

cd "$AGENT_DIR"
mkdir -p output

python3 run.py "$PDF_PATH" > redact.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="$AGENT_DIR/output/${STEM}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"
EOF

chmod +x tools/redact.sh
