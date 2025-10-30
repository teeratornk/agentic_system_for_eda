#!/usr/bin/env python
"""
EDA Analysis Script: eda_analysis.py
===================================
This script performs a comprehensive Exploratory Data Analysis (EDA) on the
provided dataset. It follows the specification given by the data_planner and
internal developer instructions.

PHASE 1  - Basic Statistics
PHASE 2  - Advanced Analysis
PHASE 3  - Visualizations
PHASE 4  - Save Results (statistics, figures, reports)

Usage (from eda/ folder):
    python code/eda_analysis.py --data_path ../data/burgers_data_R10.mat

The script will automatically create the following sub-directories if they do
not exist:
    figures/, stats/, reports/

Outputs:
    stats/statistics.json         – all computed statistics (basic + advanced)
    figures/*                     – all generated plots
    reports/data_report.md        – human-readable markdown report
    reports/data_report.json      – JSON version of the report summary
"""

# --------------------------------------------------
# Imports
# --------------------------------------------------
import os
import json
import argparse
import warnings
from datetime import datetime
from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.fft import rfft, rfftfreq
from scipy.io import loadmat

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def ensure_dirs():
    """Create required directories if they do not exist."""
    for d in ["figures", "stats", "reports"]:
        os.makedirs(d, exist_ok=True)


def is_numeric_array(arr):
    """Return True if arr is a numpy ndarray of a numeric dtype."""
    return isinstance(arr, np.ndarray) and np.issubdtype(arr.dtype, np.number)


def flatten_if_needed(arr):
    """Flatten array if it's more than 1-D for statistics calculation."""
    if arr.ndim > 1:
        return arr.ravel()
    return arr


def compute_basic_stats(arr):
    """Compute basic descriptive statistics for a 1-D numeric array."""
    arr1d = flatten_if_needed(arr)
    arr1d = arr1d[~np.isnan(arr1d)]  # exclude NaNs for stats
    if arr1d.size == 0:
        return None  # All NaNs

    q25, q75 = np.percentile(arr1d, [25, 75])
    z_scores = np.abs(stats.zscore(arr1d))
    outliers = int(np.sum(z_scores > 3))

    return {
        "min": float(np.min(arr1d)),
        "max": float(np.max(arr1d)),
        "mean": float(np.mean(arr1d)),
        "std": float(np.std(arr1d, ddof=1)),
        "median": float(np.median(arr1d)),
        "q25": float(q25),
        "q75": float(q75),
        "outliers_z3": outliers,
        "missing": int(np.sum(np.isnan(arr))),
        "total": arr.size,
    }


