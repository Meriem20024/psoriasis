#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

RAW_DIR="${1:?usage: annotate.sh RAW_DIR PROC_DIR}"
PROC_DIR="${2:?usage: annotate.sh RAW_DIR PROC_DIR}"
TMP_DIR="${TMP_DIR:?TMP_DIR not set: run through run.sh}"
ANNOT="$RAW_DIR/GPL570.annot.gz"

check_file "$ANNOT"
check_file "$PROC_DIR/expression.tsv"

log INFO "Extracting probe-to-gene table"
zcat "$ANNOT" \
    | sed -n '/^!platform_table_begin/,/^!platform_table_end/p' \
    | grep -v '^!' \
    | awk -F'\t' '
        NR==1 {
            for (i=1; i<=NF; i++) {
                if ($i=="ID") c_id=i
                if ($i=="Gene symbol") c_sym=i
                if ($i=="Gene title") c_title=i
            }
            if (!c_id || !c_sym || !c_title) exit 3
            print "probe\tgene_symbol\tgene_title"
            next
        }
        {
            sym = ($c_sym=="---") ? "" : $c_sym
            ttl = ($c_title=="---") ? "" : $c_title
            print $c_id "\t" sym "\t" ttl
        }' > "$TMP_DIR/probe_genes.tsv" \
    || die "Could not parse the annotation file (column names not found)" 11

annot_rows=$(( $(wc -l < "$TMP_DIR/probe_genes.tsv") - 1 ))
expr_rows=$(( $(wc -l < "$PROC_DIR/expression.tsv") - 1 ))
[[ "$annot_rows" -ge "$expr_rows" ]] || die "Annotation has $annot_rows probes, expression has $expr_rows" 12

mv "$TMP_DIR/probe_genes.tsv" "$PROC_DIR/probe_genes.tsv"
log INFO "Annotation done: $annot_rows probes"
