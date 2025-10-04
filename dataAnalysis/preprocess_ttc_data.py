import pandas as pd
import os
import glob

# --- Configuration ---

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# Assumes this script is in a 'scripts' or 'backend' folder
DATA_DIRECTORY = os.path.join(SCRIPT_DIR, '..', 'data', 'ttc_delay_data') 

# <<< IMPROVEMENT 1: Output to Parquet for speed and efficiency >>>
# You can still output a CSV for human readability if you want.
OUTPUT_PARQUET_FILE = 'ttc_bus_delays_master.parquet'
OUTPUT_CSV_FILE = 'ttc_bus_delays_master.csv'

# --- Main Script ---

def clean_column_names(df):
    """Standardizes column names."""
    cleaned_columns = {}
    for col in df.columns:
        new_col = col.strip().lower().replace(' ', '_').replace('-', '_')
        cleaned_columns[col] = new_col
    df = df.rename(columns=cleaned_columns)
    return df

def process_files():
    """
    Finds, reads, standardizes, and concatenates all Excel files,
    then saves them in an efficient format.
    """
    excel_files = glob.glob(os.path.join(DATA_DIRECTORY, '*.xlsx'))
    if not excel_files:
        print(f"Error: No XLSX files found in the directory: '{DATA_DIRECTORY}'")
        return
        
    excel_files.sort()
    print(f"Found {len(excel_files)} files to process...")

    all_dataframes = []
    
    # Final column order we want
    final_columns = [
        'date', 'route', 'time', 'day', 'location', 'incident', 
        'min_delay', 'min_gap', 'direction', 'vehicle'
    ]

    # <<< IMPROVEMENT 2: Map expects already-cleaned names for robustness >>>
    # This map will fix inconsistencies AFTER the initial cleaning.
    column_name_map = {
        'report_date': 'date',     # From 'Report Date'
        'min__delay': 'min_delay', # From 'Min - Delay'
        'delay': 'min_delay',      # From 'Delay'
        'min__gap': 'min_gap',     # From 'Min - Gap'
        'gap': 'min_gap'           # From 'Gap'
    }

    for i, filepath in enumerate(excel_files):
        filename = os.path.basename(filepath)
        print(f"Processing file {i+1}/{len(excel_files)}: {filename}")
        
        try:
            df = pd.read_excel(filepath)
            
            # 1. Clean names first
            df = clean_column_names(df)
            
            # 2. Rename based on cleaned names
            df = df.rename(columns=column_name_map)

            # 3. Add any missing columns from our ideal set
            for col in final_columns:
                if col not in df.columns:
                    df[col] = None 
            
            # 4. Enforce column order and select only the columns we need
            df = df[final_columns]
            all_dataframes.append(df)

        except Exception as e:
            print(f"  - ERROR processing {filename}: {e}. Skipping file.")

    if not all_dataframes:
        print("\nNo dataframes were processed. Exiting.")
        return

    print("\nConcatenating all dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    print("Performing final cleaning and feature engineering...")

    # <<< IMPROVEMENT 3: Create a single, powerful datetime column >>>
    # First, handle potential non-string or None values in date/time columns
    combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce').dt.date

    # Handle time column which may already be time objects (2014-2016) or strings/datetime
    from datetime import time as time_type
    def safe_time_convert(val):
        if isinstance(val, time_type):
            return val  # Already a time object
        elif pd.isna(val):
            return None
        else:
            # Try to parse as datetime and extract time
            try:
                return pd.to_datetime(val).time()
            except:
                return None

    combined_df['time'] = combined_df['time'].apply(safe_time_convert)

    # Drop rows where date or time could not be parsed
    combined_df.dropna(subset=['date', 'time'], inplace=True)
    
    # Combine them into the master datetime column
    combined_df['datetime'] = combined_df.apply(lambda row: pd.Timestamp.combine(row['date'], row['time']), axis=1)

    # Convert numeric columns, coercing errors
    combined_df['min_delay'] = pd.to_numeric(combined_df['min_delay'], errors='coerce')
    combined_df['min_gap'] = pd.to_numeric(combined_df['min_gap'], errors='coerce')

    # Keep route as string since it contains alphanumeric values (e.g., 'A242')
    combined_df['route'] = combined_df['route'].astype(str)
    
    # Sort chronologically, which is great practice
    combined_df.sort_values(by='datetime', inplace=True)

    # Now we can drop the original redundant columns
    combined_df = combined_df.drop(columns=['date', 'time'])
    
    try:
        # Define output paths relative to the script location
        parquet_path = os.path.join(SCRIPT_DIR, OUTPUT_PARQUET_FILE)
        csv_path = os.path.join(SCRIPT_DIR, OUTPUT_CSV_FILE)
        
        # Save to Parquet (for your code)
        combined_df.to_parquet(parquet_path, index=False)
        
        # Save to CSV (for manual inspection)
        combined_df.to_csv(csv_path, index=False)
        
        print("\n---------------- SUCCESS ----------------")
        print(f"Saved master Parquet file to: {parquet_path}")
        print(f"Saved master CSV file to:     {csv_path}")
        print(f"Total rows in final dataset: {len(combined_df)}")
        print("\nFinal data schema and first 5 rows:")
        print(combined_df.info())
        print(combined_df.head())
    except Exception as e:
        print(f"\nERROR: Could not save the final files. Reason: {e}")

if __name__ == "__main__":
    process_files()