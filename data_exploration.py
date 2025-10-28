import os
import json
from pathlib import Path
import autogen
from config import llm_config

# Create necessary directories
base_dir = Path(__file__).parent
directories = [
    base_dir / "eda" / "agents" / "stats",      # Statistical results
    base_dir / "eda" / "agents" / "analysis",   # Analysis narratives
    base_dir / "eda" / "agents" / "figures",    # Visualizations
    base_dir / "eda" / "reports",               # Final reports
    base_dir / "coding",                        # Code execution
]
for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)

# Get absolute paths for the agents to use
stats_dir = str(base_dir / "eda" / "agents" / "stats")
stats_results_path = str(base_dir / "eda" / "agents" / "stats" / "statistical_results.json")
stats_summary_path = str(base_dir / "eda" / "agents" / "stats" / "summary_statistics.json")
correlations_path = str(base_dir / "eda" / "agents" / "stats" / "correlations.json")
outliers_path = str(base_dir / "eda" / "agents" / "stats" / "outliers.json")
quality_metrics_path = str(base_dir / "eda" / "agents" / "stats" / "data_quality.json")
time_series_path = str(base_dir / "eda" / "agents" / "stats" / "time_series_analysis.json")
analysis_details_path = str(base_dir / "eda" / "agents" / "analysis" / "analysis_details.txt")
analysis_insights_path = str(base_dir / "eda" / "agents" / "analysis" / "key_insights.md")
figures_dir = str(base_dir / "eda" / "agents" / "figures")
report_md_path = str(base_dir / "eda" / "reports" / "data_report.md")
report_json_path = str(base_dir / "eda" / "reports" / "data_report.json")

# Define the executor agent first (since it's referenced by others)
executor = autogen.ConversableAgent(
    name="Executor",
    system_message="""You are a code execution specialist responsible for:
    1. Executing Python code written by the data_analyzer and data_planner
    2. Handling file operations and data processing tasks
    3. Reporting execution results clearly with any outputs or errors
    4. Ensuring all file saves are successful
    5. Validating that outputs are created in the correct directories
    
    Always provide clear feedback on execution status and any issues encountered.""",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": str(base_dir),  # Use the script directory as working dir
        "use_docker": False,
    },
    description="Code execution specialist that runs Python code and reports results."
)

