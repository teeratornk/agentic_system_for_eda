import autogen
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import llm_config

# Create EDA directory structure
eda_dirs = ["eda", "eda/stats", "eda/reports", "eda/figures"]
for dir_path in eda_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Define agents
data_planner = autogen.ConversableAgent(
    name="data_planner",
    llm_config=llm_config,
    system_message="""You are a data planning expert. Your responsibilities:
    1. Initial Phase - Create EDA specifications:
       - Specify data loading requirements
       - Define statistical metrics needed
       - List visualization types required
    2. Report Phase - After receiving statistics/figures from executor:
       - Analyze the statistics JSON content shown by executor
       - Create the ACTUAL REPORT CONTENT (not code):
         * Write the full markdown text for data_report.md
         * Create the JSON structure for data_report.json
       - Send this content to data_analyzer with instruction:
         "Save the following markdown content to reports/data_report.md: [content]
          Save the following JSON to reports/data_report.json: [content]"
    3. TERMINATION - After reports are successfully saved:
       - When executor confirms "Reports saved successfully"
       - Simply respond: "TERMINATE"
       - This ends the conversation
    4. NEVER write Python code - only specifications and report content
    You create report CONTENT, data_analyzer saves it, then you TERMINATE.""",
    description="Strategic planner who creates report content and terminates when complete."
)

data_analyzer = autogen.AssistantAgent(
    name="data_analyzer",
    llm_config=llm_config,
    system_message="""You are a data analysis expert proficient in Python. Your responsibilities:
    1. For analysis specifications from data_planner:
       - Save code as eda_analysis_vX.py
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
    5. Always save code to a file first, then request execution
    Transform specifications into insightful analysis code.""",
    description="Python expert who implements creative and comprehensive data analysis."
)

executor = autogen.ConversableAgent(
    name="executor",
    system_message="""You are a code execution specialist. Your responsibilities:
    1. When data_analyzer provides code:
       - First execute any file-saving code
       - Then execute the saved file with: python filename.py
    2. After executing analysis files:
       - Show console output
       - List created files: ls -la stats/ figures/
       - IMPORTANT: Show full statistics: cat stats/statistics.json
       - List figures: ls figures/*.png
       - Tell data_planner: "Analysis complete. Review the statistics above to create reports."
    3. After executing report saving:
       - Show: ls -la reports/
       - Show report content: head -30 reports/data_report.md
       - Confirm: "Reports saved successfully. All tasks complete."
    4. Always show file contents so data_planner can see the data
    Show actual content, especially statistics.json for report creation.""",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "eda",
        "use_docker": False,
    },
    description="Executes code and confirms completion for termination."
)

# Set up group chat with controlled transitions
groupchat = autogen.GroupChat(
    agents=[data_planner, data_analyzer, executor],
    messages=[],
    allowed_or_disallowed_speaker_transitions={
        data_planner: [data_analyzer],
        data_analyzer: [executor],
        executor: [data_analyzer, data_planner],
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
