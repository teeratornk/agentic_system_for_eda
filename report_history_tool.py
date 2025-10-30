"""
Report History Tool for AutoGen Agents
Provides utilities for saving and loading historical reports for learning.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

class ReportHistory:
    """Utility class for managing report history and learning from past analyses."""
    
    def __init__(self, history_dir: str = "eda/history"):
        """
        Initialize ReportHistory with history directory.
        
        Args:
            history_dir: Directory for storing historical reports
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.history_dir / "index.json"
        self.load_index()
    
    def load_index(self):
        """Load or create the history index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {"reports": [], "patterns": {}}
    
    def save_index(self):
        """Save the history index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def generate_report_id(self, file_path: str) -> str:
        """Generate a unique ID for a report based on file and timestamp."""
        timestamp = datetime.now().isoformat()
        content = f"{file_path}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def save_report(self, 
                   file_path: str,
                   data_summary: Dict[str, Any],
                   statistics: Dict[str, Any],
                   report_content: str,
                   insights: Optional[List[str]] = None) -> str:
        """
        Save a report to history for future learning.
        
        Args:
            file_path: Path of the analyzed file
            data_summary: Summary of data structure and types
            statistics: Statistical findings
            report_content: The markdown report content
            insights: Key insights discovered
            
        Returns:
            Report ID for reference
        """
        report_id = self.generate_report_id(file_path)
        timestamp = datetime.now().isoformat()
        
        # Create report record
        report_record = {
            "id": report_id,
            "timestamp": timestamp,
            "file_path": file_path,
            "file_type": Path(file_path).suffix,
            "data_summary": data_summary,
            "statistics": statistics,
            "insights": insights or [],
            "report_file": f"{report_id}_report.md"
        }
        
        # Save markdown report
        report_path = self.history_dir / f"{report_id}_report.md"
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        # Save JSON metadata
        metadata_path = self.history_dir / f"{report_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(report_record, f, indent=2)
        
        # Update index
        self.index["reports"].append(report_record)
        
        # Update patterns (for learning)
        file_type = report_record["file_type"]
        if file_type not in self.index["patterns"]:
            self.index["patterns"][file_type] = []
        
        # Extract patterns from this analysis
        patterns = {
            "data_shape": data_summary.get("shape", "unknown"),
            "has_missing": statistics.get("has_missing_values", False),
            "common_analyses": list(statistics.keys()),
            "insights_count": len(insights or [])
        }
        self.index["patterns"][file_type].append(patterns)
        
        self.save_index()
        return report_id
    
    def find_similar_reports(self, 
                            file_path: str,
                            limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find similar past reports based on file type and characteristics.
        
        Args:
            file_path: Path of the file to analyze
            limit: Maximum number of similar reports to return
            
        Returns:
            List of similar report records
        """
        file_type = Path(file_path).suffix
        similar_reports = []
        
        # Filter by file type first
        for report in self.index["reports"]:
            if report["file_type"] == file_type:
                similar_reports.append(report)
        
        # Sort by recency and limit
        similar_reports.sort(key=lambda x: x["timestamp"], reverse=True)
        return similar_reports[:limit]
    
    def get_common_patterns(self, file_type: str) -> Dict[str, Any]:
        """
        Get common patterns for a file type from history.
        
        Args:
            file_type: File extension (e.g., '.mat', '.csv')
            
        Returns:
            Dictionary of common patterns and approaches
        """
        if file_type not in self.index["patterns"]:
            return {}
        
        patterns = self.index["patterns"][file_type]
        if not patterns:
            return {}
        
        # Aggregate common analyses
        all_analyses = []
        for p in patterns:
            all_analyses.extend(p.get("common_analyses", []))
        
        # Count frequency
        analysis_freq = {}
        for analysis in all_analyses:
            analysis_freq[analysis] = analysis_freq.get(analysis, 0) + 1
        
        # Sort by frequency
        common_analyses = sorted(analysis_freq.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "file_type": file_type,
            "total_reports": len(patterns),
            "common_analyses": [a[0] for a in common_analyses[:10]],
            "typical_has_missing": sum(p.get("has_missing", False) for p in patterns) > len(patterns) / 2
        }
    
    def get_insights_summary(self, limit: int = 10) -> List[str]:
        """
        Get a summary of recent insights across all reports.
        
        Args:
            limit: Maximum number of insights to return
            
        Returns:
            List of recent insights
        """
        all_insights = []
        
        # Sort reports by timestamp
        sorted_reports = sorted(self.index["reports"], 
                              key=lambda x: x["timestamp"], 
                              reverse=True)
        
        # Collect insights
        for report in sorted_reports[:5]:  # Last 5 reports
            all_insights.extend(report.get("insights", []))
        
        return all_insights[:limit]


# Function wrappers for agent use
def save_analysis_to_history(file_path: str,
                            data_summary: Dict[str, Any],
                            statistics: Dict[str, Any],
                            report_content: str,
                            insights: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Save analysis results to history for future learning.
    
    Args:
        file_path: Path of analyzed file
        data_summary: Data structure summary
        statistics: Statistical findings
        report_content: Markdown report
        insights: Key insights
        
    Returns:
        Status dictionary
    """
    try:
        history = ReportHistory()
        report_id = history.save_report(
            file_path, data_summary, statistics, 
            report_content, insights
        )
        return {
            "status": "success",
            "message": f"Report saved to history with ID: {report_id}",
            "report_id": report_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save to history: {str(e)}",
            "report_id": None
        }

def load_similar_analyses(file_path: str, limit: int = 3) -> Dict[str, Any]:
    """
    Load similar past analyses for learning.
    
    Args:
        file_path: Path of file to analyze
        limit: Maximum similar reports
        
    Returns:
        Dictionary with similar reports and patterns
    """
    try:
        history = ReportHistory()
        similar = history.find_similar_reports(file_path, limit)
        file_type = Path(file_path).suffix
        patterns = history.get_common_patterns(file_type)
        
        return {
            "status": "success",
            "similar_reports": similar,
            "common_patterns": patterns,
            "message": f"Found {len(similar)} similar analyses"
        }
    except Exception as e:
        return {
            "status": "error",
            "similar_reports": [],
            "common_patterns": {},
            "message": f"Failed to load history: {str(e)}"
        }

def get_historical_insights(limit: int = 10) -> Dict[str, Any]:
    """
    Get insights from historical analyses.
    
    Args:
        limit: Maximum insights to return
        
    Returns:
        Dictionary with historical insights
    """
    try:
        history = ReportHistory()
        insights = history.get_insights_summary(limit)
        
        return {
            "status": "success",
            "insights": insights,
            "count": len(insights),
            "message": "Historical insights retrieved"
        }
    except Exception as e:
        return {
            "status": "error",
            "insights": [],
            "count": 0,
            "message": f"Failed to get insights: {str(e)}"
        }


def load_current_reports() -> Dict[str, Any]:
    """
    Load the current analysis reports for review.
    
    Returns:
        Dictionary with report contents
    """
    try:
        reports_dir = Path("eda/reports")
        
        # Check for all report versions
        all_reports = list(reports_dir.glob("data_report*.md")) if reports_dir.exists() else []
        report_files = {
            "versioned": [],
            "final": None,
            "latest": None
        }
        
        for report in all_reports:
            name = report.name
            if "FINAL" in name:
                report_files["final"] = name
            elif "latest" in name:
                report_files["latest"] = name
            elif "_v" in name:
                report_files["versioned"].append(name)
        
        result = {
            "status": "success",
            "reports_found": len(all_reports),
            "versioned_reports": report_files["versioned"],
            "final_report_exists": report_files["final"] is not None,
            "final_report_name": report_files["final"],
            "latest_report_name": report_files["latest"],
            "final_content": None,
            "message": ""
        }
        
        # Load final report content if it exists
        if report_files["final"]:
            final_path = reports_dir / report_files["final"]
            with open(final_path, 'r', encoding='utf-8') as f:
                result["final_content"] = f.read()[:1000] + "..." if len(f.read()) > 1000 else f.read()
            result["message"] = f"Final report found: {report_files['final']}"
        elif report_files["versioned"]:
            result["message"] = f"Found {len(report_files['versioned'])} versioned reports, but no FINAL report"
        else:
            result["message"] = "No reports found. Analysis may not be complete."
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load reports: {str(e)}",
            "reports_found": 0,
            "final_report_exists": False
        }

