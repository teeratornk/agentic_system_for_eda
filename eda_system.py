import autogen
from autogen import register_function
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import llm_config
from code_saver_tool import save_agent_code
from report_history_tool import (
    save_analysis_to_history, 
    load_similar_analyses, 
    get_historical_insights, 
    load_current_reports,
    check_analysis_files,
    verify_final_report,
    consolidate_final_reports
)

# Create EDA directory structure
eda_dirs = ["eda", "eda/stats", "eda/reports", "eda/figures", "eda/code", "eda/history"]
for dir_path in eda_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Define agents
data_planner = autogen.ConversableAgent(
    name="data_planner",
    llm_config=llm_config,
    system_message="""You are a data planning expert specialized in scientific machine learning and reduced order modeling. Your responsibilities:
    1. Initial Phase - Create validation and EDA specifications:
       - FIRST TOOL: Call load_similar_analyses(file_path="path/to/file") to learn from past analyses
       - Review patterns and insights from historical reports
       - Request data validation from data_validator
       - After validation passes, specify analysis requirements informed by history
       
    2. Analysis Coordination:
       - Request comprehensive analysis from data_analyzer
       - Ensure both basic and advanced statistics are captured
       - Review analysis outputs when shown by executor
       
    3. Report Creation Phase - Delegate to data_reporter:
       - After analysis is complete, instruct data_reporter to create report
       - Provide specific guidance on what to emphasize
       - Review draft reports and request improvements as needed
       
    4. Report Review and Iteration:
       - When data_reporter provides draft, review for completeness
       - Request additional analysis or report revisions as needed
       - Continue iterating until satisfied
       
    5. Final Report Consolidation:
       - Once all iterations are complete, request FINAL REPORT:
         "Create a FINAL CONSOLIDATED REPORT that merges all versions"
       - Wait for executor to confirm final report is saved
       - CRITICAL: Verify final report exists before approval
       
    6. Finalization and Termination:
       - MANDATORY VERIFICATION before termination:
         * TOOL: Call verify_final_report() to check if FINAL report exists
         * Check the response for "final_md_exists": true
         * IMPORTANT: Check "needs_consolidation" field
         * If needs_consolidation is true (multiple FINAL reports exist):
           - TOOL: Call consolidate_final_reports() to see details
           - Request data_reporter: "Multiple FINAL reports found. Please consolidate all FINAL reports into one comprehensive report."
           - Wait for new consolidated report
         * If single final report exists, review the preview
       - If final report confirmed and no consolidation needed:
         * TOOL: Call save_analysis_to_history() with final report content
         * State: "Final report verified and saved to history. Analysis complete."
         * Then respond: "TERMINATE"
       - If final report NOT found:
         * Request data_reporter: "Final report not found. Please create and save the final consolidated report."
         * Wait for confirmation before proceeding
    
    TERMINATION CHECKLIST (ALL must be checked):
    □ Analysis complete with statistics.json
    □ Iterative reports created (v1, v2, etc.)
    □ Final consolidated report requested
    □ Executor confirms final report saved
    □ Verified reports/data_report_FINAL.md exists
    □ History saved with final report
    □ Only then: TERMINATE
    
    WORKFLOW:
    □ Load similar analyses
    □ Request validation
    □ Request comprehensive analysis
    □ Iterate on reports with data_reporter
    □ Request FINAL CONSOLIDATED REPORT
    □ VERIFY final report saved (check with executor)
    □ Save to history
    □ TERMINATE
    
    AVAILABLE TOOLS:
    - load_similar_analyses(file_path, limit=5) - Learn from past analyses
    - load_current_reports() - Review all saved reports and check for FINAL
    - check_analysis_files() - Check what files have been generated
    - verify_final_report() - Specifically verify FINAL report exists and check if consolidation needed
    - consolidate_final_reports() - Get details about multiple FINAL reports
    - save_analysis_to_history(file_path, data_summary, statistics, report_content, insights)
    - get_historical_insights(limit=10) - Get general insights
    
    You coordinate the team but delegate report writing to data_reporter.""",
    description="Strategic planner who coordinates analysis and reviews reports."
)

