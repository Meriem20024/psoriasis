#!/usr/bin/env python3
"""Add gene symbols to the probe-level results and list the top genes."""
import argparse
import sys
from pathlib import Path

import pandas as pd


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Merge probe_genes.tsv into deg_results.csv and write a top-genes table.")
    p.add_argument("--results", required=True, help="deg_results.csv from analyze.py")
    p.add_argument("--annotation", required=True, help="probe_genes.tsv (probe, gene_symbol, gene_title)")
    p.add_argument("--outdir", default="results", help="output directory (default: results)")
    p.add_argument("--top", type=int, default=30, help="number of top genes to list (default: 30)")
    return p.parse_args(argv)


def merge_genes(res, annot):
    """Left-join gene symbol and title onto the results (one annotation row per probe)."""
    annot = annot.drop_duplicates(subset="probe")
    out = res.merge(annot, on="probe", how="left")
    for col in ("gene_symbol", "gene_title"):
        out[col] = out[col].fillna("").astype(str)
    return out


def top_genes(annotated, n=30):
    """Best probe per gene among significant, annotated probes, sorted by adjusted p-value."""
    sig = annotated[annotated["significant"] & (annotated["gene_symbol"] != "")].copy()
    sig["gene"] = sig["gene_symbol"].str.split(" /// ").str[0]
    best = sig.sort_values("fdr").drop_duplicates(subset="gene")
    return best.head(n)[["gene", "probe", "mean_log2fc", "fdr", "gene_title"]]


def main(argv=None):
    args = parse_args(argv)
    try:
        res = pd.read_csv(args.results)
        annot = pd.read_csv(args.annotation, sep="\t", dtype=str)
        annotated = merge_genes(res, annot)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    annotated.to_csv(outdir / "deg_annotated.csv", index=False)
    top = top_genes(annotated, args.top)
    top.to_csv(outdir / "top_genes.csv", index=False)
    print(top.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
