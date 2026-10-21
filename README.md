# CTI TKG Model Comparison

Version 1.0 data package for **Model Comparison and Sensitivity Analysis of Changes in Attack Technique Relations in Temporal Knowledge Graphs Built from CTI Reports**.

This repository provides derived inputs, preserved numerical results, manuscript figures, and focused verification scripts. It supports inspection of reported values and selected recalculations. Verification covers the checks explicitly implemented in the supplied scripts, rather than every statement in the article.

## Contents

| Directory | Contents |
| --- | --- |
| `data/` | Report metadata and analytical membership, technique evidence and links, adopted time expressions, report–year weights, relation universe, and report exclusion lists |
| `configs/` | Preserved initial and follow-up settings and seeds |
| `results/main/` | Main model comparisons, conditional tests, LOTO, B2 selection, contrast tests, and cross-condition comparisons |
| `results/initial/` | Preserved initial-run results |
| `results/followup/` | Strict-criterion follow-up numerical arrays |
| `results/corrections/` | Corrected summaries of the historical follow-up runs |
| `results/audit/` | Pseudonymous initial and final judgments, stratum counts, and interval estimates |
| `results/time_revision/` | Time-rule revision results and the six-expression weight sensitivity calculation |
| `figures/` | Eleven manuscript images; no figure-generation code |
| `scripts/` | Numerical verification and paired LOTO interval recalculation |
| `docs/` | File schemas, artifact index, run registry, and verification outputs |

Use `docs/paper_artifacts.csv` to locate supplied files and `docs/file_schema.csv` to inspect their columns. The index lists the material supplied in this package. It is not a claim that every historical working file named in the Supplementary Materials is distributed. Identical-byte path changes are listed in `docs/path_changes.csv`.

## Verification

Use Python 3.10 or later. Install the numerical dependencies, then run:

```bash
python -m pip install -r requirements-verification.txt
python scripts/verify.py
python scripts/verify_recovered.py
python scripts/recalculate_loto.py
sha256sum -c checksums.sha256
```

`verify.py` checks reported values and arithmetic identities, including all 180 candidate-set rows across 36 conditions, audit summaries, input counts, and selected table values. Any unavailable input required by an implemented check produces a nonzero exit status. `verify_recovered.py` checks derived inputs, reconstructs observed ratios from released links and weights, and checks preserved arrays. `recalculate_loto.py` first reproduces the 30 supplied R1−R0 and R1−R2 intervals, then calculates 15 R0−R2 intervals. These calculations use moving blocks of length 3, 10,000 samples, and the saved seeds. The R0−R2 outputs are recalculations from released losses, not recovered original output files.

Verification reports are written under `docs/`. Generated reports and the recalculated LOTO outputs are excluded from the static checksum list so that rerunning the scripts does not invalidate it. Their source inputs are checksummed.

## Interpretation and scope

- The main comparison uses the original input, unified positive criterion, B0, and L2. Historical strict-criterion runs and time-revised inputs have distinct roles; use the condition columns and run registry when selecting rows.
- Audit judgments support agreement calculations. The supplied stratum counts support weighted rates and uncertainty summaries. Sample selection, source-context reassessment, and the linkage of individual judgments to strata are outside this release's verification scope.
- The 14,076-expression residual-six input was evaluated through report–year weights and observed ratios W. No downstream randomization, excess-ratio, or model results for that input are asserted here.
- Original and revised time lists include pre-final-scope entries. Use the supplied final-scope views for the manuscript counts of 14,082 and 14,076. See `docs/analysis_history.md`.
- Historical per-run files, source-text manifests, illustrative-source files, and analysis kernels not listed in the artifact index are outside this distribution. The preserved summaries and supplied recalculations have the narrower coverage stated in the index.
- This release does not reproduce report collection, text reconstruction, evidence extraction, the full analysis pipeline, or figure rendering.

## Privacy and rights

Original CTI reports, full source sentences, reviewer correspondence, and development conversations are excluded. Public source identifiers and ATT&CK identifiers are retained for traceability. Audit raters are represented by role identifiers.

The license files supplied with the source package are retained: MIT for author-written code and CC BY 4.0 for author-created data, numerical results, figures, and documentation, subject to the third-party exclusions in `LICENSE-DATA`.

## Citation

See `CITATION.cff`. When citing a published copy, include its actual GitHub release URL and version. Repository: https://github.com/xdmankg/cti-tkg-model-comparison. Version 1.0 is the package version; use an existing release tag or commit when identifying the exact copy used.
