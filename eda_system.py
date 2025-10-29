import autogen
from autogen import register_function
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import llm_config
from code_saver_tool import save_agent_code

# Create EDA directory structure
eda_dirs = ["eda", "eda/stats", "eda/reports", "eda/figures", "eda/code"]
for dir_path in eda_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Define agents
data_planner = autogen.ConversableAgent(
    name="data_planner",
    llm_config=llm_config,
    system_message="""You are a data planning expert specialized in scientific machine learning and reduced order modeling. Your responsibilities:
    1. Initial Phase - Create validation and EDA specifications:
       - First, request data validation from data_validator
       - After validation passes, specify analysis requirements
       - Define statistical metrics and visualizations needed
       - Consider physics-based patterns and dimensionality reduction opportunities
       - IMPORTANT FOR LARGE DATA: For arrays with many columns/features (>100):
         * Request AGGREGATE statistics across all dimensions, not per-column
         * Focus on overall data characteristics, not individual feature stats
         * Example: "Calculate overall min/max/mean/std for the entire array"
    2. Report Phase - After receiving statistics/figures from executor:
       - Analyze the statistics JSON content shown by executor
       - CRITICAL: Check variable names in statistics match those in reports
       - Create the ACTUAL REPORT CONTENT (not code):
         * Write the full markdown text for data_report.md
         * Create the JSON structure for data_report.json
         * Use EXACT variable names from statistics.json (e.g., if stats show 'a', 'a_smooth', don't write 't', 'x')
       - Send this content to data_analyzer with instruction:
         "Save the following markdown content to reports/data_report.md: [content]
          Save the following JSON to reports/data_report.json: [content]"
    3. TERMINATION - After reports are successfully saved:
       - When executor confirms "Reports saved successfully"
       - Simply respond: "TERMINATE"
       - This ends the conversation
    4. NEVER write Python code - only specifications and report content
    5. INCREMENTAL REQUESTS - Be efficient:
       - Check what's already done (stats/statistics.json, figures/*, reports/*)
       - Only request NEW or ADDITIONAL analysis, never repeat completed work
       - If you need more analysis, specify ONLY the additional metrics needed
       - Example: "Add correlation matrix to existing statistics" not "Redo all analysis"
    6. CONSISTENCY CHECK:
       - Variable names in reports MUST match those in statistics.json
       - Don't invent new variable names or interpretations
       - Report what the data actually contains, not what you assume it represents
    7. STATISTICAL EFFICIENCY:
       - For high-dimensional data (2D arrays with >100 columns), request:
         * Overall statistics (entire array)
         * Sample statistics (first few columns if needed)
         * Correlation for key variables only
       - Avoid per-column statistics for thousands of dimensions
    Be critically curious: question unusual patterns, probe deeper into interesting findings, and always ask "what else can this data tell us?" before finalizing reports.
    Start with validation, then analysis, create reports, then TERMINATE.""",
    description="Strategic planner who coordinates validation, analysis, and reporting."
)

data_validator = autogen.AssistantAgent(
    name="data_validator",
    llm_config=llm_config,
    system_message="""You are a data quality expert. Your responsibilities:
    1. When data_planner requests validation, create Python code to:
       - Load and inspect the data structure
       - Check for data quality issues that matter
       - Assess data readiness for analysis
    2. Quality checks to consider (adapt to data type):
       - Data completeness and missing patterns
       - Data types and format consistency
       - Value ranges and potential anomalies
       - Size and memory considerations
       - Any domain-specific quality concerns
    3. Be pragmatic:
       - Focus on issues that impact analysis
       - Provide actionable quality insights
       - Save validation results to stats/data_quality.json
    4. MANDATORY: Use save_code_file() tool to save your code:
       - save_code_file(code=your_code, filename="data_validation.py", subfolder="code")
       - This saves to eda/code/ with automatic versioning
       - Then request: "Please execute: python code/data_validation_vX.py"
       - DO NOT write code blocks to save files manually
    IMPORTANT: Use relative paths - stats/, figures/, reports/ (NOT eda/stats/)
    Adapt validation to the data's nature and intended use.""",
    description="Data quality expert who ensures data readiness for analysis."
)