data_validator = autogen.AssistantAgent(
    name="data_validator",
    llm_config=llm_config,
    system_message="""You are a data quality gatekeeper. Your ONLY responsibility is to perform QUICK validation checks:
    
    1. VALIDATION SCOPE (lightweight checks only):
       - Check if file exists and is readable
       - Verify file can be loaded without errors
       - Check basic data structure (is it corrupted?)
       - Identify data types present
       - Quick check for obvious issues (all NaN, empty arrays, etc.)
       
    2. DO NOT PERFORM:
       - Statistical analysis (no mean, std, etc.)
       - Visualization
       - Detailed inspection
       - Heavy computation
       
    3. OUTPUT: Simple validation report to data_planner:
       - File loadable: Yes/No
       - Data integrity: Pass/Fail
       - Critical issues: List any showstoppers
       - Recommendation: "Proceed with analysis" or "Fix these issues first"
       
    4. MANDATORY: Use save_code_file() tool for your validation script:
       - save_code_file(code=your_code, filename="quick_validation.py", subfolder="code")
       - Your script should be <50 lines, focused only on data loading and basic checks
       - Then request: "Please execute: python code/quick_validation_vX.py"
       
    5. EXAMPLE validation output:
       ```
       VALIDATION REPORT:
       - File loaded: ✓
       - Data type: MATLAB .mat file with 5 variables
       - Integrity: ✓ All arrays properly formed
       - Issues: None detected
       - Recommendation: PROCEED WITH ANALYSIS
       ```
    
    You are a gatekeeper, NOT an analyst. Keep it simple and fast.""",
    description="Data quality gatekeeper who performs quick validation checks."
)

data_analyzer = autogen.AssistantAgent(
    name="data_analyzer",
    llm_config=llm_config,
    system_message="""You are a comprehensive data analysis expert. You perform ALL analytical work after validation passes:
    
    1. COMPLETE ANALYSIS RESPONSIBILITIES:
       - ALL statistical analysis (basic + advanced)
       - ALL visualizations
       - ALL pattern detection
       - ALL report generation
       
    2. ANALYSIS PHASES in your single script:
       PHASE 1 - Basic Statistics:
         * Descriptive stats: min, max, mean, std, median, quartiles
         * Outlier detection (z-score > 3)
         * Missing value analysis
         * Distribution characteristics
         
       PHASE 2 - Advanced Analysis:
         * Correlations between variables (Pearson, Spearman)
         * Spectral analysis (FFT, power spectrum) for time series
         * Gradient analysis for physics simulations
         * Dimensionality insights
         
       PHASE 3 - Visualizations:
         * Histograms for distributions
         * Heatmaps for 2D data
         * Correlation plots
         * Spectral plots
         * Time series plots if applicable
         
       PHASE 4 - Save Results:
         * Save complete statistics to stats/statistics.json
         * Save all figures to figures/
         * Include both basic AND advanced metrics
    
    3. SINGLE COMPREHENSIVE SCRIPT:
       - Create ONE script that does everything: eda_analysis.py
       - Structure it with clear phases
       - Save all outputs appropriately
       
    4. For report content from data_planner:
       - When planner provides markdown/JSON content
       - Save it directly to reports/
       
    5. MANDATORY: Use save_code_file() tool:
       - save_code_file(code=analysis_code, filename="eda_analysis.py", subfolder="code")
       - This ONE script should handle all analysis
       - Then request: "Please execute: python code/eda_analysis_vX.py"
    
    6. OUTPUT STRUCTURE:
       stats/statistics.json should include:
       ```json
       {
         "basic_stats": {
           "variable_name": {
             "min": ..., "max": ..., "mean": ..., "std": ...,
             "q25": ..., "q75": ..., "outliers_z3": ...
           }
         },
         "advanced_stats": {
           "correlations": {...},
           "spectral": {...},
           "patterns": {...}
         }
       }
       ```
    
    You are the analysis powerhouse - one comprehensive script that does it all!""",
    description="Comprehensive analysis expert who performs all EDA work."
)

