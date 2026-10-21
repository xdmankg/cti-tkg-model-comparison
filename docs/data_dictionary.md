# Data dictionary

`file_schema.csv` lists the exact columns and row counts of supplied CSV files. Numerical values and identifiers retain their source field names.

- `scenario`: report composition; S0_FULL is the complete analytical corpus, S1_DROP_TOP1 excludes the top 15 reports, and S2_DROP_TOP5 excludes the top 74 reports by combination count.
- `replicate`: randomization bundle identifier, not an independent report sample.
- `threshold`: strict (0) or unified (1e-12) positive criterion.
- `level`: randomization sample level; L0, L1, and L2 correspond to 200, 2,400, and 9,600 samples per year.
- `baseline` / `baseline_threshold`: original time input in the relevant result file; consult criterion fields and run context separately.
- `modified` / `modified_threshold`: time-rule revision input.
- `low`, `high`: interval endpoints for the specified paired comparison, not pooled intervals across bundles.
- `seed`: exact integer seed; read as an integer or string, not a floating-point number.
- `final_author_record`: final author decision, distinct from each rater's initial response.
- `included_in_analytical_corpus`: membership in the 1,474-report analytical scope; see analysis_history.md for its derivation in this release.

Report–technique links, evidence items, distinct combinations, and combination–year observations are different counting units. Time-assignment row counts depend on whether the final analytical scope has been applied.
