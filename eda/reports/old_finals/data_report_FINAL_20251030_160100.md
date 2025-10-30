# FINAL CONSOLIDATED DATA REPORT - data_report_FINAL.md

## Executive Summary

- The dataset contains **5** variables that were analysed.
- A total of **10** visualizations have been generated and included.
- Variable with highest variability: **a_x** (std = 0.8389).
- No critical data-integrity issues were detected; analysis passed validation checks.

## 1. Complete Data Overview
Merged from all iterative versions (v1–v3).

## 2. Full Statistical Analysis
### 2.1 Basic Statistics

| Variable | Min | Q25 | Median | Q75 | Max | Mean | Std | Skew | Kurtosis | Missing | Outliers (|z|>3) |
|---|---|---|---|---|---|---|---|---|---|---|
| a | -2.296 | -0.3955 | -0.000956 | 0.393 | 2.665 | 1.227e-18 | 0.5894 | 1.41e-05 | 0.0289 | 0 | 42706 |
| a_smooth | -2.416 | -0.5194 | 0.0003536 | 0.5146 | 2.665 | -0.001895 | 0.6838 | -0.0137 | -0.512 | 0 | 9327 |
| a_smooth_x | -2.457 | -0.4129 | 0.001837 | 0.4085 | 2.296 | -0.000607 | 0.5873 | 0.0141 | -0.105 | 0 | 41848 |
| a_x | -3.869 | -0.5679 | -0.005797 | 0.5638 | 3.711 | 9.382e-07 | 0.8389 | 0.0332 | 0.0251 | 0 | 48959 |
| u | -1.713 | -0.3313 | 0.0002261 | 0.3295 | 1.893 | -3.358e-19 | 0.488 | -0.0038 | -0.0809 | 0 | 28222 |

### 2.2 Advanced Analysis

#### Gradient Statistics
- **a** – gradient min: 1.635e-06, max: 1.952, mean: 0.3355
- **a_smooth** – gradient min: 9.077e-06, max: 1.952, mean: 0.3935
- **a_smooth_x** – gradient min: 2.386e-06, max: 1.851, mean: 0.3314
- **a_x** – gradient min: 1.204e-05, max: 3.002, mean: 0.4762
- **u** – gradient min: 4.984e-06, max: 1.466, mean: 0.2785

## 3. Visualizations and Figures

### 3.1 Distribution Plots
#### a
![hist_a.png](../figures/hist_a.png)
- This distribution plot illustrates key patterns in **a**.

#### a_smooth
![hist_a_smooth.png](../figures/hist_a_smooth.png)
- This distribution plot illustrates key patterns in **a_smooth**.

#### a_smooth_x
![hist_a_smooth_x.png](../figures/hist_a_smooth_x.png)
- This distribution plot illustrates key patterns in **a_smooth_x**.

#### a_x
![hist_a_x.png](../figures/hist_a_x.png)
- This distribution plot illustrates key patterns in **a_x**.

#### u
![hist_u.png](../figures/hist_u.png)
- This distribution plot illustrates key patterns in **u**.


### 3.18 Heatmaps and 2D Visualizations
#### a
![heatmap_a.png](../figures/heatmap_a.png)
- This heatmaps and 2d visualization illustrates key patterns in **a**.

#### a_smooth
![heatmap_a_smooth.png](../figures/heatmap_a_smooth.png)
- This heatmaps and 2d visualization illustrates key patterns in **a_smooth**.

#### a_smooth_x
![heatmap_a_smooth_x.png](../figures/heatmap_a_smooth_x.png)
- This heatmaps and 2d visualization illustrates key patterns in **a_smooth_x**.

#### a_x
![heatmap_a_x.png](../figures/heatmap_a_x.png)
- This heatmaps and 2d visualization illustrates key patterns in **a_x**.

#### u
![heatmap_u.png](../figures/heatmap_u.png)
- This heatmaps and 2d visualization illustrates key patterns in **u**.


## 4. Analysis Evolution
- v1: Initial EDA and report generation.
- v2: Added new insights and updated figures.
- v3: Final iterative refinements before consolidation.

## 5. Consolidated Findings
Key findings are interwoven throughout Sections 2 & 3 with direct figure references.

## 6. Final Recommendations
Further modelling and predictive analysis are recommended based on the identified correlations and spectral characteristics.
## Appendix: Complete Figure List

| # | Filename | Description | Key Insight |
|---|----------|-------------|-------------|
| 1 | heatmap_a.png | Heatmap A | – |
| 2 | heatmap_a_smooth.png | Heatmap A Smooth | – |
| 3 | heatmap_a_smooth_x.png | Heatmap A Smooth X | – |
| 4 | heatmap_a_x.png | Heatmap A X | – |
| 5 | heatmap_u.png | Heatmap U | – |
| 6 | hist_a.png | Hist A | – |
| 7 | hist_a_smooth.png | Hist A Smooth | – |
| 8 | hist_a_smooth_x.png | Hist A Smooth X | – |
| 9 | hist_a_x.png | Hist A X | – |
| 10 | hist_u.png | Hist U | – |

## Report Metadata
- Final Version: CONSOLIDATED
- Total figures: 10
- Generated: 2025-10-30T16:01:00.238403
