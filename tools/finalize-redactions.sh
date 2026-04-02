#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
INPUT="$1"


PDF_PATH=$(python3 -c "import sys, json; raw = sys.argv[1]; data = json.loads(raw) if raw.startswith('{') else {}; print(data.get('pdf_path', raw))" "$INPUT")

cd "$AGENT_DIR"
mkdir -p output

python3 finalize_redactions.py "$PDF_PATH" > finalize_error.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
# Swap out "_FOR_REVIEW" with "_FINAL_REDACTED"
CLEAN_STEM=${STEM/_FOR_REVIEW/_FINAL_REDACTED}
OUTPUT="$AGENT_DIR/output/${CLEAN_STEM}.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"