# Define the data analyzer agent
data_analyzer = autogen.AssistantAgent(
    name="data_analyzer",
    llm_config=llm_config,
    system_message=f"""You are an expert data analyst responsible for comprehensive data exploration and statistical analysis. Your role is to provide FACTS and STATISTICAL VALUES.

    Your responsibilities:
    
    1. Data Loading and Complete Inspection:
       - Load the data file from the provided path
       - Report EXACT shape: (rows, columns) or dimensions for multi-dimensional arrays
       - For physics/scientific data: identify if it's (time_steps, spatial_points, variables)
       - List ALL column names and their data types (or variable names for arrays)
       - Memory usage in MB
       - File size on disk
       - Data collection timespan (if temporal)
       - Sampling frequency (if applicable)
    
    2. Comprehensive Statistical Analysis (provide ALL exact numerical values):
       a) Basic Statistics for EVERY numerical column/variable:
          - Count, mean, median, mode, std deviation
          - Min, 25%, 50%, 75%, max values
          - Variance, standard error
          - Coefficient of variation (CV)
          - Range and interquartile range (IQR)
       
       b) Distribution Analysis:
          - Skewness value and interpretation
          - Kurtosis value and interpretation  
          - Shapiro-Wilk test p-value for normality
          - Anderson-Darling test statistic
          - Q-Q plot quantiles comparison
       
       c) Missing Data Analysis:
          - Exact count and percentage of missing values per column
          - Missing data patterns (MCAR/MAR/MNAR indicators)
          - Columns with >5%, >10%, >50% missing
          - Rows with any missing values count
       
       d) Outlier Detection:
          - IQR method: count of outliers per column
          - Z-score method (>3σ): count per column
          - Modified Z-score: count per column
          - Isolation Forest anomaly scores
          - Local Outlier Factor (LOF) scores
          - List top 10 most extreme values per column
    
    3. Advanced Statistical Measures:
       a) Correlation Analysis:
          - Full correlation matrix (Pearson)
          - Spearman rank correlations
          - Kendall's tau correlations
          - Top 10 strongest positive correlations
          - Top 10 strongest negative correlations
          - Multicollinearity detection (VIF scores)
       
       b) Information Theory Metrics:
          - Entropy for each column
          - Mutual information between features
          - Information gain ratios
       
       c) Time Series Analysis (if temporal):
          - Autocorrelation values (lag 1-20)
          - Partial autocorrelation values
          - Trend strength (linear regression R²)
          - Seasonality detection (FFT peaks)
          - Stationarity tests (ADF, KPSS p-values)
          - Change point detection results
    
    4. Data Quality Metrics:
       - Duplicate rows: exact count and percentage
       - Near-duplicate detection (similarity > 0.95)
       - Cardinality per column (unique values)
       - Cardinality ratio (unique/total)
       - Constant columns (single value)
       - Low variance columns (<0.01)
       - Data type inconsistencies
       - Value range violations
       - Referential integrity issues
    
    5. Sampling and Segmentation Analysis:
       - First 100 rows/timesteps statistics
       - Last 100 rows/timesteps statistics  
       - Random 10% sample statistics
       - Comparison between samples (KS test p-values)
       - Temporal segments analysis (if applicable)
       - Spatial segments analysis (if applicable)
       - Statistical stability across segments
    
    6. Feature Engineering Insights:
       - Suggested transformations (log, sqrt, box-cox lambda)
       - Interaction terms with high correlation
       - Polynomial features potential
       - Binning recommendations with optimal bins
       - Scaling requirements per feature
    
    7. Pattern Detection:
       - Periodicities detected (frequencies and strengths)
       - Trend changes/breakpoints
       - Clustering tendency (Hopkins statistic)
       - Principal components explaining 95% variance
       - Dimensionality reduction potential
    
    8. PHYSICS/SCIENTIFIC DATA SPECIFIC (if applicable):
       - Conservation law verification (mass, energy, momentum)
       - Shock detection and characteristics
       - Wave speed calculations
       - Dissipation rates
       - Spectral analysis (power spectrum)
       - Phase space analysis
       - Lyapunov exponents (for chaos detection)
    
    9. Output Requirements (USE THESE EXACT PATHS AND NAMING CONVENTIONS):
       STATISTICAL FILES (save to stats directory):
       - Complete results: {stats_results_path}
       - Summary statistics: {stats_summary_path}
       - Correlation matrices: {correlations_path}
       - Outlier analysis: {outliers_path}
       - Data quality metrics: {quality_metrics_path}
       - Time series analysis (if applicable): {time_series_path}
       
       ANALYSIS FILES:
       - Detailed narrative: {analysis_details_path}
       - Key insights: {analysis_insights_path}
       
       VISUALIZATIONS (save to figures directory with DESCRIPTIVE names):
       Generate and save visualizations to: {figures_dir}/
       
       USE DESCRIPTIVE FILENAMES like:
         * correlation_heatmap_all_features.png
         * distribution_histogram_[variable_name].png
         * missing_data_pattern_matrix.png
         * outliers_boxplot_all_features.png
         * time_series_decomposition_[variable].png
         * qq_plot_normality_test_[variable].png
         * feature_importance_ranking.png
         * pairwise_scatter_matrix.png
         * histogram_grid_all_numeric.png
         * violin_plots_distributions.png
         * temporal_evolution_[variable].png
         * spatial_pattern_t[timestep].png
         * autocorrelation_function_[variable].png
         * pca_explained_variance_curve.png
         * data_quality_summary_dashboard.png
       
       For multi-dimensional/physics data:
         * evolution_[variable]_over_time.png
         * snapshot_[variable]_t[timestep].png
         * phase_space_[var1]_vs_[var2].png
         * spectrum_analysis_[variable].png
       
       AVOID generic names like: a_485_hist.png
       INSTEAD use: histogram_variable_a_timestep_485.png
    
    CRITICAL REQUIREMENTS: 
    - Calculate EVERYTHING - the data_planner needs complete information
    - Provide EXACT NUMERICAL VALUES for all metrics
    - Use DESCRIPTIVE FILENAMES for all outputs
    - Organize statistics into logical separate files
    - Explore EVERY column and feature thoroughly
    - For physics data: analyze both temporal and spatial dimensions
    - Compare different samples and segments
    - Test multiple statistical hypotheses
    - Generate comprehensive visualizations with clear names
    - Save all results with clear organization
    - Use the ABSOLUTE PATHS provided above
    - Write efficient, vectorized code for large datasets
    - Handle errors gracefully and report any issues
    - NEVER include "TERMINATE" in your messages""",
    description="Expert data analyst that performs exhaustive statistical analysis and provides comprehensive quantitative metrics."
)

