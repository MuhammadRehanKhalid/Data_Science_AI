Templates for data sources.

- template_hplc.csv: HPLC fingerprint rows. Columns: sample_id, species, phylum, replicate, intensity_RT_01..intensity_RT_50, activity_<solvent>, <assay>_<solvent> for each assay.
- template_gcms.csv: GC-MS fingerprint rows. Columns: sample_id, species, phylum, replicate, intensity_mz_001..intensity_mz_80, activity_<solvent>, <assay>_<solvent>.
- template_ftir.csv: FTIR spectral rows. Columns: sample_id, species, phylum, wn_<wavenumber>_.., plus activity_<solvent> and per-assay columns if you want FTIR-only training.

Guidelines: Replace the example rows with your experimental data. Ensure species and phylum columns are filled and that activity_<solvent> columns exist if you want training to build targets.
