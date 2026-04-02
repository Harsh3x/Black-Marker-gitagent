#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
INPUT="$1"

PDF_PATH=$(python3 -c "import sys, json; raw = sys.argv[1]; data = json.loads(raw) if raw.startswith('{') else {}; print(data.get('pdf_path', raw))" "$INPUT")

cd "$AGENT_DIR"
mkdir -p output

# Run Python silently and send all output to a log file instead of the terminal
python3 run.py "$PDF_PATH" --review > redact_review.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="$AGENT_DIR/output/${STEM}_FOR_REVIEW.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

# Safely print ONLY the JSON response for GitClaw
python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"