# Define the data planner agent
data_planner = autogen.ConversableAgent(
    name="data_planner",
    llm_config=llm_config,
    system_message=f"""You are a strategic data planning expert responsible for orchestrating the analysis process and providing insights. 

    Your responsibilities:
    
    1. Initial Planning Phase:
       - Receive and validate the data path from the user
       - Create a comprehensive analysis plan
       - Direct the data_analyzer on what specific analyses to perform
       - Specify which features/samples to explore
    
    2. Review and Quality Control:
       - Carefully review ALL statistical results from data_analyzer
       - Check that files were saved to: {stats_results_path}
       - Verify analysis details at: {analysis_details_path}
       - Check for completeness of the analysis
       - Identify missing analyses or unexplored features
       - Provide specific feedback to data_analyzer:
         * "Please analyze feature X in more detail"
         * "Explore the correlation between Y and Z"
         * "Sample data from different time periods/regions"
         * "Check for patterns in the outliers"
         * "Perform additional tests on the anomalies found"
    
    3. Iterative Improvement:
       - Request additional analyses until satisfied
       - Ensure all important aspects are covered
       - Verify statistical rigor and completeness
       - Push for deeper exploration where needed
    
    4. Synthesis and Recommendations:
       - Only after thorough analysis is complete:
         * Interpret the statistical findings
         * Identify key insights and patterns
         * Formulate actionable recommendations
         * Consider business/research implications
         * Prioritize findings by importance
    
    5. Final Deliverables (USE THESE EXACT PATHS):
       - Create comprehensive Markdown report at: {report_md_path}
       - Generate structured JSON report at: {report_json_path}
       
       JSON Structure:
       {{
           "executive_summary": "High-level overview",
           "key_findings": [
               {{"finding": "...", "statistical_evidence": "...", "importance": "high/medium/low"}}
           ],
           "data_quality": {{
               "completeness": "X%",
               "issues_found": [...],
               "reliability_score": "..."
           }},
           "recommendations": [
               {{"recommendation": "...", "rationale": "...", "priority": 1-5}}
           ],
           "areas_for_further_analysis": [...],
           "next_steps": [...],
           "metadata": {{
               "analysis_date": "...",
               "data_file": "...",
               "total_records": "...",
               "features_analyzed": [...]
           }}
       }}
    
    IMPORTANT:
    - Be demanding: request more analysis if needed
    - Don't accept superficial analysis
    - Ensure all features and samples are properly explored
    - Provide SPECIFIC feedback, not vague suggestions
    - Only provide recommendations AFTER thorough analysis
    - MUST write and save both reports using the EXACT PATHS provided above
    - Only YOU can terminate the conversation
    - When analysis is complete AND reports are saved, end your message with "ANALYSIS_COMPLETE_TERMINATE" """,
    description="Strategic data planner that reviews analyses, provides specific feedback for improvements, and creates comprehensive recommendations after thorough exploration."
)

# Create the group chat with speaker transitions
groupchat = autogen.GroupChat(
    agents=[data_planner, data_analyzer, executor],
    messages=[],
    allowed_or_disallowed_speaker_transitions={
        data_analyzer: [executor, data_planner],
        executor: [data_analyzer, data_planner],
        data_planner: [data_analyzer],
    },
    speaker_transitions_type="allowed",
    max_round=400,
)

# Create the group chat manager
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
    is_termination_msg=lambda x: (
        x.get("name") == "data_planner" and 
        "ANALYSIS_COMPLETE_TERMINATE" in x.get("content", "")
    ),
)

