#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/scripts/utils.sh"

OUT_DIR="$ROOT/results"
THRESHOLD=1

usage() {
    cat <<EOF
Usage: ./run.sh [-o output_dir] [-t log2fc_threshold] [-h]
  -o DIR   results directory (default: results/)
  -t NUM   |log2 fold change| threshold (default: 1)
  -h       show this help
EOF
}

while getopts ":o:t:h" opt; do
    case "$opt" in
        o) OUT_DIR="$OPTARG" ;;
        t) THRESHOLD="$OPTARG" ;;
        h) usage; exit 0 ;;
        :) usage; die "Option -$OPTARG requires an argument" 64 ;;
        \?) usage; die "Unknown option: -$OPTARG" 64 ;;
    esac
done

mkdir -p "$ROOT/logs" "$OUT_DIR"
LOG_FILE="$ROOT/logs/run_$(date +%Y%m%d_%H%M%S).log"
export LOG_FILE

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT
trap 'log WARN "Interrupted"; exit 130' INT TERM

main() {
    log INFO "Pipeline started (threshold=$THRESHOLD, output=$OUT_DIR)"
    "$ROOT/scripts/fetch.sh" "$ROOT/data/raw"
    # next: clean.sh, analyze.py, archive
    log INFO "Pipeline finished"
}

main
