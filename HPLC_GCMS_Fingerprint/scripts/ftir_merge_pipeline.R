#!/usr/bin/env Rscript
# FTIR merge & preprocessing pipeline script
# Usage example:
# Rscript ftir_merge_pipeline.R --input_dir "path/to/dir" --output_dir "out" --bin_width 5 --norm minsub --do_pca

suppressPackageStartupMessages({
  library(optparse)
  library(tidyverse)
})

option_list <- list(
  make_option(c("-i", "--input_dir"), type = "character", default = NULL,
              help = "Directory containing CSV files", metavar = "character"),
  make_option(c("-o", "--output_dir"), type = "character", default = NULL,
              help = "Directory to save outputs (will be created)", metavar = "character"),
  make_option(c("-s", "--skip_lines"), type = "integer", default = 1,
              help = "Number of header lines to skip when reading CSVs", metavar = "integer"),
  make_option(c("-b", "--bin_width"), type = "double", default = 5,
              help = "Bin width (cm^-1) for wavelength binning", metavar = "double"),
  make_option(c("-n", "--norm"), type = "character", default = "minsub",
              help = "Normalization method: minsub|minmax|zscore|none", metavar = "character"),
  make_option(c("--do_pca"), action = "store_true", default = FALSE,
              help = "Run PCA on binned data"),
  make_option(c("--pattern"), type = "character", default = "\\.csv$",
              help = "Filename pattern for input files (regex)")
)

opt <- parse_args(OptionParser(option_list = option_list))

if (is.null(opt$input_dir)) stop("--input_dir is required")
if (is.null(opt$output_dir)) opt$output_dir <- file.path(opt$input_dir, "processed")
if (!dir.exists(opt$output_dir)) dir.create(opt$output_dir, recursive = TRUE)

files <- list.files(opt$input_dir, pattern = opt$pattern, full.names = TRUE)
if (length(files) == 0) stop("No files found in input_dir with the given pattern")

read_spectrum <- function(path, skip = 1) {
  df <- read.csv(path, skip = skip, stringsAsFactors = FALSE)
  # try to find first two numeric columns as wavenumber and intensity
  nums <- sapply(df, is.numeric)
  if (sum(nums) >= 2) {
    numcols <- which(nums)
    df2 <- df[, numcols[1:2]]
    names(df2) <- c("cm.1", "A")
    return(df2)
  }
  stop(paste("Could not find numeric columns in", path))
}

# combine
df_list <- lapply(files, function(f) {
  d <- read_spectrum(f, skip = opt$skip_lines)
  d$source_file <- basename(f)
  d
})

df_all_raw <- bind_rows(df_list)
df_all_raw <- df_all_raw %>% relocate(source_file)

write_csv(df_all_raw, file.path(opt$output_dir, "ftir_all_raw.csv"))

# wide raw
df_wide_raw <- df_all_raw %>%
  select(cm.1, A, source_file) %>%
  tidyr::pivot_wider(names_from = source_file, values_from = A)
write_csv(df_wide_raw, file.path(opt$output_dir, "ftir_wide_raw.csv"))

# Plot original spectra (overlay and facet)
library(ggplot2)
plot_overlay <- ggplot(df_all_raw, aes(x = cm.1, y = A, color = source_file)) +
  geom_line(size = 0.7) +
  scale_x_reverse() + theme_classic() +
  labs(x = expression("Wavenumber (cm"^-1*")"), y = "Absorbance", color = "Sample")
ggsave(filename = file.path(opt$output_dir, "spectra_overlay_raw.png"), plot = plot_overlay, width = 8, height = 6)

plot_facet <- ggplot(df_all_raw, aes(x = cm.1, y = A)) +
  geom_line(color = "steelblue") + scale_x_reverse() +
  facet_wrap(~source_file, ncol = 1, scales = "free_y") + theme_classic() +
  labs(x = expression("Wavenumber (cm"^-1*")"), y = "Absorbance")
ggsave(filename = file.path(opt$output_dir, "spectra_facet_raw.png"), plot = plot_facet, width = 6, height = 3 + length(unique(df_all_raw$source_file)) * 0.2)

# Preprocessing: subtract min per sample and clamp negatives to zero (user requested)
df_processed <- df_all_raw %>% group_by(source_file) %>%
  mutate(A_minsub = A - min(A),
         A_minsub = ifelse(A_minsub < 0, 0, A_minsub)) %>% ungroup()

