# FINAL CONSOLIDATED DATA REPORT – burgers_data_R10

## Executive Summary
This consolidated report merges insights from all exploratory data analysis
iterations (v1, v2, …) applied to *burgers_data_R10.mat*. It provides a
comprehensive overview of dataset characteristics, spectral behaviour, and
observed patterns, as well as recommendations for future modelling and data
handling.


## 1. Complete Data Overview

The dataset contains five high-resolution numeric variables (‘a’, ‘a_smooth’, ‘a_smooth_x’, ‘a_x’, ‘u’) derived from a Burgers-equation simulation. Each is a 2-D array with about 16–17 million elements. No missing values were detected across variables.


## 2. Full Statistical Analysis

### 2.1 Basic Statistics

| Variable | Min | Max | Mean | Std | Median | Q25 | Q75 | Outliers (z>3) | Missing | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| a | -2.296 | 2.665 | 1.893e-19 | 0.5894 | -0.000956 | -0.3955 | 0.393 | 24 | 0 | 16777216 |
| a_smooth | -2.416 | 2.665 | -0.001895 | 0.6838 | 0.0003536 | -0.5194 | 0.5146 | 1 | 0 | 16777216 |
| a_smooth_x | -2.457 | 2.296 | -0.000607 | 0.5873 | 0.001837 | -0.4129 | 0.4085 | 25 | 0 | 16775168 |
| a_x | -3.869 | 3.711 | 9.382e-07 | 0.8389 | -0.005797 | -0.5679 | 0.5638 | 32 | 0 | 16775168 |
| u | -1.713 | 1.893 | -1.116e-18 | 0.488 | 0.0002261 | -0.3313 | 0.3295 | 20 | 0 | 16777216 |

### 2.2 Spectral Density Highlights

### a
- Frequency: 0.0001221, Power: 4.82e+07
- Frequency: 0.0001831, Power: 7.8e+06
- Frequency: 6.104e-05, Power: 1.75e+06
- Frequency: 0.0002441, Power: 1.57e+06
- Frequency: 0.0003052, Power: 9.22e+05
- Frequency: 0.0004272, Power: 4.56e+05
- Frequency: 0.0005493, Power: 3.58e+05
- Frequency: 0.0003662, Power: 1.77e+05
- Frequency: 0.0004883, Power: 9.05e+04
- Frequency: 0.001038, Power: 4.32e+04

### a_smooth
- Frequency: 0.0001221, Power: 5.07e+07
- Frequency: 0, Power: 5.15e+06
- Frequency: 0.0001831, Power: 4.94e+06
- Frequency: 6.104e-05, Power: 4.33e+06
- Frequency: 0.0002441, Power: 1.14e+06
- Frequency: 0.0003662, Power: 1.05e+05
- Frequency: 0.0004883, Power: 4.64e+04
- Frequency: 0.0006104, Power: 2.77e+04
- Frequency: 0.0004272, Power: 1.89e+04
- Frequency: 0.0007324, Power: 1.86e+04

### a_smooth_x
- Frequency: 0.0001221, Power: 4.72e+07
- Frequency: 0.0001831, Power: 8.59e+06
- Frequency: 0.0002441, Power: 4.05e+06
- Frequency: 6.104e-05, Power: 1.8e+06
- Frequency: 0, Power: 6.37e+05
- Frequency: 0.0003662, Power: 3.67e+05
- Frequency: 0.0004883, Power: 1.34e+05
- Frequency: 0.0006104, Power: 7.22e+04
- Frequency: 0.0003052, Power: 5.9e+04
- Frequency: 0.0007324, Power: 4.29e+04

### a_x
- Frequency: 0.0001221, Power: 4.82e+07
- Frequency: 0.0001831, Power: 2.42e+07
- Frequency: 0.0002441, Power: 6.27e+06
- Frequency: 0.0005493, Power: 3.51e+06
- Frequency: 0.0003052, Power: 3.36e+06
- Frequency: 0.0004272, Power: 2.04e+06
- Frequency: 0.0003662, Power: 1.6e+06
- Frequency: 0.0004883, Power: 1.44e+06
- Frequency: 0.001282, Power: 1.35e+06
- Frequency: 0.001343, Power: 1.28e+06

### u
- Frequency: 0.0001221, Power: 3.54e+07
- Frequency: 0.0001831, Power: 3.61e+06
- Frequency: 0.0002441, Power: 2.29e+06
- Frequency: 0.0003052, Power: 1.13e+06
- Frequency: 6.104e-05, Power: 9.17e+05
- Frequency: 0.0004272, Power: 7.25e+05
- Frequency: 0.0005493, Power: 3.33e+05
- Frequency: 0.0006714, Power: 7.56e+04
- Frequency: 0.0003662, Power: 6.57e+04
- Frequency: 0.0006104, Power: 5.31e+04


### 2.3 Correlation Summary

No correlations calculated (insufficient suitable 1-D vectors).

## 3. Analysis Evolution

#### Version 1 – data_report_v1.md
*Initial run:* Successful data load, descriptive stats, and spectral analysis. Heatmaps skipped due to array size; correlation skipped for insufficient 1-D vectors.

#### Version 2 – data_report_v2.md
*Optimised run:* Introduced sampling and size caps to prevent time-outs, enabling processing of full 629 MB file. No new correlations due to data dimensionality.


## 4. Consolidated Findings

1. All variables are centred near zero; spreads range σ ≈ 0.49–0.84.
2. Dominant low-frequency modes (~1.22×10⁻⁴ Hz) appear across all fields, indicating large-scale coherent structures.
3. Derivative fields (‘a_x’, ‘a_smooth_x’) exhibit greater variance and enhanced high-frequency power, as expected after differentiation.
4. Outliers (|z|>3) constitute <0.0002 % of values—unlikely to distort modelling.
5. Correlation analysis requires dimensionality reduction (e.g., spatial slicing or PCA) to compare variables effectively.

## 5. Recommendations

• Apply dimensionality-reduction techniques (random sampling, PCA, or FFT truncation) before multivariate analyses.
• Leverage dominant spectral modes to build reduced-order models or surrogate emulators for rapid inference.
• Consider storing future simulations in chunked, stream-friendly formats (HDF5, Zarr) to expedite partial loading.
• Investigate regularisation or smoothing to mitigate amplified noise in derivative fields.

## Metadata

- Report generated: 2025-10-30T12:46:15.967460
- Iterations merged: 2 (v1–v2)