#!/usr/bin/env python
"""
quick_validation.py
-------------------
Lightweight validation of the generated consolidated report.
Checks:
1. File exists & readable
2. Non-empty content
3. Starts with expected title header
"""
import os
import sys

REPORT_PATH = "reports/final_consolidated_report.md"

result = {
    "File loadable": False,
    "Data integrity": "Fail",
    "Critical issues": [],
}

if not os.path.exists(REPORT_PATH):
    result["Critical issues"].append("File does not exist")
else:
    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        result["File loadable"] = True
        if len(content.strip()) == 0:
            result["Critical issues"].append("File is empty")
        elif not content.lstrip().startswith("# FINAL CONSOLIDATED DATA REPORT"):
            result["Critical issues"].append("Unexpected header – may be corrupted")
        else:
            result["Data integrity"] = "Pass"
    except Exception as e:
        result["Critical issues"].append(f"Read error: {e}")

print("VALIDATION REPORT:")
print(f"- File loaded: {'✓' if result['File loadable'] else '✗'}")
print(f"- Integrity: {result['Data integrity']}")
if result["Critical issues"]:
    print("- Issues: ")
    for issue in result["Critical issues"]:
        print(f"  • {issue}")
else:
    print("- Issues: None detected")
print(f"- Recommendation: {'PROCEED' if result['Data integrity']=='Pass' else 'FIX THESE ISSUES FIRST'}")
