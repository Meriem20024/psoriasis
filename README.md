# Psoriasis Pipeline (Group [XX])

Which genes are expressed differently in lesional vs non-lesional skin of the same
psoriasis patient? Dataset: GEO GSE34248 (14 patients, 28 biopsies, Affymetrix GPL570).
Pattern: probes with adjusted p-value (FDR) < 0.05 and |log2 fold change| above a threshold
(paired test, Benjamini-Hochberg correction).

## Requirements

Tested on Ubuntu 24.04 (WSL2), Python 3.12.3. Internet access is needed on the first run
(about 160 MB download).

```bash
sudo apt update && sudo apt install -y git curl cron python3 python3-venv python3-pip
```

## Installation

```bash
git clone [REPOSITORY URL] projet_maladie
cd projet_maladie
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
chmod +x run.sh scripts/*.sh scripts/*.py
```

## Usage

```bash
./run.sh            # full pipeline with default settings
./run.sh -t 1.5     # stricter fold-change threshold
./run.sh -o out     # write results to out/ instead of results/
./run.sh -h         # help
```

Options: `-o DIR` results directory (default `results/`), `-t NUM` minimum
|log2 fold change| (default 1), `-h` help. Other analysis settings (`--floor`,
`--min-expr`, `--min-samples`, `--fdr`) are listed by
`.venv/bin/python scripts/analyze.py -h`.

The pipeline can be re-run at any time without manual cleanup. Raw data are downloaded
once and verified with SHA-256 checksums on every later run.

## What the pipeline does

1. `scripts/fetch.sh`: downloads the series matrix, the raw CEL archive and the
   GPL570 annotation, tests the files, creates or verifies `data/checksums.sha256`,
   makes the raw files read-only.
2. `scripts/clean.sh`: builds `samples.tsv` and `expression.tsv` with shell tools and
   checks them (28 samples, 2 per patient, correct columns).
3. `scripts/annotate.sh`: builds `probe_genes.tsv` (probe, gene symbol, gene title).
4. `scripts/analyze.py`: filters unexpressed probes, log2 transform, paired test per
   probe, FDR correction, volcano plot.
5. `scripts/add_genes.py`: adds gene names and lists the top genes.
6. `run.sh` packs the results into a dated archive.

## Directory tree

```
run.sh                 single entry point
scripts/               utils.sh fetch.sh clean.sh annotate.sh analyze.py add_genes.py install_cron.sh
tests/                 test_analyze.py
data/raw/              downloaded files (read-only, not in Git)
data/processed/        cleaned tables (not in Git)
results/               outputs (not in Git)
logs/                  timestamped logs (not in Git)
requirements.txt       pinned Python packages
SOURCES.md             dataset identifiers, URLs, hashes, download date
```

## Files produced

| File | Content |
|---|---|
| `results/deg_results.csv` | one row per probe: log2 fold change, t statistic, p-value, FDR, significant |
| `results/deg_annotated.csv` | same, with gene symbol and title |
| `results/top_genes.csv` | best probe for each significant gene |
| `results/summary.json` | counts and thresholds used |
| `results/volcano.png` | volcano plot |
| `results/archive_YYYYmmdd_HHMMSS.tar.gz` | dated archive of the files above |
| `logs/run_YYYYmmdd_HHMMSS.log` | timestamped log of each run |
| `data/processed/*.tsv` | cleaned tables used by the analysis |

## Exit codes

0 success, 2 missing file or Python error, 3 download failed, 4 corrupted file,
5 checksum mismatch, 6 wrong number of samples, 7 samples not paired or unlabeled,
8 wrong number of columns, 9 Python environment missing, 10 corrupted archive,
11 annotation could not be parsed, 12 annotation does not match the data,
64 invalid option, 130 interrupted.

## Tests

```bash
.venv/bin/python -m pytest tests -v
```

## Scheduled run (cron)

```bash
scripts/install_cron.sh      # weekly run, Sundays 03:00, output in logs/cron.log
crontab -l                   # check
crontab -l | grep -v projet_maladie_pipeline | crontab -    # remove
```

On WSL, cron only runs while WSL is running, and the service must be started with
`sudo service cron start` (or enable systemd in `/etc/wsl.conf`).

## Work split

Member	                    Assigned Part
Djebara Meriem	          analyze.py + test_analyze.py
Benmerabet Mohamed Ali	fetch.sh + clean.sh
Dahmani Lamis	          add_genes.py + annotate.sh
Bouhamam Kenza	            utils.sh + installcron.sh
Bouras Said		          run.sh + integration testing

## Known limits

Some intensities in the source data are negative; they are raised to a floor before the
log transform, and weakly expressed probes are filtered out. Results depend somewhat on
these two choices (see report). Only 14 patients, one platform, no independent validation.

## Troubleshooting

If the download fails (`Download failed`, exit code 3), check your internet connection and run
`./run.sh` again: files that were already downloaded and verified are not downloaded twice.
