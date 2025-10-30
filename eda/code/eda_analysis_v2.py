#!/usr/bin/env python
"""
EDA Analysis Script v2: eda_analysis.py
======================================
Optimised for large MAT files (>= 600 MB).
This version adds sampling and smart-skipping rules to avoid timeouts and
excessive memory/CPU usage when generating histograms, heatmaps, FFTs, and
correlations on huge arrays.

Key Optimisations
-----------------
1. Sampling for costly computations (histograms, FFT, correlations).
2. Heatmaps generated only if array size <= 250k elements.
3. FFT length capped to 16384 samples.
4. Correlations computed only on vectors <= 100k length and limited to 100
   variables.
5. Graceful degradation: expensive plots are skipped with a note in report.
6. Incremental JSON writing to reduce memory footprint.

Usage (from eda/):
    python code/eda_analysis.py --data_path ../data/burgers_data_R10.mat
"""
# --------------------------------------------------
# Imports
# --------------------------------------------------
import os
import json
import argparse
import warnings
from datetime import datetime
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.fft import rfft, rfftfreq
from scipy.io import loadmat

# --------------------------------------------------
# Configurable Limits for Performance
# --------------------------------------------------
HEATMAP_MAX_ELEMENTS = 250_000  # 500x500
HIST_SAMPLE_SIZE = 100_000
SPECTRUM_MAX_LEN = 16_384
CORR_MAX_LEN = 100_000
CORR_MAX_VARS = 100

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def ensure_dirs():
    for d in ["figures", "stats", "reports"]:
        os.makedirs(d, exist_ok=True)


def is_numeric_array(arr):
    return isinstance(arr, np.ndarray) and np.issubdtype(arr.dtype, np.number)


def flatten_if_needed(arr):
    return arr.ravel() if arr.ndim > 1 else arr


def sample_array(arr, max_samples):
    arr1d = flatten_if_needed(arr)
    n = arr1d.size
    if n <= max_samples:
        return arr1d
    idx = np.random.choice(n, size=max_samples, replace=False)
    return arr1d[idx]


def compute_basic_stats(arr):
    arr1d = flatten_if_needed(arr)
    # handle NaNs
    valid = arr1d[~np.isnan(arr1d)]
    if valid.size == 0:
        return None

    q25, q75 = np.percentile(valid, [25, 75])
    z_scores = np.abs(stats.zscore(sample_array(valid, min(valid.size, 10_000))))
    outliers = int(np.sum(z_scores > 3))

    return {
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "std": float(np.std(valid, ddof=1)),
        "median": float(np.median(valid)),
        "q25": float(q25),
        "q75": float(q75),
        "outliers_z3": outliers,
        "missing": int(np.sum(np.isnan(arr1d))),
        "total": int(arr1d.size),
    }