def plot_histogram(arr, name):
    arr1d = flatten_if_needed(arr)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(arr1d, kde=True, ax=ax, bins="auto")
    ax.set_title(f"Histogram of {name}")
    ax.set_xlabel(name)
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    fig_path = os.path.join("figures", f"hist_{name}.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    return fig_path


def plot_heatmap(arr, name):
    if arr.ndim != 2:
        return None
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(arr, cmap="viridis", ax=ax)
    ax.set_title(f"Heatmap of {name}")
    fig.tight_layout()
    fig_path = os.path.join("figures", f"heatmap_{name}.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    return fig_path


def plot_timeseries(arr, name):
    if arr.ndim != 1:
        arr = flatten_if_needed(arr)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(arr)
    ax.set_title(f"Time Series Plot of {name}")
    ax.set_xlabel("Index")
    ax.set_ylabel(name)
    fig.tight_layout()
    fig_path = os.path.join("figures", f"timeseries_{name}.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    return fig_path


def plot_spectrum(arr, name, sampling_rate=1.0):
    arr1d = flatten_if_needed(arr)
    # Remove NaNs
    arr1d = arr1d[~np.isnan(arr1d)]
    N = len(arr1d)
    if N < 4:
        return None, None  # Too few points for FFT
    yf = rfft(arr1d)
    xf = rfftfreq(N, d=1.0 / sampling_rate)
    power = np.abs(yf) ** 2
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xf, power)
    ax.set_title(f"Power Spectrum of {name}")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power")
    ax.set_yscale("log")
    ax.set_xscale("log")
    fig.tight_layout()
    fig_path = os.path.join("figures", f"spectrum_{name}.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)

    # Return spectral summary (top 10 frequencies)
    top_idx = np.argsort(power)[-10:][::-1]
    spectral_summary = {
        "top_frequencies": xf[top_idx].tolist(),
        "top_powers": power[top_idx].tolist(),
    }
    return fig_path, spectral_summary


def plot_correlation_matrix(df, name="correlation_matrix"):
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Matrix (Pearson)")
    fig.tight_layout()
    fig_path = os.path.join("figures", f"{name}.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    return fig_path

# --------------------------------------------------
# Main Analysis Function
# --------------------------------------------------

def perform_eda(data_path):
    ensure_dirs()

    basic_stats = {}
    advanced_stats = {
        "correlations": {},
        "spectral": {},
        "patterns": {},
    }

    report_lines = [
        f"# Exploratory Data Analysis Report",
        f"*Date*: {datetime.now().isoformat()}",
        f"*Data File*: {data_path}",
        "\n---\n",
    ]

    # ----------------------------------------------
    # Load .mat data
    # ----------------------------------------------
    try:
        mat_data = loadmat(data_path)
        report_lines.append("## Data Loading Successful (MAT file)")
    except Exception as e:
        raise RuntimeError(f"Failed to load .mat file: {e}")

    # Remove MATLAB metadata keys
    mat_vars = {k: v for k, v in mat_data.items() if not k.startswith("__")}

    # Convert 1-D numeric vectors of different lengths to pandas Series for correlation later.
    candidate_corr_series = {}

    # Iterate over each variable in the .mat
    for var_name, var_value in mat_vars.items():
        # Skip non-numeric data
        if not is_numeric_array(var_value):
            warnings.warn(f"Skipping non-numeric variable: {var_name}")
            continue

        report_lines.append(f"### Variable: `{var_name}`")
        report_lines.append(f"Shape: {var_value.shape}, Dtype: {var_value.dtype}")

        # --------------------------------------------------
        # PHASE 1: Basic Statistics
        # --------------------------------------------------
        stats_dict = compute_basic_stats(var_value)
        if stats_dict is None:
            warnings.warn(f"Variable {var_name} contains only NaNs or is empty.")
            continue
        basic_stats[var_name] = stats_dict

        report_lines.append("#### Basic Statistics")
        report_lines.extend([f"- {k}: {v}" for k, v in stats_dict.items()])

        # --------------------------------------------------
        # PHASE 3: Visualizations per variable
        # --------------------------------------------------
        hist_path = plot_histogram(var_value, var_name)
        heat_path = plot_heatmap(var_value, var_name)
        ts_path = plot_timeseries(var_value, var_name)
        spec_path, spec_summary = plot_spectrum(var_value, var_name)

        if spec_summary is not None:
            advanced_stats["spectral"][var_name] = spec_summary
            report_lines.append("#### Spectral Summary (Top 10)")
            for f, p in zip(spec_summary["top_frequencies"], spec_summary["top_powers"]):
                report_lines.append(f"- Frequency: {f:.4g}, Power: {p:.4g}")

        # Save candidate for correlations if 1-D
        arr1d = flatten_if_needed(var_value)
        if arr1d.ndim == 1:
            candidate_corr_series[var_name] = pd.Series(arr1d)

    # ------------------------------------------------------
    # PHASE 2: Advanced Analysis – Correlations
    # ------------------------------------------------------
    if len(candidate_corr_series) >= 2:
        # Align series by truncating to min length
        min_len = min(len(s) for s in candidate_corr_series.values())
        aligned = {k: s.iloc[:min_len].reset_index(drop=True) for k, s in candidate_corr_series.items()}
        df_corr = pd.DataFrame(aligned)

        # Pearson & Spearman pairwise
        for (var1, var2) in combinations(df_corr.columns, 2):
            pearson_r, pearson_p = stats.pearsonr(df_corr[var1], df_corr[var2])
            spearman_r, spearman_p = stats.spearmanr(df_corr[var1], df_corr[var2])
            key = f"{var1}__{var2}"
            advanced_stats["correlations"][key] = {
                "pearson_r": float(pearson_r),
                "pearson_p": float(pearson_p),
                "spearman_r": float(spearman_r),
                "spearman_p": float(spearman_p),
            }

        # Plot correlation matrix
        corr_fig_path = plot_correlation_matrix(df_corr)
        report_lines.append("## Correlation Matrix generated.")

    # --------------------------------------------------
    # Save statistics JSON
    # --------------------------------------------------
    statistics_output = {
        "basic_stats": basic_stats,
        "advanced_stats": advanced_stats,
    }

    stats_path = os.path.join("stats", "statistics.json")
    with open(stats_path, "w") as f:
        json.dump(statistics_output, f, indent=2)

    # --------------------------------------------------
    # Save report files
    # --------------------------------------------------
    report_md_path = os.path.join("reports", "data_report.md")
    with open(report_md_path, "w") as f:
        f.write("\n".join(report_lines))

    report_json_path = os.path.join("reports", "data_report.json")
    with open(report_json_path, "w") as f:
        json.dump(statistics_output, f, indent=2)

    print("EDA complete! Results saved to stats/, figures/, and reports/ directories.")

# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Comprehensive EDA script")
    parser.add_argument(
        "--data_path",
        type=str,
        default="../data/burgers_data_R10.mat",
        help="Path to the .mat data file relative to eda folder",
    )
    args = parser.parse_args()

    perform_eda(args.data_path)


if __name__ == "__main__":
    main()
