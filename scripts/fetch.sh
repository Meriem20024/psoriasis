#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

RAW_DIR="${1:?usage: fetch.sh RAW_DIR}"
SUMS="$RAW_DIR/../checksums.sha256"
BASE="https://ftp.ncbi.nlm.nih.gov/geo"
FILES=("series/GSE34nnn/GSE34248/matrix/GSE34248_series_matrix.txt.gz" "series/GSE34nnn/GSE34248/suppl/GSE34248_RAW.tar" "platforms/GPLnnn/GPL570/annot/GPL570.annot.gz")

mkdir -p "$RAW_DIR"

for f in "${FILES[@]}"; do
    name="$(basename "$f")"
    if [[ -f "$RAW_DIR/$name" ]]; then
        log INFO "Already downloaded: $name"
        continue
    fi
    log INFO "Downloading $name"
    wget -4 -q --show-progress --timeout=30 --tries=3 -O "$RAW_DIR/$name.part" "$BASE/$f" \
        || { rm -f "$RAW_DIR/$name.part"; die "Download failed: $name" 3; }
    mv "$RAW_DIR/$name.part" "$RAW_DIR/$name"
done

# Integrity: test the archives, then create or verify SHA-256 checksums
gzip -t "$RAW_DIR/GSE34248_series_matrix.txt.gz" || die "Corrupted file: series matrix" 4
gzip -t "$RAW_DIR/GPL570.annot.gz" || die "Corrupted file: annotation" 4
tar -tf "$RAW_DIR/GSE34248_RAW.tar" > /dev/null || die "Corrupted file: RAW.tar" 4

if [[ -f "$SUMS" ]]; then
    log INFO "Verifying checksums"
    (cd "$RAW_DIR" && sha256sum -c ../checksums.sha256) || die "Checksum mismatch" 5
else
    log INFO "Creating checksums"
    (cd "$RAW_DIR" && sha256sum -- * > ../checksums.sha256)
fi

chmod a-w "$RAW_DIR"/*
log INFO "Data ready in $RAW_DIR"
