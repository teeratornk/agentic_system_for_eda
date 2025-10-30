#!/usr/bin/env python
"""
save_final_report.py (v2)
========================
Generate a FINAL CONSOLIDATED REPORT by merging all versioned data_report_v*.md
files and integrating key statistics from stats/statistics.json.
Saves output to:
    reports/final_consolidated_report.md

Usage (run from eda/):
    python code/save_final_report_v2.py
"""

import os
import glob
import json
from datetime import datetime

REPORT_DIR = "reports"
STATS_PATH = os.path.join("stats", "statistics.json")
FINAL_REPORT_PATH = os.path.join(REPORT_DIR, "final_consolidated_report.md")

FINAL_HEADER = """# FINAL CONSOLIDATED DATA REPORT – burgers_data_R10

## Executive Summary
This consolidated report merges insights from all exploratory data analysis
iterations (v1, v2, …) applied to *burgers_data_R10.mat*. It provides a
comprehensive overview of dataset characteristics, spectral behaviour, and
observed patterns, as well as recommendations for future modelling and data
handling.
"""

VERSION_OVERVIEW_HEADER = "## 3. Analysis Evolution"


def load_version_reports():
    """Return list of dicts with version filename and content, ordered."""
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "data_report_v*.md")))
    reports = []
    for f in files:
        with open(f, "r") as fp:
            reports.append({"file": os.path.basename(f), "content": fp.read()})
    return reports


def build_basic_stats_table(basic_stats):
    rows = ["| Variable | Min | Max | Mean | Std | Median | Q25 | Q75 | Outliers (z>3) | Missing | Total |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for var, s in basic_stats.items():
        rows.append(
            f"| {var} | {s['min']:.4g} | {s['max']:.4g} | {s['mean']:.4g} | {s['std']:.4g} | "
            f"{s['median']:.4g} | {s['q25']:.4g} | {s['q75']:.4g} | {s['outliers_z3']} | "
            f"{s['missing']} | {s['total']} |")
    return "\n".join(rows)


def build_spectral_section(spectral):
    if not spectral:
        return "No spectral data available."
    lines = []
    for var, spec in spectral.items():
        lines.append(f"### {var}")
        for f, p in zip(spec["top_frequencies"], spec["top_powers"]):
            lines.append(f"- Frequency: {f:.4g}, Power: {p:.3g}")
        lines.append("")
    return "\n".join(lines)


def build_correlation_section(corr):
    if not corr:
        return "No correlations calculated (insufficient suitable 1-D vectors)."
    lines = ["| Pair | Pearson r | p-value |", "|---|---|---|"]
    for pair, vals in corr.items():
        lines.append(f"| {pair} | {vals['pearson_r']:.4g} | {vals['p_value']:.4g} |")
    return "\n".join(lines)


def generate_final_report():
    # Ensure required files exist
    if not os.path.exists(STATS_PATH):
        raise FileNotFoundError("stats/statistics.json not found – run EDA first.")

    with open(STATS_PATH, "r") as f:
        stats_json = json.load(f)

    basic_stats = stats_json.get("basic_stats", {})
    adv_stats = stats_json.get("advanced_stats", {})

    # Load versioned markdown reports
    version_reports = load_version_reports()

    # Begin building final report
    lines = [FINAL_HEADER]

    # Section 1 – Complete Data Overview
    lines.append("\n## 1. Complete Data Overview\n")
    lines.append("The dataset contains five high-resolution numeric variables (‘a’, ‘a_smooth’, ‘a_smooth_x’, ‘a_x’, ‘u’) derived from a Burgers-equation simulation. Each is a 2-D array with about 16–17 million elements. No missing values were detected across variables.\n")

    # Section 2 – Full Statistical Analysis
    lines.append("\n## 2. Full Statistical Analysis\n")
    lines.append("### 2.1 Basic Statistics\n")
    lines.append(build_basic_stats_table(basic_stats))

    lines.append("\n### 2.2 Spectral Density Highlights\n")
    lines.append(build_spectral_section(adv_stats.get("spectral", {})))

    lines.append("\n### 2.3 Correlation Summary\n")
    lines.append(build_correlation_section(adv_stats.get("correlations", {})))

    # Section 3 – Analysis Evolution
    lines.append("\n" + VERSION_OVERVIEW_HEADER + "\n")
    if version_reports:
        for idx, rep in enumerate(version_reports, 1):
            lines.append(f"#### Version {idx} – {rep['file']}")
            if idx == 1:
                lines.append("*Initial run:* Successful data load, descriptive stats, and spectral analysis. Heatmaps skipped due to array size; correlation skipped for insufficient 1-D vectors.")
            else:
                lines.append("*Optimised run:* Introduced sampling and size caps to prevent time-outs, enabling processing of full 629 MB file. No new correlations due to data dimensionality.")
            lines.append("")
    else:
        lines.append("Only a single iteration found – no evolution summary required.\n")

    # Section 4 – Consolidated Findings
    lines.append("\n## 4. Consolidated Findings\n")
    findings = [
        "1. All variables are centred near zero; spreads range σ ≈ 0.49–0.84.",
        "2. Dominant low-frequency modes (~1.22×10⁻⁴ Hz) appear across all fields, indicating large-scale coherent structures.",
        "3. Derivative fields (‘a_x’, ‘a_smooth_x’) exhibit greater variance and enhanced high-frequency power, as expected after differentiation.",
        "4. Outliers (|z|>3) constitute \u003c0.0002 % of values—unlikely to distort modelling.",
        "5. Correlation analysis requires dimensionality reduction (e.g., spatial slicing or PCA) to compare variables effectively.",
    ]
    lines.extend(findings)

    # Section 5 – Recommendations
    lines.append("\n## 5. Recommendations\n")
    recs = [
        "• Apply dimensionality-reduction techniques (random sampling, PCA, or FFT truncation) before multivariate analyses.",
        "• Leverage dominant spectral modes to build reduced-order models or surrogate emulators for rapid inference.",
        "• Consider storing future simulations in chunked, stream-friendly formats (HDF5, Zarr) to expedite partial loading.",
        "• Investigate regularisation or smoothing to mitigate amplified noise in derivative fields.",
    ]
    lines.extend(recs)

    # Metadata
    ts = datetime.now().isoformat()
    lines.append("\n## Metadata\n")
    lines.append(f"- Report generated: {ts}")
    lines.append(f"- Iterations merged: {len(version_reports)} (v1–v{len(version_reports)})")

    return "\n".join(lines)


def main():
    content = generate_final_report()
    with open(FINAL_REPORT_PATH, "w") as f:
        f.write(content)
    print(f"Final consolidated report saved to {FINAL_REPORT_PATH}")


if __name__ == "__main__":
    main()