def check_analysis_files() -> Dict[str, Any]:
    """
    Check what analysis files exist in the EDA directories.
    
    Returns:
        Dictionary with file existence information
    """
    try:
        eda_base = Path("eda")
        
        # Check statistics
        stats_files = list((eda_base / "stats").glob("*.json")) if (eda_base / "stats").exists() else []
        
        # Check figures
        figure_files = []
        if (eda_base / "figures").exists():
            for ext in ["*.png", "*.jpg", "*.pdf", "*.svg"]:
                figure_files.extend((eda_base / "figures").glob(ext))
        
        # Check reports
        report_files = list((eda_base / "reports").glob("*.md")) if (eda_base / "reports").exists() else []
        json_reports = list((eda_base / "reports").glob("*.json")) if (eda_base / "reports").exists() else []
        
        # Check for specific key files
        statistics_exists = (eda_base / "stats" / "statistics.json").exists()
        final_report_exists = (eda_base / "reports" / "data_report_FINAL.md").exists()
        
        return {
            "status": "success",
            "statistics": {
                "exists": statistics_exists,
                "path": "stats/statistics.json" if statistics_exists else None,
                "other_stats": [f.name for f in stats_files]
            },
            "figures": {
                "count": len(figure_files),
                "files": [f.name for f in figure_files]
            },
            "reports": {
                "markdown_count": len(report_files),
                "json_count": len(json_reports),
                "final_exists": final_report_exists,
                "markdown_files": [f.name for f in report_files],
                "json_files": [f.name for f in json_reports]
            },
            "summary": {
                "analysis_complete": statistics_exists,
                "figures_generated": len(figure_files) > 0,
                "reports_created": len(report_files) > 0,
                "final_report_ready": final_report_exists
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check files: {str(e)}",
            "summary": {
                "analysis_complete": False,
                "figures_generated": False,
                "reports_created": False,
                "final_report_ready": False
            }
        }

def verify_final_report() -> Dict[str, Any]:
    """
    Specifically verify that the final report exists and is valid.
    Checks for both report_for_user.md (preferred) and data_report_FINAL.md (legacy).
    
    Returns:
        Dictionary with final report verification
    """
    try:
        reports_dir = Path("eda/reports")
        
        # Primary final report for user
        user_report_path = reports_dir / "report_for_user.md"
        user_json_path = reports_dir / "report_for_user.json"
        
        # Legacy final report naming
        final_path = reports_dir / "data_report_FINAL.md"
        final_json_path = reports_dir / "data_report_FINAL.json"
        
        # Check for timestamped versions
        timestamped_user = list(reports_dir.glob("report_for_user_*.md")) if reports_dir.exists() else []
        timestamped_finals = list(reports_dir.glob("data_report_FINAL_*.md")) if reports_dir.exists() else []
        
        result = {
            "status": "success",
            "user_report_exists": user_report_path.exists(),
            "user_json_exists": user_json_path.exists(),
            "final_md_exists": final_path.exists() or user_report_path.exists(),
            "final_json_exists": final_json_path.exists() or user_json_path.exists(),
            "user_report_path": str(user_report_path) if user_report_path.exists() else None,
            "legacy_final_path": str(final_path) if final_path.exists() else None,
            "timestamped_user_count": len(timestamped_user),
            "timestamped_finals_count": len(timestamped_finals),
            "timestamped_user": [f.name for f in timestamped_user],
            "timestamped_finals": [f.name for f in timestamped_finals],
            "file_size": None,
            "preview": None,
            "message": "",
            "needs_consolidation": False
        }
        
        # Determine which report to use
        primary_report = None
        if user_report_path.exists():
            primary_report = user_report_path
            report_type = "user report"
        elif final_path.exists():
            primary_report = final_path
            report_type = "legacy final report"
        
        # Check if we have multiple reports that need consolidation
        total_timestamped = len(timestamped_user) + len(timestamped_finals)
        if total_timestamped > 1:
            result["needs_consolidation"] = True
            result["message"] = f"Found {total_timestamped} timestamped reports. Consolidation into report_for_user.md recommended."
            
            # Get the most recent for preview
            all_timestamped = timestamped_user + timestamped_finals
            most_recent = sorted(all_timestamped, key=lambda x: x.stat().st_mtime)[-1]
            with open(most_recent, 'r', encoding='utf-8') as f:
                content = f.read()
                result["preview"] = content[:500] + "..." if len(content) > 500 else content
            result["message"] += f" Most recent: {most_recent.name}"
            
        elif primary_report:
            file_size = primary_report.stat().st_size
            result["file_size"] = f"{file_size / 1024:.2f} KB"
            
            # Get preview
            with open(primary_report, 'r', encoding='utf-8') as f:
                content = f.read()
                result["preview"] = content[:500] + "..." if len(content) > 500 else content
            
            if user_report_path.exists():
                result["message"] = "Final user report (report_for_user.md) verified and ready"
            else:
                result["message"] = f"Found {report_type}. Consider renaming to report_for_user.md for clarity"
                
        elif total_timestamped == 1:
            # Only one timestamped report exists
            single_report = (timestamped_user + timestamped_finals)[0]
            result["message"] = f"Found timestamped report: {single_report.name}. Should be saved as report_for_user.md"
        else:
            result["message"] = "Final user report NOT found. Please create report_for_user.md"
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "user_report_exists": False,
            "final_md_exists": False,
            "final_json_exists": False,
            "needs_consolidation": False,
            "message": f"Failed to verify final report: {str(e)}"
        }

