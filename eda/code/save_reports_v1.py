#!/usr/bin/env python
"""
save_reports.py
===============
Generate an iterative versioned data report (v1, v2, …) based on
stats/statistics.json produced by the EDA scripts. This script should be run
from the `eda` folder after the stats JSON exists.

Usage:
    python code/save_reports.py

It will:
1. Read stats/statistics.json.
2. Discover existing versioned reports in reports/ matching pattern
   data_report_v*.md.
3. Determine the next version number (starting at 1).
4. Build a markdown report containing:
   • Executive Summary (auto-generated outline)
   • Basic statistics table
   • Advanced analysis summaries (spectral / correlations)
5. Save the report as reports/data_report_v{N}.md.
"""

import json
import glob
import os
from datetime import datetime

REPORT_DIR = "reports"
STATS_FILE = os.path.join("stats", "statistics.json")

TEMPLATE_HEADER = """# DATA REPORT – Version {version}
*Generated*: {timestamp}
*Source statistics*: stats/statistics.json
---
"""


def next_version():
    existing = glob.glob(os.path.join(REPORT_DIR, "data_report_v*.md"))
    if not existing:
        return 1
    nums = [int(os.path.basename(p).split("_v")[-1].split(".")[0]) for p in existing]
    return max(nums) + 1


def generate_report_content(stats_json: dict, version: int) -> str:
    ts = datetime.now().isoformat()
    lines = [TEMPLATE_HEADER.format(version=version, timestamp=ts)]

    # Executive Summary (very brief, auto)
    lines.append("## Executive Summary\n")
    lines.append("This report summarises the descriptive statistics and advanced analyses generated in the latest EDA run.\n")

    # Section 1 – Basic statistics table
    lines.append("## 1. Basic Statistics\n")
    lines.append("| Variable | Min | Max | Mean | Std | Median | Q25 | Q75 | Outliers (z>3) | Missing | Total |\n")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for var, stats in stats_json["basic_stats"].items():
        lines.append(
            f"| {var} | {stats['min']:.4g} | {stats['max']:.4g} | {stats['mean']:.4g} | {stats['std']:.4g} | {stats['median']:.4g} | {stats['q25']:.4g} | {stats['q75']:.4g} | {stats['outliers_z3']} | {stats['missing']} | {stats['total']} |\n"
        )

    # Section 2 – Spectral summaries
    spec = stats_json["advanced_stats"].get("spectral", {})
    if spec:
        lines.append("\n## 2. Spectral Analysis (Top Frequencies)\n")
        for var, s in spec.items():
            lines.append(f"### {var}\n")
            for f, p in zip(s["top_frequencies"], s["top_powers"]):
                lines.append(f"- Frequency: {f:.4g}, Power: {p:.4g}\n")
    else:
        lines.append("\n## 2. Spectral Analysis\nNo spectral data available.\n")

    # Section 3 – Correlations
    corr = stats_json["advanced_stats"].get("correlations", {})
    if corr:
        lines.append("\n## 3. Correlation Analysis (Pearson)\n")
        lines.append("| Pair | r | p-value |\n|---|---|---|\n")
        for pair, vals in corr.items():
            lines.append(f"| {pair} | {vals['pearson_r']:.4g} | {vals['p_value']:.4g} |\n")
    else:
        lines.append("\n## 3. Correlation Analysis\nNo correlations calculated.\n")

    # Close
    lines.append("\n---\nEnd of report.\n")
    return "\n".join(lines)


def main():
    if not os.path.exists(STATS_FILE):
        raise FileNotFoundError("statistics.json not found. Run EDA first.")

    with open(STATS_FILE) as f:
        stats_json = json.load(f)

    v = next_version()
    content = generate_report_content(stats_json, v)

    out_path = os.path.join(REPORT_DIR, f"data_report_v{v}.md")
    with open(out_path, "w") as f:
        f.write(content)
    print(f"Saved iterative report: {out_path}")


if __name__ == "__main__":
    main()
