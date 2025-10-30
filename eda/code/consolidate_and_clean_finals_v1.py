# consolidate_and_clean_finals.py
"""
Consolidate ALL data_report_FINAL*.md files into a single authoritative
reports/data_report_FINAL.md and similarly consolidate any matching JSON
files.  After merging, older timestamped FINAL reports will be moved to a new
folder reports/old_finals/ for archival, leaving only:
    reports/data_report_FINAL.md
    reports/data_report_FINAL.json
in the main reports directory.

Usage (from eda directory):
    python code/consolidate_and_clean_finals.py
"""

import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path('reports')
ARCHIVE_DIR = REPORTS_DIR / 'old_finals'
ARCHIVE_DIR.mkdir(exist_ok=True, parents=True)

MD_BASE = REPORTS_DIR / 'data_report_FINAL.md'
JSON_BASE = REPORTS_DIR / 'data_report_FINAL.json'


def gather_files(ext):
    pattern = f'data_report_FINAL_*{ext}'
    return sorted(REPORTS_DIR.glob(pattern))


def merge_markdown(files):
    seen = set()
    merged_lines = []
    for fp in [MD_BASE] + files:
        if not fp.exists():
            continue
        for line in fp.read_text(encoding='utf-8').splitlines():
            if line.strip() not in seen:
                merged_lines.append(line)
                seen.add(line.strip())
    return "\n".join(merged_lines)


def merge_json(files):
    # We assume structure identical; we keep the most recent values.
    result = {}
    for fp in [JSON_BASE] + files:
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text())
            result = data  # overwrite with most recent
        except Exception:
            continue
    return result


def move_to_archive(paths):
    for p in paths:
        if p.exists():
            new_path = ARCHIVE_DIR / p.name
            p.rename(new_path)


def main():
    md_files = gather_files('.md')
    json_files = gather_files('.json')

    # Create merged content
    new_md = merge_markdown(md_files)
    new_json = merge_json(json_files)

    # Save authoritative versions
    MD_BASE.write_text(new_md, encoding='utf-8')
    JSON_BASE.write_text(json.dumps(new_json, indent=2), encoding='utf-8')

    # Archive old finals
    move_to_archive(md_files + json_files)

    print(f"Consolidated {len(md_files)+1} markdown and {len(json_files)+1} JSON FINAL reports.")
    print(f"Archived duplicates to {ARCHIVE_DIR}.")

if __name__ == '__main__':
    main()
