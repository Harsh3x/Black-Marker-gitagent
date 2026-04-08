#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$AGENT_DIR"
mkdir -p output

LOG="$AGENT_DIR/output/redact.log"

# Capture raw stdin immediately and log it for debugging
RAW_INPUT=$(cat /dev/stdin)

{
    echo "========================================"
    echo "Timestamp : $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "RAW_INPUT : $RAW_INPUT"
    echo "ARGS      : $@"
    echo "ENV pdf_path: ${pdf_path:-}"
    echo "ENV compliance: ${compliance:-}"
} >> "$LOG"

# Try all possible ways gitclaw could pass the input
PDF_PATH=""
COMPLIANCE=""

# Method 1: JSON stdin
if [ -n "$RAW_INPUT" ]; then
    PDF_PATH=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read().strip())
    print(data.get('pdf_path', ''))
except Exception as e:
    print('')
" 2>/dev/null)
    COMPLIANCE=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read().strip())
    print(data.get('compliance', '') or '')
except Exception as e:
    print('')
" 2>/dev/null)
fi

# Method 2: Environment variables (some gitclaw versions pass this way)
[ -z "$PDF_PATH" ] && PDF_PATH="${pdf_path:-}"
[ -z "$COMPLIANCE" ] && COMPLIANCE="${compliance:-}"

# Method 3: CLI args
[ -z "$PDF_PATH" ] && PDF_PATH="${1:-}"

# Method 4: Fallback to first PDF in dir
[ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ] && PDF_PATH=$(ls input/*.pdf 2>/dev/null | head -n 1)
[ -z "$COMPLIANCE" ] || [ "$COMPLIANCE" = "null" ] && COMPLIANCE="full"

{
    echo "PARSED PDF_PATH   : $PDF_PATH"
    echo "PARSED COMPLIANCE : $COMPLIANCE"
    echo "----------------------------------------"
} >> "$LOG"

python3 run.py "$PDF_PATH" --compliance "$COMPLIANCE" 2>&1 | tee -a "$LOG"
EXIT_STATUS=${PIPESTATUS[0]}

STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi

OUTPUT="$AGENT_DIR/output/${STEM}${COMPLIANCE_TAG}_REDACTED.pdf"
REPORT="$AGENT_DIR/output/${STEM}_REDACTION_REPORT.txt"

{
    echo "Exit code : $EXIT_STATUS"
    echo "Output    : $OUTPUT"
    echo "========================================"
    echo ""
} >> "$LOG"

python3 -c "
import json, os
print(json.dumps({
    'output_path': '$OUTPUT',
    'report_path': '$REPORT',
    'exists': os.path.exists('$OUTPUT')
}))
"

exit $EXIT_STATUS
