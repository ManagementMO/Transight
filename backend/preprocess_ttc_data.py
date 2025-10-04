import pandas as pd
import os
import glob

# --- Configuration ---

# --- NEW: Robust Path Handling ---
# This builds the correct path to your data folder regardless of where you run the script from.
# It starts from the script's location, goes up one level ('..') from 'backend' to 'Transight',
# then goes into the 'data' and 'ttc_delay_data' folders.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIRECTORY = os.path.join(SCRIPT_DIR, '..', 'data', 'ttc_delay_data')

# The name of the final combined CSV file.
OUTPUT_FILE = 'concatenated_ttc_bus_delays.csv'

# --- Main Script ---

def clean_column_names(df):
    """
    Standardizes column names by converting them to lowercase, 
    stripping whitespace, and replacing spaces/hyphens with underscores.
    """
    cleaned_columns = {}
    for col in df.columns:
        new_col = col.strip().lower().replace(' ', '_').replace('-', '_')
        cleaned_columns[col] = new_col
    df = df.rename(columns=cleaned_columns)
    return df

def process_files():
    """
    Finds, reads, standardizes, and concatenates all Excel files
    in the specified data directory.
    """
    # --- FIX 1: Look for .xlsx files instead of .csv ---
    excel_files = glob.glob(os.path.join(DATA_DIRECTORY, '*.xlsx'))

    if not excel_files:
        print(f"Error: No XLSX files found in the directory: '{DATA_DIRECTORY}'")
        print("Please make sure your folder structure is correct and files are present.")
        return
        
    # Sort files for more logical processing order
    excel_files.sort()

    print(f"Found {len(excel_files)} files to process in '{DATA_DIRECTORY}'. Starting...")

    all_dataframes = []

    # Define the final, standardized column names
    final_columns = [
        'date', 'route', 'time', 'day', 'location', 'incident', 
        'min_delay', 'min_gap', 'direction', 'vehicle'
    ]

    # Mapping for inconsistent column names
    column_name_map = {
        'report_date': 'date',
        'min__delay': 'min_delay',
        'delay' : 'min_delay',
        'min__gap': 'min_gap',
        'gap': 'min_gap'
    }

    for i, filepath in enumerate(excel_files):
        filename = os.path.basename(filepath)
        print(f"Processing file {i+1}/{len(excel_files)}: {filename}")
        
        try:
            # --- FIX 2: Use pd.read_excel() to read the file ---
            df = pd.read_excel(filepath)
            
            df = clean_column_names(df)
            df = df.rename(columns=column_name_map)

            for col in final_columns:
                if col not in df.columns:
                    print(f"  - Warning: Column '{col}' not found. Adding it as an empty column.")
                    df[col] = None 
            
            df = df[final_columns]
            all_dataframes.append(df)

        except Exception as e:
            print(f"  - ERROR: Could not process file {filename}. Reason: {e}")
            print("  - Skipping this file.")

    if not all_dataframes:
        print("\nNo dataframes were successfully processed. Exiting.")
        return

    print("\nConcatenating all processed files...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    print("Performing final data type conversions...")
    combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
    combined_df['min_delay'] = pd.to_numeric(combined_df['min_delay'], errors='coerce')
    combined_df['min_gap'] = pd.to_numeric(combined_df['min_gap'], errors='coerce')
    
    print("Sorting final dataset by date...")
    combined_df.dropna(subset=['date'], inplace=True)
    combined_df.sort_values(by='date', inplace=True)
    
    try:
        # We will save the combined file in the `Transight/backend/` folder, alongside the script.
        output_path = os.path.join(SCRIPT_DIR, OUTPUT_FILE)
        combined_df.to_csv(output_path, index=False)
        
        print("\n------------------------------------------------------")
        print("                  SUCCESS!                          ")
        print("------------------------------------------------------")
        print(f"All files have been combined into: {output_path}")
        print(f"Total rows in combined file: {len(combined_df)}")
        print("\nFirst 5 rows of the chronologically sorted data:")
        print(combined_df.head())
    except Exception as e:
        print(f"\nERROR: Could not save the final CSV file. Reason: {e}")


if __name__ == "__main__":
    process_files()