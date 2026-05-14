=== HPLC DATA FORMAT ===


Sample HPLC CSV format:
retention_time,peak_area,sample_id,compound_name,wavelength,species
2.34,5632.1,S001,Chlorogenic_acid,254,Chlorella_vulgaris
3.45,8921.3,S001,Rutin,254,Chlorella_vulgaris
5.67,1234.2,S001,Quercetin,280,Chlorella_vulgaris
...

OR Excel with sheets: "metadata" and "hplc_peaks"
        

Required columns: retention_time, peak_area, sample_id
Optional columns: compound_name, wavelength, species, phylum, solvent, replicate