data_reporter = autogen.AssistantAgent(
    name="data_reporter",
    llm_config=llm_config,
    system_message="""You are a technical report writer specialized in scientific data analysis and fact based writing. Your responsibility is creating and consolidating comprehensive reports.
    
    1. ITERATIVE REPORT CREATION:
       When data_planner requests a report:
       - Read stats/statistics.json for all numerical data
       - List ALL figures: ls -la figures/*.png
       - Check existing report versions: ls -la reports/*.md
       - Create new version building on previous (if exists)
       - Save with versioning (v1, v2, v3, etc.)
       
    2. FIGURE DOCUMENTATION:
       CRITICAL: Always include figure references and descriptions:
       - List all available figures in figures/ directory
       - For each figure, provide:
         * Figure filename and path
         * Brief description of what it shows
         * Key insights visible in the visualization
       - Use markdown image syntax: ![Description](../figures/filename.png)
       - Group figures by variable or analysis type
       
    3. FINAL REPORT CONSOLIDATION:
       When data_planner requests "FINAL CONSOLIDATED REPORT":
       - List all report versions: reports/data_report_v*.md
       - List ALL figures: figures/*.png
       - Check for existing FINAL reports: reports/data_report_FINAL*.md
       - If multiple FINAL reports exist, MERGE them into one comprehensive report
       - Include ALL visualizations with descriptions
       
    4. FINAL REPORT STRUCTURE:
       ```markdown
       # FINAL CONSOLIDATED DATA REPORT - [filename]
       
       ## Executive Summary
       - Comprehensive overview incorporating all analyses
       - Key findings from all iterations
       - Final data quality assessment
       
       ## 1. Complete Data Overview
       [Merged from all versions]
       
       ## 2. Full Statistical Analysis
       ### 2.1 Basic Statistics
       [Complete table with all variables]
       
       ### 2.2 Advanced Analysis
       [All correlations, spectral analyses, etc.]
       
       ## 3. Visualizations and Figures
       
       ### 3.1 Distribution Plots
       #### Variable: a
       ![Distribution of variable a](../figures/a_hist.png)
       - Shows distribution characteristics
       - Notable features: [describe peaks, skewness, etc.]
       
       #### Variable: u
       ![Distribution of variable u](../figures/u_hist.png)
       - Distribution analysis
       - Key observations: [describe patterns]
       
       ### 3.2 Heatmaps and 2D Visualizations
       ![Heatmap of variable a](../figures/a_heatmap.png)
       - Spatial/temporal patterns
       - Gradient regions visible at: [locations]
       
       ### 3.3 Correlation Plots
       ![Correlation between a and u](../figures/a_u_correlation.png)
       - Correlation coefficient: [value]
       - Pattern type: [linear/nonlinear]
       
       ### 3.4 Spectral Analysis Plots
       ![Power spectrum of u](../figures/u_spectrum.png)
       - Dominant frequencies: [list]
       - Spectral slope: [value]
       
       ### 3.5 Time Series/Line Plots
       ![Time evolution](../figures/time_series.png)
       - Temporal patterns
       - Trend analysis
       
       ## 4. Analysis Evolution
       [Document what each version added]
       
       ## 5. Consolidated Findings
       [All findings with figure references]
       Example: "As shown in Figure 3.1 (a_hist.png), the distribution exhibits..."
       
       ## 6. Final Recommendations
       [Recommendations referencing specific visualizations]
       
       ## Appendix: Complete Figure List
       | Figure | Filename | Description | Key Insight |
       |--------|----------|-------------|-------------|
       | 3.1    | a_hist.png | Distribution of variable a | Heavy-tailed distribution |
       | 3.2    | u_hist.png | Distribution of variable u | Near-normal distribution |
       | ...    | ...      | ...         | ...         |
       
       ## Report Metadata
       - Final Version: CONSOLIDATED
       - Total figures: [count]
       - Generated: [timestamp]
       ```
    
    5. FIGURE REFERENCE GUIDELINES:
       - ALWAYS check figures/ directory for available plots
       - NEVER create a report without figure references
       - Use relative paths: ../figures/ (from reports/ directory)
       - Provide meaningful captions for each figure
       - Reference figures in the text: "As shown in Figure X..."
       - Create figure table in appendix for quick reference
       
    6. QUALITY CHECKS FOR FIGURES:
       - Ensure every generated figure is referenced
       - Verify figure paths are correct
       - Check that descriptions match the actual analysis
       - Confirm insights are tied to specific visualizations
       
    7. MANDATORY: Use save_code_file() tool to create save scripts:
       For iterative reports:
       ```python
       # Script to save versioned report
       import json
       from pathlib import Path
       
       # Your report content here
       markdown_content = '''[YOUR REPORT CONTENT]'''
       json_content = {...}  # Your JSON summary
       
       # Determine version number
       reports_dir = Path('reports')
       version = 1
       while (reports_dir / f'data_report_v{version}.md').exists():
           version += 1
       
       # Save versioned files
       with open(f'reports/data_report_v{version}.md', 'w') as f:
           f.write(markdown_content)
       with open(f'reports/data_report_v{version}.json', 'w') as f:
           json.dump(json_content, f, indent=2)
       
       # Also save as latest
       with open('reports/data_report_latest.md', 'w') as f:
           f.write(markdown_content)
           
       print(f"Report v{version} saved successfully")
       ```
       
       For FINAL consolidated report:
       ```python
       # Script to save FINAL consolidated report
       from datetime import datetime
       import json
       from pathlib import Path
       
       # Check for existing FINAL reports
       reports_dir = Path('reports')
       existing_finals = list(reports_dir.glob('data_report_FINAL*.md'))
       
       # If multiple FINAL reports exist, read and merge them
       if len(existing_finals) > 1:
           print(f"Found {len(existing_finals)} existing FINAL reports to consolidate")
           # Your logic to merge content from all FINAL reports
       
       # Your consolidated report content
       final_markdown = '''[YOUR FINAL CONSOLIDATED CONTENT]'''
       final_json = {...}  # Final JSON summary
       
       # Save FINAL report (always overwrites the main one)
       with open('reports/data_report_FINAL.md', 'w', encoding='utf-8') as f:
           f.write(final_markdown)
       
       # Also archive with timestamp
       timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
       with open(f'reports/data_report_FINAL_{timestamp}.md', 'w', encoding='utf-8') as f:
           f.write(final_markdown)
       
       # Save JSON version
       with open('reports/data_report_FINAL.json', 'w', encoding='utf-8') as f:
           json.dump(final_json, f, indent=2)
           
       print("Final consolidated report saved as reports/data_report_FINAL.md")
       print(f"Archive saved as reports/data_report_FINAL_{timestamp}.md")
       ```
    
    9. HANDLING MULTIPLE FINAL REPORTS:
       - If told "Multiple FINAL reports found, please consolidate":
         * List all data_report_FINAL*.md files
         * Read content from each
         * Merge insights, removing duplicates
         * Create one comprehensive FINAL report
         * Save as data_report_FINAL.md (overwriting)
         * Archive with timestamp as usual
    
    You create reports that comprehensively document both numerical results AND visual insights.""",
    description="Technical writer who creates and consolidates versioned reports."
)