# Additional normalization options
if (opt$norm == "minmax") {
  df_processed <- df_processed %>% group_by(source_file) %>%
    mutate(A_norm = (A - min(A)) / (max(A) - min(A))) %>% ungroup()
} else if (opt$norm == "zscore") {
  df_processed <- df_processed %>% group_by(source_file) %>%
    mutate(A_norm = (A - mean(A)) / sd(A)) %>% ungroup()
} else if (opt$norm == "minsub") {
  df_processed <- df_processed %>% mutate(A_norm = A_minsub)
} else if (opt$norm == "none") {
  df_processed <- df_processed %>% mutate(A_norm = A)
} else {
  stop("Unknown normalization method: use minsub|minmax|zscore|none")
}

write_csv(df_processed, file.path(opt$output_dir, "ftir_all_processed.csv"))

# Binning
bin_width <- as.numeric(opt$bin_width)
cm_min <- floor(min(df_processed$cm.1, na.rm = TRUE))
cm_max <- ceiling(max(df_processed$cm.1, na.rm = TRUE))
breaks <- seq(cm_min, cm_max, by = bin_width)
# ensure coverage
if (tail(breaks, 1) < cm_max) breaks <- c(breaks, cm_max)

df_binned <- df_processed %>%
  mutate(bin = cut(cm.1, breaks = breaks, include.lowest = TRUE, right = FALSE)) %>%
  group_by(source_file, bin) %>%
  summarize(bin_cm = mean(cm.1, na.rm = TRUE), bin_A = mean(A_norm, na.rm = TRUE), .groups = "drop")

write_csv(df_binned, file.path(opt$output_dir, sprintf("ftir_binned_%gcm-1.csv", bin_width)))

# Histograms of binned intensities per sample
hist_plots_dir <- file.path(opt$output_dir, "histograms")
if (!dir.exists(hist_plots_dir)) dir.create(hist_plots_dir)
for (f in unique(df_binned$source_file)) {
  p <- df_binned %>% filter(source_file == f) %>%
    ggplot(aes(x = bin_A)) + geom_histogram(bins = 40, fill = "steelblue", color = "white") +
    theme_classic() + labs(title = f, x = "Binned intensity", y = "Count")
  ggsave(file.path(hist_plots_dir, paste0(f, "_hist.png")), p, width = 6, height = 4)
}

# Simple peak detection (local maxima) on the processed A_norm per sample
df_peaks <- df_processed %>% group_by(source_file) %>%
  arrange(desc(cm.1)) %>%
  mutate(prev = lag(A_norm), next = lead(A_norm)) %>%
  filter(!is.na(prev) & !is.na(next) & A_norm > prev & A_norm > next) %>%
  select(source_file, cm.1, A_norm)
write_csv(df_peaks, file.path(opt$output_dir, "ftir_peaks.csv"))

# Multivariate analysis (PCA) on binned data: samples x features
if (opt$do_pca) {
  wide_for_pca <- df_binned %>% select(source_file, bin, bin_A) %>%
    tidyr::pivot_wider(names_from = bin, values_from = bin_A)
  # pivot_wider creates one row per sample
  sample_names <- wide_for_pca$source_file
  mat <- as.matrix(wide_for_pca %>% select(-source_file))
  # replace NA with 0
  mat[is.na(mat)] <- 0
  pca <- prcomp(mat, center = TRUE, scale. = TRUE)
  pcs <- as.data.frame(pca$x)
  pcs$sample <- sample_names
  write_csv(pcs, file.path(opt$output_dir, "pca_scores.csv"))
  # simple scree
  scree <- data.frame(PC = paste0("PC", seq_along(pca$sdev)), Variance = (pca$sdev^2) / sum(pca$sdev^2))
  write_csv(scree, file.path(opt$output_dir, "pca_scree.csv"))
  library(ggplot2)
  p_scree <- ggplot(scree, aes(x = PC, y = Variance)) + geom_col(fill = "steelblue") + theme_classic()
  ggsave(file.path(opt$output_dir, "pca_scree.png"), p_scree, width = 6, height = 4)
  p_scores <- ggplot(pcs, aes(x = PC1, y = PC2, label = sample)) + geom_point() + geom_text(nudge_y = 0.02) + theme_classic()
  ggsave(file.path(opt$output_dir, "pca_scores.png"), p_scores, width = 6, height = 5)
}

message("Processing complete. Outputs written to: ", normalizePath(opt$output_dir))
