import sys
import json
from pathlib import Path
import numpy as np
import scipy.io as sio

def quick_validate(file_path: str):
    report = {
        "file_loadable": False,
        "data_integrity": "Fail",
        "critical_issues": [],
    }

    p = Path(file_path)
    if not p.exists():
        report["critical_issues"].append("File does not exist")
        return report
    if not p.is_file():
        report["critical_issues"].append("Path is not a file")
        return report

    # Try loading .mat file
    try:
        data = sio.loadmat(file_path)
        report["file_loadable"] = True
    except Exception as e:
        report["critical_issues"].append(f"Loading error: {e}")
        return report

    # Basic structure checks
    if not isinstance(data, dict):
        report["critical_issues"].append("Loaded data is not a dictionary")
        return report

    # Remove MATLAB header keys
    keys = [k for k in data.keys() if not k.startswith("__")]
    if not keys:
        report["critical_issues"].append("No user variables found in .mat file")
        return report

    for k in keys:
        obj = data[k]
        if obj is None:
            report["critical_issues"].append(f"Variable '{k}' is None")
        elif isinstance(obj, np.ndarray):
            if obj.size == 0:
                report["critical_issues"].append(f"Variable '{k}' is empty array")
            elif np.isnan(obj).all():
                report["critical_issues"].append(f"Variable '{k}' is all NaN")
        # Add other quick checks if needed

    if not report["critical_issues"]:
        report["data_integrity"] = "Pass"

    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_validation.py <path_to_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    report = quick_validate(file_path)
    print("VALIDATION REPORT:\n", json.dumps(report, indent=2))
