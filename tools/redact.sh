
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Unbreakable Python parser (Never hangs, catches all GitClaw inputs)
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

COMPLIANCE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('compliance','full'))")


cd "$AGENT_DIR"

# 2. The Resilience Fallback: If GitClaw drops the payload, just find the PDF!
if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" == "null" ]; then
    PDF_PATH=$(ls *.pdf | head -n 1)
fi

mkdir -p output
python3 run.py "$PDF_PATH" --compliance "$COMPLIANCE" > redact.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
if [ "$COMPLIANCE" != "full" ]; then
    COMPLIANCE_TAG="_$(echo $COMPLIANCE | tr '[:lower:]' '[:upper:]')"
else
    COMPLIANCE_TAG=""
fi


OUTPUT="./output/${STEM}${COMPLIANCE_TAG}_REDACTED.pdf"
REPORT="./output/${STEM}${COMPLIANCE_TAG}_REDACTION_REPORT.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"

chmod +x tools/redact.sh


