Data schema templates for training and inference.

You can provide any single source or any combination of sources:
- FTIR only
- HPLC only
- GC-MS only
- FTIR + HPLC
- FTIR + GC-MS
- HPLC + GC-MS
- FTIR + HPLC + GC-MS

Required metadata columns in every CSV:
- sample_id: unique row ID
- species: species name or label
- phylum: taxonomic phylum/class
- replicate: replicate index or batch number

Fingerprint columns:
- HPLC: intensity_RT_01 .. intensity_RT_50
- GC-MS: intensity_mz_001 .. intensity_mz_080
- FTIR: wn_<wavenumber> columns such as wn_1000, wn_1020, wn_1050, ...

Training target columns:
- activity_<solvent> for each solvent in the project list
- <assay>_<solvent> for each assay/solvent pair, for example DPPH_MeOH_70

Notes:
- If you want the model to train on your own data, include the activity_<solvent> columns.
- FTIR-only training is supported, but FTIR rows still need the target columns above.
- The pipeline aligns combined-source inputs by sample_id when possible.
- If sample_id values do not match across sources, the pipeline falls back to the shared row count.

Template files:
- template_hplc.csv: example HPLC layout
- template_gcms.csv: example GC-MS layout
- template_ftir.csv: example FTIR layout with target columns included

Replace the example rows with your experimental values and keep the column names unchanged.
