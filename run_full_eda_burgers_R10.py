import os
import numpy as np
import scipy.io as sio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

def load_matlab_data(filepath):
    """Load MATLAB .mat file and return data dictionary"""
    try:
        data = sio.loadmat(filepath)
        return data
    except Exception as e:
        print(f"Error loading MATLAB file: {e}")
        return None

def analyze_shape(data_dict):
    """Analyze the shape of all variables in the data"""
    shape_info = {}
    
    for key, value in data_dict.items():
        # Skip MATLAB metadata keys
        if not key.startswith('__'):
            if isinstance(value, np.ndarray):
                shape_info[key] = {
                    'shape': value.shape,
                    'ndim': value.ndim,
                    'size': value.size,
                    'dtype': str(value.dtype)
                }
    
    return shape_info

def analyze_statistics(data_dict):
    """Perform statistical analysis on numerical data"""
    stats_info = {}
    
    for key, value in data_dict.items():
        # Skip MATLAB metadata keys
        if not key.startswith('__'):
            if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.number):
                # Flatten array for statistical analysis
                flat_data = value.flatten()
                
                stats_info[key] = {
                    'mean': float(np.mean(flat_data)),
                    'std': float(np.std(flat_data)),
                    'min': float(np.min(flat_data)),
                    'max': float(np.max(flat_data)),
                    'median': float(np.median(flat_data)),
                    'q25': float(np.percentile(flat_data, 25)),
                    'q75': float(np.percentile(flat_data, 75)),
                    'non_zero_count': int(np.count_nonzero(flat_data)),
                    'nan_count': int(np.isnan(flat_data).sum()),
                    'inf_count': int(np.isinf(flat_data).sum())
                }
    
    return stats_info

def create_visualizations(data_dict, output_dir):
    """Create and save visualization plots"""
    plots_dir = output_dir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    for key, value in data_dict.items():
        if not key.startswith('__') and isinstance(value, np.ndarray):
            if np.issubdtype(value.dtype, np.number):
                # Create figure with subplots
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                fig.suptitle(f'Analysis of {key}', fontsize=16)
                
                # 1. Histogram
                flat_data = value.flatten()
                axes[0, 0].hist(flat_data[~np.isnan(flat_data)], bins=50, edgecolor='black', alpha=0.7)
                axes[0, 0].set_title('Distribution')
                axes[0, 0].set_xlabel('Value')
                axes[0, 0].set_ylabel('Frequency')
                axes[0, 0].grid(True, alpha=0.3)
                
                # 2. Box plot
                axes[0, 1].boxplot(flat_data[~np.isnan(flat_data)])
                axes[0, 1].set_title('Box Plot')
                axes[0, 1].set_ylabel('Value')
                axes[0, 1].grid(True, alpha=0.3)
                
                # 3. If 2D data, show heatmap
                if value.ndim == 2:
                    im = axes[1, 0].imshow(value, aspect='auto', cmap='viridis')
                    axes[1, 0].set_title('Heatmap (2D view)')
                    axes[1, 0].set_xlabel('Dimension 1')
                    axes[1, 0].set_ylabel('Dimension 0')
                    plt.colorbar(im, ax=axes[1, 0])
                elif value.ndim == 1:
                    axes[1, 0].plot(value)
                    axes[1, 0].set_title('Line Plot')
                    axes[1, 0].set_xlabel('Index')
                    axes[1, 0].set_ylabel('Value')
                    axes[1, 0].grid(True, alpha=0.3)
                else:
                    axes[1, 0].text(0.5, 0.5, f'Data has {value.ndim} dimensions\nShape: {value.shape}',
                                   ha='center', va='center', transform=axes[1, 0].transAxes)
                    axes[1, 0].set_title('Dimension Info')
                
                # 4. QQ plot for normality check
                from scipy import stats
                stats.probplot(flat_data[~np.isnan(flat_data)][:min(1000, len(flat_data))], 
                             dist="norm", plot=axes[1, 1])
                axes[1, 1].set_title('Q-Q Plot (Normality Test)')
                axes[1, 1].grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig(plots_dir / f'{key}_analysis.png', dpi=100, bbox_inches='tight')
                plt.close()

def save_summary(shape_info, stats_info, output_dir):
    """Save analysis summary to text and JSON files"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as formatted text file
    with open(output_dir / 'summary.txt', 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("BURGERS DATA ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("1. SHAPE ANALYSIS\n")
        f.write("-" * 40 + "\n")
        for var_name, info in shape_info.items():
            f.write(f"\nVariable: {var_name}\n")
            f.write(f"  Shape: {info['shape']}\n")
            f.write(f"  Dimensions: {info['ndim']}\n")
            f.write(f"  Total elements: {info['size']}\n")
            f.write(f"  Data type: {info['dtype']}\n")
        
        f.write("\n\n2. STATISTICAL ANALYSIS\n")
        f.write("-" * 40 + "\n")
        for var_name, stats in stats_info.items():
            f.write(f"\nVariable: {var_name}\n")
            f.write(f"  Mean: {stats['mean']:.6f}\n")
            f.write(f"  Std Dev: {stats['std']:.6f}\n")
            f.write(f"  Min: {stats['min']:.6f}\n")
            f.write(f"  Max: {stats['max']:.6f}\n")
            f.write(f"  Median: {stats['median']:.6f}\n")
            f.write(f"  Q1 (25%): {stats['q25']:.6f}\n")
            f.write(f"  Q3 (75%): {stats['q75']:.6f}\n")
            f.write(f"  IQR: {stats['q75'] - stats['q25']:.6f}\n")
            f.write(f"  Non-zero values: {stats['non_zero_count']}\n")
            f.write(f"  NaN values: {stats['nan_count']}\n")
            f.write(f"  Inf values: {stats['inf_count']}\n")
    
    # Save as JSON for programmatic access
    summary_json = {
        'shape_analysis': shape_info,
        'statistical_analysis': stats_info
    }
    
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary_json, f, indent=2)
    
    # Save as CSV for statistical data
    stats_df = pd.DataFrame(stats_info).T
    stats_df.to_csv(output_dir / 'statistics.csv')

def main():
    """Main analysis pipeline"""
    # Setup paths
    project_root = Path(__file__).parent
    print(f"Project root directory: {project_root}")
    data_file = project_root / 'data' / 'burgers_data_R10.mat'
    output_dir = project_root / 'output' / 'eda'
    
    print(f"Loading data from: {data_file}")
    
    # Check if file exists
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        return
    
    # Load data
    data = load_matlab_data(str(data_file))
    if data is None:
        return
    
    print(f"Successfully loaded data with keys: {[k for k in data.keys() if not k.startswith('__')]}")
    
    # Perform analysis
    print("\nPerforming shape analysis...")
    shape_info = analyze_shape(data)
    
    print("Performing statistical analysis...")
    stats_info = analyze_statistics(data)
    
    print("Creating visualizations...")
    create_visualizations(data, output_dir)
    
    print("Saving summary...")
    save_summary(shape_info, stats_info, output_dir)
    
    print(f"\nAnalysis complete! Results saved to: {output_dir}")
    print(f"  - Summary text: {output_dir / 'summary.txt'}")
    print(f"  - Summary JSON: {output_dir / 'summary.json'}")
    print(f"  - Statistics CSV: {output_dir / 'statistics.csv'}")
    print(f"  - Plots: {output_dir / 'plots/'}")

if __name__ == "__main__":
    main()
