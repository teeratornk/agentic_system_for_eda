import autogen
from autogen import register_function
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import llm_config
from code_saver_tool import save_agent_code
from report_history_tool import save_analysis_to_history, load_similar_analyses, get_historical_insights, load_current_reports

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
       - Review the final report for:
         * Complete coverage of all analyses performed
         * Clear evolution of insights through iterations
         * All key findings properly highlighted
         * Comprehensive recommendations
       
    6. Finalization and Termination:
       - Review the final consolidated report
       - If satisfactory:
         * TOOL: Call save_analysis_to_history() with final report
         * State: "Final report approved. Analysis complete."
         * Then respond: "TERMINATE"
       - If not satisfactory:
         * Request specific final adjustments
         * Review again before terminating
       
    WORKFLOW:
    □ Load similar analyses
    □ Request validation
    □ Request comprehensive analysis
    □ Iterate on reports with data_reporter
    □ Request FINAL CONSOLIDATED REPORT
    □ Review final report
    □ Save to history
    □ TERMINATE
    
    AVAILABLE TOOLS:
    - load_similar_analyses(file_path, limit=5)
    - load_current_reports() - To review saved reports
    - save_analysis_to_history(file_path, data_summary, statistics, report_content, insights)
    - get_historical_insights(limit=10)
    
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
    system_message="""You are a technical report writer specialized in scientific data analysis. Your responsibility is creating and consolidating comprehensive reports.
    
    1. ITERATIVE REPORT CREATION:
       When data_planner requests a report:
       - Read stats/statistics.json for all numerical data
       - Check existing report versions: ls -la reports/*.md
       - Create new version building on previous (if exists)
       - Save with versioning (v1, v2, v3, etc.)
       
    2. FINAL REPORT CONSOLIDATION:
       When data_planner requests "FINAL CONSOLIDATED REPORT":
       - List all report versions: reports/data_report_v*.md
       - Consolidate all versions into comprehensive final report
       - Structure the final report to show:
         * Complete analysis from all iterations
         * Evolution of insights (what was added in each version)
         * All statistics (basic + advanced)
         * All findings and recommendations
         * Analysis lineage/history
       
    3. FINAL REPORT STRUCTURE:
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
       
       ## 3. Analysis Evolution
       ### Version 1 - Initial Analysis
       - What was analyzed
       - Key findings
       
       ### Version 2 - Enhanced Analysis
       - What was added
       - New insights discovered
       
       ### Version 3+ - Further Refinements
       - Additional analyses
       - Deeper insights
       
       ## 4. Consolidated Findings
       1. [Most important finding across all analyses]
       2. [Second key finding]
       3. [Additional insights from iterations]
       
       ## 5. Complete Visualizations
       - All figures generated across iterations
       - Key patterns identified
       
       ## 6. Final Recommendations
       - Comprehensive recommendations
       - Suggested next steps
       - Modeling approaches
       
       ## Report Metadata
       - Final Version: CONSOLIDATED
       - Total iterations: [number]
       - Generated: [timestamp]
       - Analysis versions included: v1 through v[N]
       ```
    
    4. CONSOLIDATION STRATEGY:
       - Merge content, don't duplicate
       - Preserve the best insights from each version
       - Show progression of understanding
       - Highlight what each iteration added
       - Create coherent narrative from all versions
       
    5. SAVING REPORTS:
       - Iterative versions: data_report_v1.md, v2.md, etc.
       - Final report: data_report_FINAL.md
       - Also save JSON summaries
       
    6. MANDATORY: Use save_code_file() tool:
       For iterative reports:
       - save_code_file(code=report_saving_code, filename="save_reports.py", subfolder="code")
       
       For final report:
       - save_code_file(code=final_report_code, filename="save_final_report.py", subfolder="code")
       - Final report should be saved as: reports/data_report_FINAL.md
       
    7. QUALITY CHECKS:
       - Ensure no analysis is lost in consolidation
       - Verify all statistics are accurately reported
       - Check that evolution story is clear
       - Confirm all recommendations are included
       
    You create both iterative reports and the final consolidated masterpiece.""",
    description="Technical writer who creates and consolidates comprehensive reports."
)

executor = autogen.ConversableAgent(
    name="executor",
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
       - If SUCCESS: Confirm reports saved and show preview
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
       - Check if reports were saved: ls -la reports/
       - Show first 30 lines: head -30 reports/data_report.md
       - Confirm JSON created
       - Tell data_planner: "Reports saved. Review the report above."
       
    7. When data_planner requests to see reports:
       - Show full markdown: cat reports/data_report.md
       - Show JSON summary: head -50 reports/data_report.json
       
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
        "timeout": 120,
    },
    description="Executes code and routes feedback to the appropriate agent."
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
    description="Load current analysis reports for review. No arguments needed. Returns dict with markdown and JSON report contents."
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

# Register the code saving tool for data_validator, data_analyzer, and data_reporter
for caller in [data_analyzer, data_validator, data_reporter]:
    register_function(
        save_agent_code,
        caller=caller,
        executor=executor,
        name="save_code_file",
        description="Save code to a file with automatic versioning. Args: code (str): The code content to save, filename (str): Desired filename (e.g., 'analysis.py'), subfolder (str, optional): Subfolder within eda directory (e.g., 'code'), base_dir (str): Base directory, defaults to 'eda'. Returns dict with status and file path.",
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
