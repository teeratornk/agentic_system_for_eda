# consolidate_finals.py
"""Merge multiple timestamped data_report_FINAL_*.md files into a single definitive
FINAL consolidated report, removing duplicates and preserving all unique
content and figure references.

Usage:
    python code/consolidate_finals.py
"""

import re
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path('reports')


def main():
    finals = sorted(REPORTS_DIR.glob('data_report_FINAL_*.md'))
    base_final = REPORTS_DIR / 'data_report_FINAL.md'
    if not finals:
        print('No timestamped FINAL reports to consolidate.')
        return

    # Read all existing FINAL contents including base file
    contents = []
    seen_lines = set()
    for p in [base_final] + finals:
        if p.exists():
            text = p.read_text(encoding='utf-8').splitlines()
            contents.append(text)

    # Simple line-level merge while preserving order and avoiding duplicates
    merged_lines = []
    for lines in contents:
        for line in lines:
            key = line.strip()
            if key not in seen_lines:
                merged_lines.append(line)
                seen_lines.add(key)

    merged_text = "\n".join(merged_lines)

    # Overwrite main FINAL
    base_final.write_text(merged_text, encoding='utf-8')

    # Archive consolidated copy
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    (REPORTS_DIR / f'data_report_FINAL_{ts}.md').write_text(merged_text, encoding='utf-8')

    print(f'Consolidated {len(finals)+1} FINAL reports into {base_final}.')

if __name__ == '__main__':
    main()
