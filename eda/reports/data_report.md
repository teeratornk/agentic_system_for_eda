---
# Exploratory Data Analysis Report  
Source file : `../data/burgers_data_R10.mat`  

## 1. Dataset Overview  
The MAT-file contains five numeric 2-D arrays, each representing a space–time field from the 1-D viscous Burgers’ equation or its post-processed derivatives.

| Variable      | Shape (rows × cols) | Elements | Data type | Mean  | Std-dev | Min  | Max  | Outliers (|z|>3) | % Outliers |
|---------------|--------------------|----------|-----------|-------|---------|------|------|-----------------|------------|
| a             | 2048 × 8192        | 16 777 216 | float64 | 1.9 × 10⁻¹⁹ | 0.589 | –2.30 | 2.66 | 42 706 | 0.25 % |
| a_smooth      | 2048 × 8192        | 16 777 216 | float64 | –1.9 × 10⁻³ | 0.684 | –2.42 | 2.66 | 9 327  | 0.056 % |
| a_smooth_x    | 2048 × 8191        | 16 775 168 | float64 | –6.1 × 10⁻⁴ | 0.587 | –2.46 | 2.30 | 41 848 | 0.25 % |
| a_x           | 2048 × 8191        | 16 775 168 | float64 | 9.4 × 10⁻⁷ | 0.839 | –3.87 | 3.71 | 48 959 | 0.29 % |
| u             | 2048 × 8192        | 16 777 216 | float64 | –1.1 × 10⁻¹⁸ | 0.488 | –1.71 | 1.89 | 28 222 | 0.17 % |

Key characteristics  
• No missing values (NaNs) detected.  
• All means ≈ 0, indicating numerically balanced signed data.  
• Standard deviations range 0.49–0.84; `a_x` is the most variable field.  
• Outlier prevalence is low (< 0.3 %) across all variables.

## 2. Variable-wise Insights  

### 2.1 `u` – Base field  
• Symmetric distribution centred at 0 (median ≈ 0).  
• Tight amplitude (|u| ≤ 1.9).  
• Suggests well-behaved solution of Burgers’ equation.

### 2.2 `a` – Possibly acceleration term  
• Slightly heavier tails than `u` (std = 0.589).  
• 42 706 statistical outliers, but ratio still tiny (0.25 %).  
• Distribution remains symmetric; no drift observed.

### 2.3 `a_smooth` – Smoothed acceleration  
• Higher spread (std = 0.684) after smoothing—indicates smoothing did not simply damp magnitude but redistributed energy.  
• Outlier count drops 4–5× relative to raw `a`, confirming smoothing efficacy.

### 2.4 `a_x` – Spatial derivative of acceleration  
• Largest range (–3.87 … 3.71) and highest std  (0.839).  
• Highest outlier share (0.29 %) – expected for derivative data which accentuates sharp gradients or shocks.

### 2.5 `a_smooth_x` – Spatial derivative of smoothed acceleration  
• Variability comparable to `a` (std ≈ 0.587).  
• Outlier fraction similar to `a`, indicating derivative re-introduces extremes even after smoothing.

## 3. Distribution & Visual Findings  
(Refer to figures/ for plots.)  
• Histograms confirm near-Gaussian, zero-mean behaviour with mild kurtosis.  
• Heat-maps illustrate coherent shock-like structures travelling in time.  
• No block artifacts or missing tiles detected; field continuity looks intact.

## 4. Anomaly & Quality Checks  
• No NaNs / Infs.  
• Low outlier ratios; no catastrophic spikes.  
• Value ranges are physically plausible for standardised Burgers’ simulations.

## 5. Recommendations  
1. Normalisation: Zero-mean, unit-variance scaling is straightforward due to symmetric distributions.  
2. Outlier handling: Given ≤ 0.3 %, simply retain; robust models (e.g., Huber loss) can accommodate.  
3. Data reduction: Shapes are large (~16 M cells each). Consider:  
   • Coarser spatial sampling (e.g., every 2–4 grid points) if memory is an issue.  
   • Storing in single-precision float32 to halve disk footprint.  
4. Feature engineering:  
   • Temporal derivatives (u_t) could complement the spatial derivatives already provided.  
   • Shock indicator (|∂u/∂x| threshold) as a binary mask for physics-informed ML.  
5. Validation: If multiple realisations exist, compare statistics across runs to ensure consistency.

## 6. Next Steps  
• Integrate normalised tensors into downstream training pipeline.  
• Run dimensionality reduction (PCA/Autoencoders) to explore latent structure.  
• Evaluate surrogate models (e.g., CNNs, FNO) using `u` as target, derivatives as auxiliary inputs.

---
