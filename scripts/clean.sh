#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

RAW_DIR="${1:?usage: clean.sh RAW_DIR PROC_DIR}"
PROC_DIR="${2:?usage: clean.sh RAW_DIR PROC_DIR}"
MATRIX="$RAW_DIR/GSE34248_series_matrix.txt.gz"
EXPECTED_SAMPLES=28

# Sample table: one line per sample (id, title, patient, group)
extract_samples() {
    zcat "$MATRIX" \
        | grep -E '^!Sample_(geo_accession|title)' \
        | tr -d '"' \
        | awk -F'\t' '
            $1=="!Sample_geo_accession" { for (i=2; i<=NF; i++) id[i]=$i; n=NF }
            $1=="!Sample_title"         { for (i=2; i<=NF; i++) title[i]=$i }
            END {
                print "sample_id\ttitle\tpatient\tgroup"
                for (i=2; i<=n; i++) {
                    m = split(title[i], p, "-")
                    grp = (p[m]=="LS") ? "lesional" : (p[m]=="NL") ? "non_lesional" : "unknown"
                    print id[i] "\t" title[i] "\t" p[m-1] "\t" grp
                }
            }' > "$PROC_DIR/samples.tsv"
}

# Expression table: keep only the data block, drop the "!" lines and quotes
extract_expression() {
    zcat "$MATRIX" \
        | sed -n '/^!series_matrix_table_begin/,/^!series_matrix_table_end/p' \
        | grep -v '^!' \
        | tr -d '"' \
        > "$PROC_DIR/expression.tsv"
}

check_file "$MATRIX"
mkdir -p "$PROC_DIR"

log INFO "Extracting sample table"
extract_samples
log INFO "Extracting expression matrix"
extract_expression

# Sanity checks
n=$(( $(wc -l < "$PROC_DIR/samples.tsv") - 1 ))
[[ "$n" -eq "$EXPECTED_SAMPLES" ]] || die "Expected $EXPECTED_SAMPLES samples, found $n" 6

unknown=$(awk -F'\t' 'NR>1 && $4=="unknown"' "$PROC_DIR/samples.tsv" | wc -l)
[[ "$unknown" -eq 0 ]] || die "Some samples are neither LS nor NL" 7

bad=$(tail -n +2 "$PROC_DIR/samples.tsv" | cut -f3 | sort | uniq -c | awk '$1 != 2' | wc -l)
[[ "$bad" -eq 0 ]] || die "Some patients do not have exactly 2 samples" 7

cols=$(head -n 1 "$PROC_DIR/expression.tsv" | awk -F'\t' '{print NF}')
[[ "$cols" -eq $(( n + 1 )) ]] || die "Expression matrix has $cols columns, expected $(( n + 1 ))" 8

rows=$(( $(wc -l < "$PROC_DIR/expression.tsv") - 1 ))
log INFO "Cleaning done: $n samples, $rows probes"
