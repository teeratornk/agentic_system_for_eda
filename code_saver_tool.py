"""
Code Saver Tool for AutoGen Agents
Provides utilities for saving code files with proper organization and versioning.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class CodeSaver:
    """Utility class for saving code files with proper organization."""
    
    def __init__(self, base_dir: str = "eda"):
        """
        Initialize CodeSaver with base directory.
        
        Args:
            base_dir: Base directory for saving files (default: "eda")
        """
        self.base_dir = Path(base_dir)
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [
            self.base_dir,
            self.base_dir / "stats",
            self.base_dir / "reports", 
            self.base_dir / "figures",
            self.base_dir / "code"  # For versioned code files
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_code(self, 
                  code: str, 
                  filename: str, 
                  subfolder: Optional[str] = None,
                  version: bool = True) -> str:
        """
        Save code to a file with optional versioning.
        
        Args:
            code: The code content to save
            filename: Name of the file (e.g., "eda_analysis.py")
            subfolder: Optional subfolder within base_dir (e.g., "code")
            version: Whether to add version number if file exists
            
        Returns:
            Full path of the saved file
        """
        # Determine target directory
        if subfolder:
            target_dir = self.base_dir / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.base_dir
        
        # Handle versioning
        if version:
            base_name = Path(filename).stem
            extension = Path(filename).suffix
            
            # Find next available version
            version_num = 1
            while (target_dir / f"{base_name}_v{version_num}{extension}").exists():
                version_num += 1
            
            final_filename = f"{base_name}_v{version_num}{extension}"
        else:
            final_filename = filename
        
        # Save the file
        file_path = target_dir / final_filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return str(file_path)
    
    def save_json(self, 
                  data: Dict[Any, Any], 
                  filename: str,
                  subfolder: str = "stats",
                  pretty: bool = True) -> str:
        """
        Save data as JSON file.
        
        Args:
            data: Dictionary to save as JSON
            filename: Name of the JSON file
            subfolder: Subfolder to save in (default: "stats")
            pretty: Whether to format JSON nicely
            
        Returns:
            Full path of the saved file
        """
        target_dir = self.base_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        return str(file_path)
    
    def save_markdown(self,
                     content: str,
                     filename: str,
                     subfolder: str = "reports") -> str:
        """
        Save markdown content to file.
        
        Args:
            content: Markdown content to save
            filename: Name of the markdown file
            subfolder: Subfolder to save in (default: "reports")
            
        Returns:
            Full path of the saved file
        """
        target_dir = self.base_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)
    
    def get_next_version(self, base_filename: str, subfolder: Optional[str] = None) -> str:
        """
        Get the next version number for a file.
        
        Args:
            base_filename: Base name without version (e.g., "eda_analysis.py")
            subfolder: Optional subfolder to check in
            
        Returns:
            Next versioned filename (e.g., "eda_analysis_v3.py")
        """
        target_dir = self.base_dir / subfolder if subfolder else self.base_dir
        
        base_name = Path(base_filename).stem
        extension = Path(base_filename).suffix
        
        version_num = 1
        while (target_dir / f"{base_name}_v{version_num}{extension}").exists():
            version_num += 1
        
        return f"{base_name}_v{version_num}{extension}"
    
    def list_files(self, subfolder: Optional[str] = None, pattern: str = "*") -> list:
        """
        List files in a directory.
        
        Args:
            subfolder: Subfolder to list files from
            pattern: Glob pattern for filtering files
            
        Returns:
            List of file paths
        """
        target_dir = self.base_dir / subfolder if subfolder else self.base_dir
        
        if not target_dir.exists():
            return []
        
        return [str(f) for f in target_dir.glob(pattern)]
    
    def file_exists(self, filename: str, subfolder: Optional[str] = None) -> bool:
        """
        Check if a file exists.
        
        Args:
            filename: Name of the file
            subfolder: Optional subfolder
            
        Returns:
            True if file exists, False otherwise
        """
        target_dir = self.base_dir / subfolder if subfolder else self.base_dir
        file_path = target_dir / filename
        return file_path.exists()


# Function wrapper for easy agent use
def save_agent_code(code: str, 
                   filename: str, 
                   subfolder: Optional[str] = None,
                   base_dir: str = "eda") -> Dict[str, str]:
    """
    Simple function for agents to save code.
    
    Args:
        code: Code content to save
        filename: Desired filename
        subfolder: Optional subfolder
        base_dir: Base directory (default: "eda")
        
    Returns:
        Dictionary with status and file path
    """
    try:
        saver = CodeSaver(base_dir)
        file_path = saver.save_code(code, filename, subfolder)
        return {
            "status": "success",
            "message": f"Code saved to {file_path}",
            "path": file_path
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save code: {str(e)}",
            "path": None
        }


if __name__ == "__main__":
    # Example usage
    saver = CodeSaver("eda")
    
    # Save analysis code with auto-versioning
    sample_code = """
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('data.csv')
print(data.describe())
"""
    
    path = saver.save_code(sample_code, "analysis.py", "code")
    print(f"Saved code to: {path}")
    
    # Save JSON statistics
    stats = {
        "mean": 10.5,
        "std": 2.3,
        "count": 1000
    }
    json_path = saver.save_json(stats, "sample_stats.json")
    print(f"Saved JSON to: {json_path}")
    
    # List files
    files = saver.list_files("code", "*.py")
    print(f"Python files in code folder: {files}")
