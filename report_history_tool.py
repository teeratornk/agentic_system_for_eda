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
        md_path = reports_dir / "data_report.md"
        json_path = reports_dir / "data_report.json"
        
        result = {
            "status": "success",
            "markdown_exists": md_path.exists(),
            "json_exists": json_path.exists(),
            "markdown_content": None,
            "json_content": None
        }
        
        if md_path.exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                result["markdown_content"] = f.read()
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                result["json_content"] = json.load(f)
        
        if not md_path.exists() and not json_path.exists():
            result["message"] = "No reports found. Analysis may not be complete."
        else:
            result["message"] = "Reports loaded successfully"
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load reports: {str(e)}",
            "markdown_exists": False,
            "json_exists": False
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
