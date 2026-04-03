
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

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
if [ -z "$PDF_PATH" ] || [ "$PDF_PATH" == "null" ]; then
    PDF_PATH=$(ls *.pdf | head -n 1)
fi

mkdir -p output
python3 run.py "$PDF_PATH" --review > redact_review.log 2>&1

STEM=$(basename "$PDF_PATH" .pdf)
OUTPUT="./output/${STEM}_FOR_REVIEW.pdf"
REPORT="./output/${STEM}_REDACTION_REPORT.txt"

python3 -c "import json, os; print(json.dumps({'output_path': '${OUTPUT}', 'report_path': '${REPORT}', 'exists': os.path.exists('${OUTPUT}')}))"
EOF
chmod +x tools/redact-review.sh
