#!/usr/bin/env python3
"""Paired differential expression: lesional vs non-lesional psoriatic skin (GSE34248)."""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no screen needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Find probes that differ between lesional (LS) and non-lesional (NL) skin, "
                    "using a paired test per patient.")
    p.add_argument("--expression", required=True, help="expression.tsv (probes x samples)")
    p.add_argument("--samples", required=True, help="samples.tsv (sample_id, title, patient, group)")
    p.add_argument("--outdir", default="results", help="output directory (default: results)")
    p.add_argument("--lfc", type=float, default=1.0, help="min |log2 fold change| (default: 1)")
    p.add_argument("--fdr", type=float, default=0.05, help="max adjusted p-value (default: 0.05)")
    p.add_argument("--floor", type=float, default=1.0,
                   help="values below this are raised to it before log2, "
                        "because some intensities are negative (default: 1)")
    return p.parse_args(argv)


def log2_transform(values, floor=1.0):
    """log2 of intensities; values below `floor` (including negatives) are set to `floor`."""
    return np.log2(np.clip(values, floor, None))


def benjamini_hochberg(pvalues):
    """Benjamini-Hochberg adjusted p-values (FDR), same order as the input."""
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(ranked, 0, 1)
    return out


def paired_ids(samples):
    """Sample IDs of lesional and non-lesional skin, in the same patient order."""
    ls = samples[samples["group"] == "lesional"].set_index("patient")["sample_id"]
    nl = samples[samples["group"] == "non_lesional"].set_index("patient")["sample_id"]
    patients = sorted(set(ls.index) & set(nl.index))
    if len(patients) != len(ls) or len(patients) != len(nl):
        raise ValueError("Samples are not perfectly paired by patient")
    return ls.loc[patients].tolist(), nl.loc[patients].tolist()


def run_analysis(expr, samples, floor=1.0, lfc_thr=1.0, fdr_thr=0.05):
    """Paired t-test per probe on log2 values; returns one row per probe."""
    ls_ids, nl_ids = paired_ids(samples)
    ls = log2_transform(expr[ls_ids].to_numpy(dtype=float), floor)
    nl = log2_transform(expr[nl_ids].to_numpy(dtype=float), floor)
    t_stat, p = stats.ttest_rel(ls, nl, axis=1)
    p = np.nan_to_num(p, nan=1.0)            # constant probes give NaN: treat as not significant
    t_stat = np.nan_to_num(t_stat, nan=0.0)
    res = pd.DataFrame({
        "probe": expr.index,
        "mean_log2fc": (ls - nl).mean(axis=1),
        "t_stat": t_stat,
        "p_value": p,
    })
    res["fdr"] = benjamini_hochberg(res["p_value"])
    res["significant"] = (res["fdr"] < fdr_thr) & (res["mean_log2fc"].abs() >= lfc_thr)
    return res.sort_values("fdr").reset_index(drop=True)


def volcano_plot(res, lfc_thr, fdr_thr, path):
    y = -np.log10(res["fdr"].clip(lower=1e-300))
    up = res["significant"] & (res["mean_log2fc"] > 0)
    down = res["significant"] & (res["mean_log2fc"] < 0)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(res["mean_log2fc"], y, s=4, c="lightgray", label="not significant")
    ax.scatter(res.loc[up, "mean_log2fc"], y[up], s=6, c="firebrick", label="higher in lesional")
    ax.scatter(res.loc[down, "mean_log2fc"], y[down], s=6, c="steelblue", label="lower in lesional")
    ax.axhline(-np.log10(fdr_thr), ls="--", lw=0.8, c="black")
    ax.axvline(lfc_thr, ls="--", lw=0.8, c="black")
    ax.axvline(-lfc_thr, ls="--", lw=0.8, c="black")
    ax.set_xlabel("mean log2 fold change (lesional - non-lesional)")
    ax.set_ylabel("-log10 adjusted p-value")
    ax.set_title("Psoriasis GSE34248: lesional vs non-lesional skin")
    ax.legend(markerscale=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    args = parse_args(argv)
    try:
        expr = pd.read_csv(args.expression, sep="\t", index_col=0)
        samples = pd.read_csv(args.samples, sep="\t", dtype={"patient": str})
        res = run_analysis(expr, samples, args.floor, args.lfc, args.fdr)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    res.to_csv(outdir / "deg_results.csv", index=False)

    sig = res[res["significant"]]
    summary = {
        "n_probes": int(len(res)),
        "n_pairs": int(samples["patient"].nunique()),
        "thresholds": {"abs_log2fc": args.lfc, "fdr": args.fdr, "floor": args.floor},
        "n_significant": int(len(sig)),
        "n_higher_in_lesional": int((sig["mean_log2fc"] > 0).sum()),
        "n_lower_in_lesional": int((sig["mean_log2fc"] < 0).sum()),
        "top_probe": str(res.loc[0, "probe"]),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    volcano_plot(res, args.lfc, args.fdr, outdir / "volcano.png")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