def consolidate_final_reports() -> Dict[str, Any]:
    """
    Consolidate multiple FINAL reports into one.
    
    Returns:
        Dictionary with consolidation status
    """
    try:
        reports_dir = Path("eda/reports")
        
        # Find all FINAL reports
        main_final = reports_dir / "data_report_FINAL.md"
        timestamped_finals = list(reports_dir.glob("data_report_FINAL_*.md"))
        
        if not timestamped_finals and main_final.exists():
            return {
                "status": "success",
                "message": "Only one FINAL report exists, no consolidation needed",
                "consolidated": False
            }
        
        all_finals = []
        if main_final.exists():
            all_finals.append(main_final)
        all_finals.extend(timestamped_finals)
        
        if len(all_finals) <= 1:
            return {
                "status": "info",
                "message": f"Found {len(all_finals)} final report(s), no consolidation needed",
                "consolidated": False
            }
        
        # Sort by modification time
        all_finals.sort(key=lambda x: x.stat().st_mtime)
        
        # Collect unique content sections from all reports
        sections = {
            "headers": [],
            "summaries": [],
            "statistics": [],
            "analyses": [],
            "findings": [],
            "recommendations": []
        }
        
        report_info = []
        for report_path in all_finals:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                report_info.append({
                    "name": report_path.name,
                    "modified": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat(),
                    "size": report_path.stat().st_size,
                    "preview": content[:200]
                })
        
        return {
            "status": "success",
            "message": f"Found {len(all_finals)} FINAL reports that could be consolidated",
            "reports_to_consolidate": [r["name"] for r in report_info],
            "report_details": report_info,
            "consolidated": False,
            "action_needed": "Please create a new consolidated FINAL report combining insights from all versions"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check for consolidation: {str(e)}",
            "consolidated": False
        }


if __name__ == "__main__":
    # Example usage
    history = ReportHistory()
    
    # Save a sample report
    sample_stats = {
        "mean": 10.5,
        "std": 2.3,
        "has_missing_values": False
    }
    
    sample_summary = {
        "shape": (1000, 50),
        "dtypes": ["float64"]
    }
    
    report_id = history.save_report(
        "data/sample.mat",
        sample_summary,
        sample_stats,
        "# Sample Report\nThis is a test.",
        ["Pattern detected", "Outliers found"]
    )
    
    print(f"Saved report: {report_id}")
    
    # Find similar
    similar = history.find_similar_reports("data/another.mat")
    print(f"Similar reports: {similar}")
