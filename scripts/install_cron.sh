#!/usr/bin/env bash

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINE="0 3 * * 0 cd $ROOT && ./run.sh >> $ROOT/logs/cron.log 2>&1 # projet_maladie_pipeline"

mkdir -p "$ROOT/logs"
( crontab -l 2>/dev/null | grep -v "projet_maladie_pipeline" || true; echo "$LINE" ) | crontab -
echo "Cron job installed:"
echo "$LINE"
