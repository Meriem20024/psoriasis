import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze


def test_log2_transform_floors_negative_values():
    out = analyze.log2_transform(np.array([-5.0, 1.0, 8.0]), floor=1.0)
    assert np.allclose(out, [0.0, 0.0, 3.0])


def test_benjamini_hochberg():
    fdr = analyze.benjamini_hochberg([0.01, 0.04, 0.03, 0.5])
    assert np.allclose(fdr, [0.04, 0.05333, 0.05333, 0.5], atol=1e-3)


def test_run_analysis_finds_the_up_probe():
    samples = pd.DataFrame({
        "sample_id": ["L1", "L2", "L3", "L4", "N1", "N2", "N3", "N4"],
        "patient": ["p1", "p2", "p3", "p4"] * 2,
        "group": ["lesional"] * 4 + ["non_lesional"] * 4,
    })
    expr = pd.DataFrame(
        {
            "L1": [80, 10], "L2": [100, 12], "L3": [90, 11], "L4": [110, 13],
            "N1": [10, 11], "N2": [12, 11], "N3": [11, 12], "N4": [13, 12],
        },
        index=["up", "flat"],
    )
    res = analyze.run_analysis(expr, samples).set_index("probe")
    assert abs(res.loc["up", "mean_log2fc"] - 3) < 0.2
    assert abs(res.loc["flat", "mean_log2fc"]) < 0.5


def test_filter_expressed_removes_low_probes():
    expr = pd.DataFrame(
        {"a": [100, 2], "b": [120, -5], "c": [90, 3], "d": [110, 1]},
        index=["expressed", "noise"],
    )
    kept = analyze.filter_expressed(expr, min_expr=50, min_samples=3)
    assert list(kept.index) == ["expressed"]


def test_merge_genes_and_top_genes():
    import add_genes
    res = pd.DataFrame({
        "probe": ["p1", "p2", "p3"],
        "mean_log2fc": [2.0, -1.5, 3.0],
        "fdr": [0.001, 0.01, 0.0001],
        "significant": [True, True, True],
    })
    annot = pd.DataFrame({
        "probe": ["p1", "p2", "p3"],
        "gene_symbol": ["GENEA", "GENEB /// GENEC", ""],
        "gene_title": ["a", "b", ""],
    })
    merged = add_genes.merge_genes(res, annot)
    assert merged.loc[merged["probe"] == "p3", "gene_symbol"].iloc[0] == ""
    top = add_genes.top_genes(merged)
    assert list(top["gene"]) == ["GENEA", "GENEB"]   # p3 has no gene, p1 beats p2 on FDR
