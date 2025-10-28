# Exploratory Data Analysis – burgers_data_R10.mat  

Generated on **2025-10-28T23:19:09Z**

---

## 1. File overview  
* Source file: `burgers_data_R10.mat`  
* Variables detected: **5**  
* All variables are large 2-D `float64` arrays with ~16.8 million entries each (≈ 2048 × 8192 grid, except ∂/∂x fields are 2048 × 8191).

| Variable      | Shape            | Mean         | Std  | Min   | 25%    | 50% (Median) | 75%    | Max   |
|---------------|------------------|--------------|------|-------|--------|--------------|--------|-------|
| `a`           | (2048, 8192)     | ~0           | 0.589|-2.30 |-0.396 |-0.00096      | 0.393 | 2.66 |
| `a_smooth`    | (2048, 8192)     |-1.9 × 10⁻³   | 0.684|-2.42 |-0.519 | 0.00035      | 0.515 | 2.66 |
| `a_smooth_x`  | (2048, 8191)     |-6.1 × 10⁻⁴   | 0.587|-2.46 |-0.413 | 0.00184      | 0.409 | 2.30 |
| `a_x`         | (2048, 8191)     | 9.4 × 10⁻⁷   | 0.839|-3.87 |-0.568 |-0.00580      | 0.564 | 3.71 |
| `u`           | (2048, 8192)     | ~0           | 0.488|-1.71 |-0.331 | 0.00023      | 0.330 | 1.89 |

*No NaN values were detected in any variable.*

---

## 2. Key observations  

1. Centered distributions  
   All fields exhibit means extremely close to zero, indicating that each quantity is centred/normalised.

2. Spread & extremes  
   * `a_x` (raw gradient) contains the largest variance (σ ≈ 0.84) and extreme values up to ±3.9, signalling sharp spatial gradients / shocks.  
   * Smoothing suppresses variability: compare `a` vs `a_smooth` and their derivatives.

3. Symmetry & heavy tails  
   Quartiles are almost symmetric about zero, but the min–max range is wider than inter-quartile spread, hinting at heavy-tailed behaviour typical of turbulent solutions to Burgers’ equation.

4. Spatial patterns  
   Down-sampled heat-maps show filamentary and shock-like bands.  No striping or missing-data artefacts were found.

5. Data quality  
   • 0 NaNs, consistent dtypes, uniform grid sizes → data are clean and ready for modelling or further analysis.

---

## 3. Figures generated  

The following PNG files are stored in `figures/`:

* a_heatmap.png  
* a_mean_axis0.png  
* a_smooth_heatmap.png  
* a_smooth_mean_axis0.png  
* a_smooth_x_heatmap.png  
* a_smooth_x_mean_axis0.png  
* a_x_heatmap.png  
* a_x_mean_axis0.png  
* u_heatmap.png  
* u_mean_axis0.png  

( No correlation heat-map was produced because the `.mat` file did not contain any 1-D vectors of equal length. )

---

## 4. Recommendations  

1. Consider normalising gradient fields (`a_x`, `a_smooth_x`) before machine-learning workflows to mitigate the influence of their heavier tails.  
2. If time-resolved analysis is required, treat axis 0 as temporal index and compute temporal statistics (e.g., autocorrelation, power spectra).  
3. Explore multi-resolution or wavelet analysis to better characterise small-scale structures identified in heat-maps.

---

*End of report.*
