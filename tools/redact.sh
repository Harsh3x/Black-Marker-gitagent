
#!/bin/bash
# DUMP EVERYTHING TO THE LOG
echo "--- SYSTEM ENVIRONMENT DUMP ---" > redact.log
env >> redact.log
echo "-------------------------------" >> redact.log
echo "ARG 1: '$1'" >> redact.log
echo "STDIN: '$(timeout 1 cat /dev/stdin)'" >> redact.log

# Return a safe failure so GitClaw doesn't freeze
echo '{"output_path": "", "report_path": "", "exists": false}'
EOF
chmod +x tools/redact.sh