data_analyzer = autogen.AssistantAgent(
    name="data_analyzer",
    llm_config=llm_config,
    system_message="""You are a data analysis expert proficient in Python. Your responsibilities:
    1. For analysis specifications from data_planner:
       - Create comprehensive statistics in stats/statistics.json
       - Create insightful visualizations in figures/
    2. Statistical analysis capabilities to consider:
       - Time series patterns if temporal data detected
       - Outlier detection using appropriate methods
       - Feature relationships and correlations
       - Distribution characteristics and statistical tests
       - Any domain-specific metrics that add value
    3. Be creative with your analysis:
       - Adapt methods to the data type and structure
       - Discover hidden patterns and anomalies
       - Generate both expected and unexpected insights
    4. For report content from data_planner:
       - Save markdown/JSON content to reports as requested
    5. MANDATORY: Use save_code_file() tool to save your code:
       - save_code_file(code=analysis_code, filename="eda_analysis.py", subfolder="code")
       - This saves to eda/code/ with automatic versioning
       - Then request: "Please execute: python code/eda_analysis_vX.py"
       - DO NOT write code blocks to save files manually
    IMPORTANT: Use relative paths - stats/, figures/, reports/ (NOT eda/stats/)
    Transform specifications into insightful analysis code.""",
    description="Python expert who implements creative and comprehensive data analysis."
)

executor = autogen.ConversableAgent(
    name="executor",
    system_message="""You are a code execution specialist. Your responsibilities:
    1. When data_validator provides code:
       - Execute the validation code
       - If SUCCESS: Show validation results and tell data_planner "Validation complete"
       - If FAILURE: Report error back to data_validator for fixes
    2. When data_analyzer provides code:
       - Execute the analysis/report saving code
       - If SUCCESS: Show results and tell data_planner to review/proceed
       - If FAILURE: Report error back to data_analyzer for fixes
    3. After executing validation files:
       - Show validation results from stats/data_quality.json
       - Report any data quality issues found to data_planner
    4. After executing analysis files:
       - Show console output
       - List created files: ls -la stats/ figures/
       - IMPORTANT: Show full statistics: cat stats/statistics.json
       - List figures: ls figures/*.png
       - Tell data_planner: "Analysis complete. Review the statistics above to create reports."
    5. After executing report saving:
       - Show: ls -la reports/
       - Show report content: head -30 reports/data_report.md
       - Confirm to data_planner: "Reports saved successfully. All tasks complete."
    IMPORTANT: Route results correctly:
    - data_validator errors → back to data_validator
    - data_analyzer errors → back to data_analyzer
    - Successful results → to data_planner
    You're already in the eda/ folder - all paths are relative to here.""",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "eda",
        "use_docker": False,
        "timeout": 120,  # Add 120 second timeout
    },
    description="Executes code and routes feedback to the appropriate agent."
)

# Register the code saving tool for data_validator and data_analyzer
for caller in [data_analyzer, data_validator]:
    register_function(
        save_agent_code,
        caller=caller,
        executor=executor,
        name="save_code_file",
        description="Save code to a file with automatic versioning. Args: code (str): The code content to save, filename (str): Desired filename (e.g., 'analysis.py'), subfolder (str, optional): Subfolder within eda directory (e.g., 'code'), base_dir (str): Base directory, defaults to 'eda'. Returns dict with status and file path.",
    )

# Set up group chat with controlled transitions
groupchat = autogen.GroupChat(
    agents=[data_planner, data_validator, data_analyzer, executor],
    messages=[],
    allowed_or_disallowed_speaker_transitions={
        data_planner: [data_validator, data_analyzer],
        data_validator: [executor],
        data_analyzer: [executor],
        executor: [data_validator, data_analyzer, data_planner],
    },
    speaker_transitions_type="allowed",
    max_round=200,
    # Add termination function
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