def create_sample_data():
    """Create a sample CSV file for testing."""
    import pandas as pd
    import numpy as np
    
    # Create sample data directory
    sample_dir = Path(__file__).parent / "data" / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'customer_id': range(1, n_samples + 1),
        'age': np.random.randint(18, 80, n_samples),
        'income': np.random.lognormal(10.5, 0.5, n_samples),
        'spending_score': np.random.randint(1, 100, n_samples),
        'membership_years': np.random.randint(0, 20, n_samples),
        'num_purchases': np.random.poisson(15, n_samples),
        'satisfaction_score': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.05, 0.1, 0.2, 0.4, 0.25]),
        'is_premium': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], n_samples),
        'channel_preference': np.random.choice(['Online', 'Store', 'Mobile'], n_samples, p=[0.5, 0.3, 0.2])
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    df.loc[np.random.choice(df.index, 50), 'satisfaction_score'] = np.nan
    df.loc[np.random.choice(df.index, 30), 'income'] = np.nan
    
    # Save to CSV
    sample_file = sample_dir / "customer_data.csv"
    df.to_csv(sample_file, index=False)
    
    print(f"Sample data created at: {sample_file}")
    return str(sample_file)

def start_data_exploration(data_path: str, additional_instructions: str = ""):
    """
    Start the data exploration process with the given data path.
    
    Args:
        data_path: Path to the data file to analyze
        additional_instructions: Optional additional instructions for the analysis
    """
    # Convert to absolute path
    if not os.path.isabs(data_path):
        # If relative path, make it relative to the script directory
        data_path = os.path.abspath(os.path.join(base_dir, data_path))
    
    # Validate the data path
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        
        # Try to look for the file in common locations
        possible_paths = [
            os.path.join(base_dir, data_path),
            os.path.join(base_dir, "data", os.path.basename(data_path)),
            os.path.join(os.getcwd(), data_path),
        ]
        
        for possible_path in possible_paths:
            if os.path.exists(possible_path):
                print(f"Found file at: {possible_path}")
                data_path = possible_path
                break
        else:
            print(f"\nSearched in:")
            for path in possible_paths:
                print(f"  - {path}")
            return
    
    # Normalize the path
    data_path = os.path.normpath(data_path)
    
    # Prepare the initial message with absolute path
    initial_message = f"""
    Please analyze the data located at: {data_path}
    
    {additional_instructions if additional_instructions else "Perform a comprehensive exploratory data analysis."}
    
    Data planner: Please coordinate with the data analyzer to explore this dataset thoroughly,
    create comprehensive reports, and save them to the designated output folders.
    
    Important file paths to use (use these EXACT paths in your Python code):
    
    STATISTICAL OUTPUTS:
    - Stats directory: {stats_dir}
    - Main statistical results: {stats_results_path}
    - Summary statistics: {stats_summary_path}
    - Correlations: {correlations_path}
    - Outliers: {outliers_path}
    - Data quality: {quality_metrics_path}
    - Time series (if applicable): {time_series_path}
    
    ANALYSIS OUTPUTS:
    - Analysis details: {analysis_details_path}
    - Key insights: {analysis_insights_path}
    
    VISUALIZATIONS:
    - Figures directory: {figures_dir}
    
    FINAL REPORTS:
    - Markdown report: {report_md_path}
    - JSON report: {report_json_path}
    
    CRITICAL: When writing Python code:
    1. Use the absolute paths provided above exactly as given
    2. Do NOT modify or construct paths - use them as provided
    3. The data_analyzer should save statistical results to the stats directory
    4. You (data_planner) must create and save both the Markdown and JSON reports
    5. Only the data_planner can terminate the conversation after saving all reports
    
    Note: The file path is absolute. When writing code, use this exact path: {data_path}
    """
    
    print(f"\n🚀 Starting data exploration for: {data_path}")
    print("=" * 60)
    
    try:
        # Start the conversation
        result = data_planner.initiate_chat(
            manager,
            message=initial_message,
            max_turns=400,  # Add max turns as safety
        )
        
        print("\n" + "=" * 60)
        print("✅ Data exploration completed successfully!")
        print("=" * 60)
        
        # Helper function to check both Windows and WSL paths
        def check_file_exists(windows_path):
            """Check if file exists in either Windows path or WSL equivalent."""
            if windows_path.exists():
                return True
            # Check WSL path equivalent
            wsl_style = Path(str(windows_path).replace('\\', '/'))
            if wsl_style.exists():
                return True
            # Check if file was created in /mnt/c/ path (WSL)
            mnt_path = Path('/mnt/c') / str(windows_path).replace('C:\\', '').replace('\\', '/')
            if mnt_path.exists():
                return True
            return False
        
        # Check if reports were created
        report_md = base_dir / "eda" / "reports" / "data_report.md"
        report_json = base_dir / "eda" / "reports" / "data_report.json"
        
        print("\n📁 Output Files:")
        
        # Check stats files
        stats_folder = base_dir / "eda" / "agents" / "stats"
        if stats_folder.exists():
            stats_files = list(stats_folder.glob("*.json"))
            if stats_files:
                print(f"  ✅ {len(stats_files)} statistical file(s) in: {stats_folder}")
                for file in stats_files[:5]:  # Show first 5 files
                    print(f"      - {file.name}")
            else:
                print(f"  ❌ No statistical files found in: {stats_folder}")
        else:
            print(f"  ⚠️  Stats folder not found, checking for WSL paths...")
        
        # Check analysis files  
        analysis_folder = base_dir / "eda" / "agents" / "analysis"
        if analysis_folder.exists():
            analysis_files = list(analysis_folder.glob("*"))
            if analysis_files:
                print(f"  ✅ {len(analysis_files)} analysis file(s) in: {analysis_folder}")
                for file in analysis_files:
                    print(f"      - {file.name}")
            else:
                print(f"  ❌ No analysis files found in: {analysis_folder}")
        
        # Check figures
        figures_path = base_dir / "eda" / "agents" / "figures"
        if figures_path.exists():
            png_files = list(figures_path.glob("*.png"))
            if png_files:
                print(f"  ✅ {len(png_files)} figure(s) saved in: {figures_path}")
                # List first few figure names
                for i, fig in enumerate(png_files[:5]):
                    print(f"      - {fig.name}")
                if len(png_files) > 5:
                    print(f"      ... and {len(png_files) - 5} more")
            else:
                print(f"  ⚠️  Figures directory exists but no PNG files found")
        
        # Check final reports with better path handling
        if check_file_exists(report_md):
            print(f"  ✅ Markdown report: {report_md}")
            # Try to show file size
            try:
                size = report_md.stat().st_size if report_md.exists() else 0
                if size > 0:
                    print(f"      Size: {size / 1024:.1f} KB")
            except:
                pass
        else:
            print(f"  ❌ Markdown report not found: {report_md}")
            print(f"      Note: Files may have been saved to WSL path. Check manually.")
            
        if check_file_exists(report_json):
            print(f"  ✅ JSON report: {report_json}")
            # Try to show file size
            try:
                size = report_json.stat().st_size if report_json.exists() else 0
                if size > 0:
                    print(f"      Size: {size / 1024:.1f} KB")
            except:
                pass
        else:
            print(f"  ❌ JSON report not found: {report_json}")
            print(f"      Note: Files may have been saved to WSL path. Check manually.")
        
        # Additional note about WSL paths
        if not (report_md.exists() and report_json.exists()):
            print("\n  💡 If running with WSL, check these locations:")
            print(f"      WSL: /mnt/c/{str(report_md).replace('C:', '').replace(chr(92), '/')}")
            print(f"      WSL: /mnt/c/{str(report_json).replace('C:', '').replace(chr(92), '/')}")
            
    except Exception as e:
        print(f"\n❌ Error during data exploration: {e}")
        
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        data_file_path = sys.argv[1]
        instructions = sys.argv[2] if len(sys.argv) > 2 else ""
        start_data_exploration(data_file_path, instructions)
    else:
        print("\n📊 Data Exploration System")
        print("=" * 60)
        print("\nNo arguments provided. Choose an option:")
        print("1. Run with sample test data")
        print("2. Enter your own data file path")
        print("3. Show usage and exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🔧 Creating sample test data...")
            sample_file = create_sample_data()
            instructions = input("\nEnter additional instructions (or press Enter to skip): ").strip()
            start_data_exploration(sample_file, instructions)
        elif choice == "2":
            data_path = input("\nEnter the path to your data file: ").strip()
            instructions = input("Enter additional instructions (or press Enter to skip): ").strip()
            start_data_exploration(data_path, instructions)
        else:
            print("\nUsage: python data_exploration.py <path_to_data_file> [additional_instructions]")
            print("Example: python data_exploration.py data/sample.csv 'Focus on customer segmentation'")
