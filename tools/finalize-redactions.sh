
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Unbreakable Python parser
PDF_PATH=$(python3 -c "
import sys, json, os, select
raw = ''
if select.select([sys.stdin], [], [], 0.2)[0]: raw = sys.stdin.read().strip()
if not raw and len(sys.argv) > 1: raw = sys.argv[1].strip()

path = ''
if raw:
    try: path = json.loads(raw).get('pdf_path', '')
    except: path = raw

if not path: path = os.environ.get('pdf_path', '')
print(path.strip())
" "$1")

cd "$AGENT_DIR"

# 2. Fallback: If GitClaw passes a bad/empty path, grab the actual review file
if [ ! -f "$PDF_PATH" ]; then
    PDF_PATH=$(ls output/*_FOR_REVIEW.pdf 2>/dev/null | head -n 1)
fi

# 3. SAFETY CHECK: If it STILL doesn't exist, abort gracefully!
if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    echo "{\"output_path\": \"\", \"report_path\": \"\", \"exists\": false, \"error\": \"No _FOR_REVIEW.pdf file found. You must run redact-review first.\"}"
    exit 0
fi

mkdir -p output
python3 finalize_redactions.py "$PDF_PATH" > finalize_error.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
CLEAN_STEM=${STEM/_FOR_REVIEW/_FINAL_REDACTED}
OUTPUT="$AGENT_DIR/output/${CLEAN_STEM}.pdf"
REPORT="$AGENT_DIR/output/redaction_report.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"
EOF
chmod +x tools/finalize-redactions.sh
