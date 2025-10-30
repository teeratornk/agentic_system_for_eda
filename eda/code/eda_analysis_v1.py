# eda_analysis.py
"""
Comprehensive Exploratory Data Analysis Script
================================================
This script performs the following phases on a given dataset (MATLAB .mat file or other
supported formats):
    PHASE 1 - Basic Statistics
    PHASE 2 - Advanced Analysis
    PHASE 3 - Visualizations
    PHASE 4 - Save Results (statistics & figures)

It adheres to the specification defined by the data_planner & developer instructions.

Usage (from eda folder):
    python code/eda_analysis.py ../data/burgers_data_R10.mat

Outputs:
  stats/statistics.json         - All basic & advanced metrics in JSON
  figures/                      - Folder with all generated visualizations (.png)
  reports/data_report.md        - Human-readable markdown summary
  reports/data_report.json      - Machine-readable summary of findings
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import scipy.io as sio
import scipy.stats as stats
from scipy.signal import welch
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------------------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------------------------------------

def make_dirs():
    """Ensure output directories exist"""
    for d in ["stats", "figures", "reports"]:
        Path(d).mkdir(parents=True, exist_ok=True)


def load_mat_file(file_path: str) -> Dict[str, Any]:
    """Load MATLAB .mat file and remove meta keys"""
    data = sio.loadmat(file_path)
    clean_data = {k: v for k, v in data.items() if not k.startswith("__")}
    return clean_data


# ----------------------------------------------------------------------------------------------
# PHASE 1 – Basic Statistics
# ----------------------------------------------------------------------------------------------

def compute_basic_stats(arr: np.ndarray) -> Dict[str, Any]:
    """Compute core descriptive statistics for a numeric numpy array"""
    flat = arr.flatten(order="C").astype(float)
    flat_no_nan = flat[~np.isnan(flat)] if np.isnan(flat).any() else flat

    stats_dict = {
        "shape": list(arr.shape),
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "mean": float(np.nanmean(arr)),
        "std": float(np.nanstd(arr)),
        "median": float(np.nanmedian(arr)),
        "q25": float(np.nanpercentile(arr, 25)),
        "q75": float(np.nanpercentile(arr, 75)),
        "missing_values": int(np.isnan(flat).sum()),
        "total_values": int(flat.size),
    }

    # Outlier detection using z-score (>3 or <-3)
    if flat_no_nan.size > 0:
        z_scores = stats.zscore(flat_no_nan)
        outliers = np.where(np.abs(z_scores) > 3)[0]
        stats_dict["outliers_z3"] = int(outliers.size)
    else:
        stats_dict["outliers_z3"] = 0

    # Distribution characteristics
    if flat_no_nan.size > 0:
        stats_dict["skewness"] = float(stats.skew(flat_no_nan))
        stats_dict["kurtosis"] = float(stats.kurtosis(flat_no_nan))
    else:
        stats_dict["skewness"] = None
        stats_dict["kurtosis"] = None

    return stats_dict


# ----------------------------------------------------------------------------------------------
# PHASE 2 – Advanced Analysis
# ----------------------------------------------------------------------------------------------

def compute_correlations(vars_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    """Compute Pearson & Spearman correlations between 1D variables of equal length"""
    # Prepare only 1D arrays with same length
    one_d_vars = {k: v.flatten() for k, v in vars_dict.items() if v.ndim == 1}
    lengths = {k: len(v) for k, v in one_d_vars.items()}
    if not lengths:
        return {}
    # Choose the most common length
    common_len = max(set(lengths.values()), key=list(lengths.values()).count)
    aligned_vars = {k: v for k, v in one_d_vars.items() if len(v) == common_len}

    var_names = list(aligned_vars.keys())
    pearson_mat = {}
    spearman_mat = {}

    for i, v1 in enumerate(var_names):
        pearson_mat[v1] = {}
        spearman_mat[v1] = {}
        for j, v2 in enumerate(var_names):
            if j < i:
                # Mirror value to keep matrix symmetrical
                pearson_mat[v1][v2] = pearson_mat[v2][v1]
                spearman_mat[v1][v2] = spearman_mat[v2][v1]
                continue
            if v1 == v2:
                pearson_mat[v1][v2] = 1.0
                spearman_mat[v1][v2] = 1.0
            else:
                pearson_mat[v1][v2] = float(stats.pearsonr(aligned_vars[v1], aligned_vars[v2])[0])
                spearman_mat[v1][v2] = float(stats.spearmanr(aligned_vars[v1], aligned_vars[v2])[0])
    return {"pearson": pearson_mat, "spearman": spearman_mat}


def compute_spectral_analysis(vars_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, Any]]:
    """Compute spectral analysis (Welch power spectrum) for 1D numeric variables"""
    spectral_results = {}
    for name, arr in vars_dict.items():
        if arr.ndim != 1:
            continue
        data = arr.astype(float)
        # Remove NaNs
        data = data[~np.isnan(data)]
        if data.size < 8:
            continue
        freqs, pxx = welch(data, nperseg=min(256, data.size))
        dominant_idx = np.argmax(pxx)
        spectral_results[name] = {
            "dominant_frequency": float(freqs[dominant_idx]),
            "max_power": float(pxx[dominant_idx]),
        }
    return spectral_results


def compute_gradient_analysis(vars_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, Any]]:
    """Compute gradient statistics for multi-dimensional arrays"""
    grad_results = {}
    for name, arr in vars_dict.items():
        if arr.ndim < 2:
            continue
        try:
            grads = np.gradient(arr)
            if isinstance(grads, list):
                grads = np.stack(grads, axis=0)
            grad_mag = np.sqrt(np.sum(np.square(grads), axis=0))
            grad_results[name] = {
                "gradient_min": float(np.nanmin(grad_mag)),
                "gradient_max": float(np.nanmax(grad_mag)),
                "gradient_mean": float(np.nanmean(grad_mag)),
            }
        except Exception as e:
            grad_results[name] = {"error": str(e)}
    return grad_results


# ----------------------------------------------------------------------------------------------
# PHASE 3 – Visualizations
# ----------------------------------------------------------------------------------------------

def save_histogram(name: str, arr: np.ndarray):
    plt.figure(figsize=(6, 4))
    flat = arr.flatten()
    flat = flat[~np.isnan(flat)]
    sns.histplot(flat, kde=True, bins=50, color="skyblue")
    plt.title(f"Histogram ‑ {name}")
    plt.xlabel(name)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"figures/hist_{name}.png")
    plt.close()


def save_heatmap(name: str, arr: np.ndarray):
    plt.figure(figsize=(6, 5))
    sns.heatmap(arr, cmap="viridis")
    plt.title(f"Heatmap ‑ {name}")
    plt.tight_layout()
    plt.savefig(f"figures/heatmap_{name}.png")
    plt.close()


def save_timeseries(name: str, arr: np.ndarray):
    plt.figure(figsize=(8, 4))
    plt.plot(arr)
    plt.title(f"Time Series ‑ {name}")
    plt.xlabel("Index")
    plt.ylabel(name)
    plt.tight_layout()
    plt.savefig(f"figures/ts_{name}.png")
    plt.close()


def save_spectral_plot(name: str, arr: np.ndarray):
    data = arr[~np.isnan(arr)]
    freqs, pxx = welch(data, nperseg=min(256, data.size))
    plt.figure(figsize=(6, 4))
    plt.semilogy(freqs, pxx)
    plt.title(f"Power Spectrum ‑ {name}")
    plt.xlabel("Frequency")
    plt.ylabel("Power (dB)")
    plt.tight_layout()
    plt.savefig(f"figures/spectral_{name}.png")
    plt.close()


def save_correlation_heatmap(corr_dict: Dict[str, Dict[str, float]], method_name: str):
    if not corr_dict:
        return
    corr_matrix = sns.color_palette("rocket")  # dummy to ensure seaborn is loaded
    names = list(corr_dict.keys())
    mat = np.array([[corr_dict[i][j] for j in names] for i in names])
    plt.figure(figsize=(8, 6))
    sns.heatmap(mat, xticklabels=names, yticklabels=names, annot=True, vmin=-1, vmax=1, cmap="coolwarm")
    plt.title(f"{method_name.capitalize()} Correlation Matrix")
    plt.tight_layout()
    plt.savefig(f"figures/corr_{method_name}.png")
    plt.close()


# ----------------------------------------------------------------------------------------------
# PHASE 4 – Reporting Helpers
# ----------------------------------------------------------------------------------------------

def save_statistics_json(stats_obj: Dict[str, Any]):
    with open("stats/statistics.json", "w") as f:
        json.dump(stats_obj, f, indent=2)


def save_report_md(stats_obj: Dict[str, Any]):
    md_lines = ["# Data Analysis Report\n"]
    md_lines.append("## Basic Statistics\n")
    for var, d in stats_obj["basic_stats"].items():
        md_lines.append(f"### {var}\n")
        for k, v in d.items():
            md_lines.append(f"* **{k}**: {v}")
        md_lines.append("")
    md_lines.append("\n## Advanced Analysis\n")
    md_lines.append("### Correlations\n")
    md_lines.append("Correlation matrices saved under figures/.\n")
    md_lines.append("### Spectral Analysis\n")
    for var, d in stats_obj["advanced_stats"].get("spectral", {}).items():
        md_lines.append(f"* {var}: dominant freq = {d['dominant_frequency']:.4f}, max power = {d['max_power']:.4e}")
    md_lines.append("\n### Gradient Analysis\n")
    for var, d in stats_obj["advanced_stats"].get("gradient", {}).items():
        md_lines.append(f"* {var}: {d}")
    with open("reports/data_report.md", "w") as f:
        f.write("\n".join(md_lines))


def save_report_json(stats_obj: Dict[str, Any]):
    with open("reports/data_report.json", "w") as f:
        json.dump(stats_obj, f, indent=2)


# -------------------------------------------------------------------------------------------------
# Main execution
# -------------------------------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python code/eda_analysis.py <path_to_data_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"ERROR: File not found – {file_path}")
        sys.exit(1)

    make_dirs()

    # ---------- Load data ----------
    try:
        data_dict = load_mat_file(file_path)
    except Exception as e:
        print(f"Failed loading .mat file: {e}")
        sys.exit(1)

    # Containers for statistics
    basic_stats_all: Dict[str, Any] = {}

    # ---------- Phase 1: Basic Stats & visualizations ----------
    for var_name, value in data_dict.items():
        if not isinstance(value, np.ndarray):
            continue  # skip non-array entries
        basic_stats_all[var_name] = compute_basic_stats(value)

        # Visualizations
        try:
            if value.ndim == 1:
                save_histogram(var_name, value)
                save_timeseries(var_name, value)
            elif value.ndim == 2:
                save_heatmap(var_name, value)
                # also histogram of flattened values
                save_histogram(var_name, value)
            else:
                # high-dim: just histogram of flattened
                save_histogram(var_name, value)
        except Exception as e:
            print(f"Visualization error for {var_name}: {e}")

    # ---------- Phase 2: Advanced Analysis ----------
    correlations = compute_correlations(data_dict)
    spectral = compute_spectral_analysis(data_dict)
    gradient = compute_gradient_analysis(data_dict)

    # Correlation heatmaps
    if correlations.get("pearson"):
        save_correlation_heatmap(correlations["pearson"], "pearson")
    if correlations.get("spearman"):
        save_correlation_heatmap(correlations["spearman"], "spearman")

    # Spectral plots
    for var_name, arr in data_dict.items():
        if arr.ndim == 1 and var_name in spectral:
            try:
                save_spectral_plot(var_name, arr)
            except Exception as e:
                print(f"Spectral plot error for {var_name}: {e}")

    # ---------- Combine statistics ----------
    stats_obj = {
        "basic_stats": basic_stats_all,
        "advanced_stats": {
            "correlations": correlations,
            "spectral": spectral,
            "gradient": gradient,
        },
    }

    # ---------- Phase 3 & 4: Save outputs ----------
    save_statistics_json(stats_obj)
    save_report_md(stats_obj)
    save_report_json(stats_obj)

    print("Analysis complete. Results saved to stats/, figures/, and reports/ directories.")


if __name__ == "__main__":
    main()