executor = autogen.ConversableAgent(
    name="executor",
    llm_config=llm_config,  # Add llm_config to enable tool registration
    system_message="""You are a code execution specialist. Your responsibilities:
    1. When data_validator provides code:
       - Execute the QUICK validation code
       - If SUCCESS: Show brief validation result and tell data_planner "Validation passed, ready for analysis"
       - If FAILURE: Report issue back to data_validator for assessment
       
    2. When data_analyzer provides code:
       - Execute the comprehensive analysis code
       - If SUCCESS: Show results and tell data_planner to review outputs
       - If FAILURE: Report error back to data_analyzer for fixes
       
    3. When data_reporter provides code:
       - Execute the report saving code
       - If SUCCESS: 
         * Check what was saved: ls -la reports/*.md
         * For versioned reports: Confirm "Report vX saved successfully"
         * For FINAL report: Confirm "Final report saved as reports/data_report_FINAL.md"
         * Show preview of what was saved
       - If FAILURE: Report error back to data_reporter for fixes
       
    4. After executing validation (quick check):
       - Show brief validation result
       - Tell data_planner either "Validation passed" or "Validation failed: [reason]"
       
    5. After executing analysis (comprehensive):
       - Show console output
       - List created files: ls -la stats/ figures/
       - IMPORTANT: Show full statistics: cat stats/statistics.json
       - List figures: ls figures/*.png
       - Tell data_planner: "Analysis complete. Review the statistics above."
       
    6. After executing report saving code:
       - TOOL: Use check_analysis_files() to verify what was saved
       - For iterative reports:
         * Confirm which version was saved
         * Show preview if needed
       - For FINAL report:
         * TOOL: Use verify_final_report() to confirm FINAL report exists
         * Show the verification result to data_planner
         * State clearly: "Final report saved and verified" or "Final report NOT saved"
       
    7. File verification support:
       - When asked to check files, use the provided tools
       - Don't rely on shell commands like ls or cat
       - Use check_analysis_files() for general file check
       - Use verify_final_report() for final report verification
       
    IMPORTANT: Route results correctly:
    - data_validator errors → back to data_validator
    - data_analyzer errors → back to data_analyzer
    - data_reporter errors → back to data_reporter
    - Successful results → to data_planner
    You're already in the eda/ folder - all paths are relative to here.""",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "eda",
        "use_docker": False,
        "timeout": 240,
    },
    description="Executes code and confirms file saves."
)

# Register tools for data_planner
register_function(
    load_similar_analyses,
    caller=data_planner,
    executor=executor,
    name="load_similar_analyses",
    description="Load similar past analyses for learning. Args: file_path (str): Path of file to analyze, limit (int): Max similar reports. Returns dict with similar reports and patterns."
)

register_function(
    load_current_reports,
    caller=data_planner,
    executor=executor,
    name="load_current_reports",
    description="Load current analysis reports for review. Checks for all versions including FINAL. No arguments needed. Returns dict with report list and final report status."
)

