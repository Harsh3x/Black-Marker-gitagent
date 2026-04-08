#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$AGENT_DIR"
mkdir -p output

LOG="$AGENT_DIR/output/redact.log"

# Capture everything for debugging
RAW_INPUT=$(cat /dev/stdin 2>/dev/null || echo "")

{
    echo "========================================"
    echo "Timestamp : $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "RAW_INPUT : $RAW_INPUT"
    echo "ARGS      : $@"
    echo "--- ALL ENV VARS WITH 'pdf' or 'compliance' or 'input' ---"
    env | grep -iE "pdf|compliance|input|path" || echo "(none found)"
    echo "--- FULL ENV DUMP ---"
    env | sort >> "$LOG"
    echo "----------------------------------------"
} >> "$LOG"

# Parse pdf_path — try every possible method
PDF_PATH=""
COMPLIANCE=""

# Method 1: JSON stdin
if [ -n "$RAW_INPUT" ]; then
    PDF_PATH=$(echo "$RAW_INPUT" | python3 -c "
import sys,json
try: print(json.loads(sys.stdin.read()).get('pdf_path',''))
except: print('')
" 2>/dev/null)
    COMPLIANCE=$(echo "$RAW_INPUT" | python3 -c "
import sys,json
try: print(json.loads(sys.stdin.read()).get('compliance','') or '')
except: print('')
" 2>/dev/null)
fi

# Method 2: Env vars (exact name match from tool schema)
[ -z "$PDF_PATH" ] && PDF_PATH="${pdf_path:-}"
[ -z "$COMPLIANCE" ] && COMPLIANCE="${compliance:-}"

# Method 3: Uppercase env vars
[ -z "$PDF_PATH" ] && PDF_PATH="${PDF_PATH:-}"
[ -z "$COMPLIANCE" ] && COMPLIANCE="${COMPLIANCE:-}"

# Method 4: CLI args
[ -z "$PDF_PATH" ] && PDF_PATH="${1:-}"
[ -z "$COMPLIANCE" ] && COMPLIANCE="${2:-}"

# Method 5: INPUT env var (some frameworks wrap as JSON here)
if [ -z "$PDF_PATH" ] && [ -n "${INPUT:-}" ]; then
    PDF_PATH=$(echo "$INPUT" | python3 -c "
import sys,json
try: print(json.loads(sys.stdin.read()).get('pdf_path',''))
except: print('')
" 2>/dev/null)
    COMPLIANCE=$(echo "$INPUT" | python3 -c "
import sys,json
try: print(json.loads(sys.stdin.read()).get('compliance','') or '')
except: print('')
" 2>/dev/null)
fi

# Final fallbacks
[ -z "$COMPLIANCE" ] || [ "$COMPLIANCE" = "null" ] && COMPLIANCE="full"

{
    echo "FINAL PDF_PATH   : $PDF_PATH"
    echo "FINAL COMPLIANCE : $COMPLIANCE"
    echo "----------------------------------------"
} >> "$LOG"

if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" = "null" ]; then
    echo "[ERROR] No pdf_path received from gitclaw. Check redact.log for env dump." | tee -a "$LOG"
    echo "{\"output_path\": \"\", \"report_path\": \"\", \"exists\": false, \"error\": \"pdf_path not received\"}"
    exit 1
fi

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