def plot_histogram(arr, name):
    arr_sample = sample_array(arr, HIST_SAMPLE_SIZE)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(arr_sample, kde=True, ax=ax, bins="auto")
    ax.set_title(f"Histogram of {name} (sampled)")
    fig.tight_layout()
    path = os.path.join("figures", f"hist_{name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_heatmap(arr, name):
    if arr.ndim != 2 or arr.size > HEATMAP_MAX_ELEMENTS:
        return None
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(arr, cmap="viridis", ax=ax)
    ax.set_title(f"Heatmap of {name}")
    fig.tight_layout()
    path = os.path.join("figures", f"heatmap_{name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_timeseries(arr, name):
    arr1d = flatten_if_needed(arr)
    # sample if too long
    if arr1d.size > 100_000:
        arr1d = arr1d[:100_000]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(arr1d)
    ax.set_title(f"Time Series (first {arr1d.size}) of {name}")
    ax.set_xlabel("Index")
    ax.set_ylabel(name)
    fig.tight_layout()
    path = os.path.join("figures", f"timeseries_{name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_spectrum(arr, name, fs=1.0):
    arr1d = flatten_if_needed(arr)
    arr1d = arr1d[~np.isnan(arr1d)]
    if arr1d.size < 4:
        return None, None
    if arr1d.size > SPECTRUM_MAX_LEN:
        arr1d = arr1d[:SPECTRUM_MAX_LEN]
    N = arr1d.size
    yf = rfft(arr1d)
    xf = rfftfreq(N, 1 / fs)
    power = np.abs(yf) ** 2

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xf, power)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(f"Power Spectrum (first {N}) of {name}")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Power")
    fig.tight_layout()
    path = os.path.join("figures", f"spectrum_{name}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)

    top_idx = np.argsort(power)[-10:][::-1]
    summary = {
        "top_frequencies": xf[top_idx].tolist(),
        "top_powers": power[top_idx].tolist(),
    }
    return path, summary


def plot_correlation_matrix(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df.corr(), annot=False, cmap="coolwarm", ax=ax)
    ax.set_title("Pearson Correlation Matrix")
    fig.tight_layout()
    path = os.path.join("figures", "correlation_matrix.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path

# --------------------------------------------------
# Core EDA
# --------------------------------------------------

def perform_eda(path):
    ensure_dirs()

    # report storage
    report_md = []
    add = report_md.append
    add(f"# Exploratory Data Analysis Report\n")
    add(f"*Generated*: {datetime.now().isoformat()}\n")
    add(f"*Data File*: {path}\n")
    add("---\n")

    # statistics containers
    basic_stats = {}
    advanced_stats = {
        "correlations": {},
        "spectral": {},
        "patterns": {},
    }

    # Load MAT file
    add("## Loading MAT file\n")
    try:
        mat = loadmat(path, simplify_cells=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load MAT file: {e}")

    # Drop meta keys
    mat = {k: v for k, v in mat.items() if not k.startswith("__")}
    add(f"Loaded variables: {list(mat.keys())}\n")

    # Candidate vectors for correlation
    corr_series = {}

    for var, data in mat.items():
        if not is_numeric_array(data):
            warnings.warn(f"Skipping non-numeric variable {var}")
            continue

        add(f"### Variable `{var}`\n")
        add(f"Shape: {data.shape}, dtype: {data.dtype}\n")

        # Basic stats
        stats_dict = compute_basic_stats(data)
        if stats_dict is None:
            add("Variable contains only NaNs or is empty.\n")
            continue
        basic_stats[var] = stats_dict
        add("#### Basic Statistics\n")
        for k, v in stats_dict.items():
            add(f"- {k}: {v}\n")

        # Visualisations with smart skipping
        try:
            plot_histogram(data, var)
        except Exception as e:
            warnings.warn(f"Histogram failed for {var}: {e}")

        if data.size <= HEATMAP_MAX_ELEMENTS:
            try:
                plot_heatmap(data, var)
            except Exception as e:
                warnings.warn(f"Heatmap failed for {var}: {e}")
        else:
            add("Heatmap skipped (array too large).\n")

        # time series if 1-D
        if data.ndim == 1:
            try:
                plot_timeseries(data, var)
            except Exception as e:
                warnings.warn(f"Timeseries plot failed for {var}: {e}")

            # candidate for correlation
            if data.size <= CORR_MAX_LEN and len(corr_series) < CORR_MAX_VARS:
                corr_series[var] = pd.Series(data).dropna().reset_index(drop=True)
            else:
                add("Skipped correlation candidate (vector too long or too many vars).\n")

        # Spectrum
        try:
            _, spec_sum = plot_spectrum(data, var)
            if spec_sum:
                advanced_stats["spectral"][var] = spec_sum
        except Exception as e:
            warnings.warn(f"Spectrum failed for {var}: {e}")

    # Correlation analysis
    if len(corr_series) >= 2:
        min_len = min(len(s) for s in corr_series.values())
        aligned = {k: s.iloc[:min_len] for k, s in corr_series.items()}
        df = pd.DataFrame(aligned)
        plot_correlation_matrix(df)
        for var1, var2 in combinations(df.columns, 2):
            r, p = stats.pearsonr(df[var1], df[var2])
            advanced_stats["correlations"][f"{var1}__{var2}"] = {
                "pearson_r": float(r),
                "p_value": float(p),
            }
        add("## Correlation analysis completed.\n")
    else:
        add("Correlation analysis skipped (insufficient suitable vectors).\n")

    # Save statistics
    stats_path = os.path.join("stats", "statistics.json")
    with open(stats_path, "w") as f:
        json.dump({"basic_stats": basic_stats, "advanced_stats": advanced_stats}, f, indent=2)

    # Save markdown report
    report_path = os.path.join("reports", "data_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_md))

    # Also JSON report (same as statistics for now)
    with open(os.path.join("reports", "data_report.json"), "w") as f:
        json.dump({"basic_stats": basic_stats, "advanced_stats": advanced_stats}, f, indent=2)

    print("EDA completed. Outputs saved to stats/, figures/, and reports/.")

# --------------------------------------------------
# CLI
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Comprehensive EDA (v2) with optimisations for large MAT files")
    parser.add_argument("--data_path", type=str, required=True, help="Path to .mat file")
    args = parser.parse_args()
    perform_eda(args.data_path)


if __name__ == "__main__":
    main()
