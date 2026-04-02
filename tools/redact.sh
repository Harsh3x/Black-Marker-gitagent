#!/bin/bash

# 1. Log everything to a file so we can see what goes wrong
exec 2> redact_error.log
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# 2. Grab the input passed by GitClaw (or you)
INPUT="$1"

# 3. Safely extract the path using Python (handles both raw paths and JSON)
PDF_PATH=$(python3 -c "
import sys, json
raw = sys.argv[1]
try:
    data = json.loads(raw)
    print(data.get('pdf_path', raw))
except json.JSONDecodeError:
    # If it's not JSON, just use the raw string
    print(raw)
" "$INPUT")

# 4. Navigate and prepare output
cd "$AGENT_DIR"
mkdir -p output

# 5. Run the actual redaction engine and capture errors!
python3 run.py "$PDF_PATH" >> redact_error.log 2>&1

# 6. Format the response for GitClaw
STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="$AGENT_DIR/output/${STEM}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"