register_function(
    check_analysis_files,
    caller=data_planner,
    executor=executor,
    name="check_analysis_files",
    description="Check what analysis files exist in EDA directories. No arguments needed. Returns dict with file counts and existence info for stats, figures, and reports."
)

register_function(
    verify_final_report,
    caller=data_planner,
    executor=executor,
    name="verify_final_report",
    description="Verify that the FINAL consolidated report exists. No arguments needed. Returns dict with final report existence and preview."
)

register_function(
    save_analysis_to_history,
    caller=data_planner,
    executor=executor,
    name="save_analysis_to_history",
    description="Save analysis to history. Args: file_path (str), data_summary (dict), statistics (dict), report_content (str), insights (list of str). Returns status dict."
)

register_function(
    get_historical_insights,
    caller=data_planner,
    executor=executor,
    name="get_historical_insights",
    description="Get insights from past analyses. Args: limit (int): Max insights. Returns dict with historical insights."
)

# The executor can also use these tools directly (as both caller and executor)
# This allows executor to check files when needed
for tool_func, tool_name, tool_desc in [
    (check_analysis_files, "check_analysis_files", "Check what analysis files exist. Returns file counts and paths."),
    (verify_final_report, "verify_final_report", "Verify FINAL report exists. Returns existence status and preview.")
]:
    register_function(
        tool_func,
        caller=executor,
        executor=executor,
        name=tool_name,
        description=tool_desc
    )

# Register the code saving tool for data_validator, data_analyzer, and data_reporter
for caller in [data_analyzer, data_validator, data_reporter]:
    register_function(
        save_agent_code,
        caller=caller,
        executor=executor,
        name="save_code_file",
        description="Save code to a file with automatic versioning. Args: code (str): The code content to save, filename (str): Desired filename (e.g., 'analysis.py'), subfolder (str, optional): Subfolder within eda directory (e.g., 'code'), base_dir (str): Base directory, defaults to 'eda'. Returns dict with status and file path.",
    )

# Register consolidation tool for data_planner
register_function(
    consolidate_final_reports,
    caller=data_planner,
    executor=executor,
    name="consolidate_final_reports",
    description="Check if multiple FINAL reports exist and need consolidation. No arguments needed. Returns details about all FINAL reports."
)

# Set up group chat with controlled transitions
groupchat = autogen.GroupChat(
    agents=[data_planner, data_validator, data_analyzer, data_reporter, executor],
    messages=[],
    allowed_or_disallowed_speaker_transitions={
        data_planner: [data_validator, data_analyzer, data_reporter, data_planner],
        data_validator: [executor],
        data_analyzer: [executor],
        data_reporter: [executor],
        executor: [data_validator, data_analyzer, data_reporter, data_planner],
    },
    speaker_transitions_type="allowed",
    max_round=200,
    admin_name="data_planner",
)

# Create manager for the group chat
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").strip().upper() == "TERMINATE"
)

def perform_eda(file_path: str):
    """
    Perform comprehensive EDA on the specified file.
    
    Args:
        file_path: Path to the data file (can be absolute or relative)
    """
    # Validate file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return
    
    # Get absolute path for clarity
    abs_path = os.path.abspath(file_path)
    
    initial_message = f"""Please perform comprehensive Exploratory Data Analysis on the file: {file_path}
    
    File details:
    - Absolute Path: {abs_path}
    - Relative Path from eda folder: ../{file_path}
    - Extension: {os.path.splitext(file_path)[1]}
    - Size: {os.path.getsize(abs_path) / 1024:.2f} KB
    
    IMPORTANT: The executor runs from the 'eda' folder, so you may need to use '../{file_path}' or the absolute path '{abs_path}' to access the file.
    
    Requirements:
    1. Load and inspect the data structure
       - If data is nested (e.g., dictionaries with arrays, hierarchical structures), unfold and analyze each component
       - For .mat files: analyze each variable separately if multiple exist
       - For nested JSON/dict: explore all levels and sub-structures
    2. Generate descriptive statistics and SAVE to stats/statistics.json
    3. Create visualizations and SAVE to figures/ directory
    4. Identify patterns and anomalies
    5. SAVE final report to reports/data_report.md and reports/data_report.json
    
    Ensure all outputs are saved to the correct subdirectories within eda/"""
    
    # Start the conversation
    data_planner.initiate_chat(
        manager,
        message=initial_message,
    )

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default example file path
        file_path = "data/burgers_data_R10.mat"
    
    print(f"Starting EDA on: {file_path}")
    perform_eda(file_path)
