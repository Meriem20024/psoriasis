#!/usr/bin/env bash
# Shared helper functions, sourced by run.sh and the other scripts.

log() {                      # log LEVEL message...
    local level="$1"; shift
    printf '%s [%s] %s\n' "$(date '+%F %T')" "$level" "$*" | tee -a "${LOG_FILE:-/dev/null}" >&2
}

die() {                      # die "message" [exit_code]
    local code="${2:-1}"
    log ERROR "$1"
    exit "$code"
}

check_file() {               # check_file path
    [[ -f "$1" ]] || die "Missing file: $1" 2
}

