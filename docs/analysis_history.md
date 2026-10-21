# Analysis conditions and data scope

Initial results, strict-criterion follow-up results, corrected summaries, the main comparison, and time-input revisions are stored separately. These groups reflect different analysis settings; matching filenames or model labels alone do not establish equivalence.

The main comparison uses original input, the unified positive criterion, B0, and L2. Cross-condition files retain input, criterion, level, composition, and replicate fields.

The analytical report membership in `data/canonical_documents.csv` is reconstructed from the preserved final-report ranking and checked against the report identifiers in the original weight table. It contains 1,474 reports. This derived membership field should be distinguished from untouched source metadata.

Time-revision files retain their pre-final-scope rows: the v3.1 list contains 14,098 entries and the residual-six list 14,092. Restriction to the 1,474-report scope gives 14,082 and 14,076. Explicit final-scope files are supplied. Historical run arrays must not be substituted for main-comparison arrays.

R0−R2 LOTO intervals were recalculated during release assembly. The calculation first reproduced all 30 saved reference intervals, then reused each corresponding R1−R2 seed for R0−R2. See `results/main/LOTO_verification.json` for the input hashes and numerical agreement.

Audit initial responses and final author decisions remain distinct. Stratum summaries are provided as preserved aggregates; this release does not reconstruct the sample-to-source and sample-to-stratum crosswalk.
