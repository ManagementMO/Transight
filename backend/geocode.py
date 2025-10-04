import pandas as pd
import os
import re

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_DATA_FILE = os.path.join(SCRIPT_DIR, 'ttc_bus_delays_master.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'geocoded_delays.csv')
STOPS_FILE = os.path.join(SCRIPT_DIR, 'stops.txt')

# --- Helper Functions ---

def clean_location_string(text):
    """Standardizes location strings for robust fuzzy matching."""
    if not isinstance(text, str) or pd.isna(text):
        return ''

    text = text.lower().strip()

    # Standardize common abbreviations
    text = text.replace(' stn', ' station')
    text = text.replace(' sta ', ' station ')
    text = text.replace(' st.', ' st')
    text = text.replace(' ave.', ' ave')
    text = text.replace(' rd.', ' rd')
    text = text.replace(' blvd.', ' blvd')

    # Standardize directional indicators
    text = text.replace('n/b', 'north').replace('s/b', 'south')
    text = text.replace('e/b', 'east').replace('w/b', 'west')
    text = text.replace(' nb ', ' north ').replace(' sb ', ' south ')
    text = text.replace(' eb ', ' east ').replace(' wb ', ' west ')

    # Normalize separators
    text = re.sub(r'\s+(at|and|&|/)\s+', ' at ', text)

    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)

    # Collapse spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# --- Geocoding Logic ---

def geocode_with_stops(df, stops_df):
    """Geocode locations using only the TTC GTFS stops.txt data."""
    print("\n--- Geocoding using TTC GTFS stops.txt ---")

    # Clean stop names
    stops_df['cleaned_name'] = stops_df['stop_name'].apply(clean_location_string)

    # Create lookup dictionary with averaged coordinates
    coordinate_map = stops_df.groupby('cleaned_name')[['stop_lat', 'stop_lon']].mean()
    stops_dict = coordinate_map.to_dict('index')

    # Clean location column
    df['cleaned_location'] = df['location'].apply(clean_location_string)

    # Match exact locations
    def get_coords(cleaned_loc):
        if cleaned_loc in stops_dict:
            return stops_dict[cleaned_loc]['stop_lat'], stops_dict[cleaned_loc]['stop_lon']
        return None, None

    df[['latitude', 'longitude']] = df['cleaned_location'].apply(
        lambda x: pd.Series(get_coords(x))
    )

    matched_count = df['latitude'].notna().sum()
    total_count = len(df)
    print(f"-> Matched {matched_count}/{total_count} locations ({matched_count/total_count:.1%})")

    return df.drop(columns=['cleaned_location'])

# --- Main Execution ---
if __name__ == "__main__":
    # Load input data
    try:
        df = pd.read_csv(INPUT_DATA_FILE)
        print(f"Successfully loaded '{INPUT_DATA_FILE}' with {len(df)} rows.")
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{INPUT_DATA_FILE}'")
        exit(1)

    # Load stops.txt
    try:
        stops_df = pd.read_csv(STOPS_FILE)
        print(f"Successfully loaded '{STOPS_FILE}' with {len(stops_df)} stops.")
    except FileNotFoundError:
        print(f"ERROR: stops.txt not found at '{STOPS_FILE}'")
        exit(1)

    # Geocode using stops.txt only
    original_count = len(df)
    df = geocode_with_stops(df, stops_df)

    # Drop rows that failed to geocode
    df_geocoded = df[df['latitude'].notna()].copy()
    dropped_count = original_count - len(df_geocoded)

    # Final report
    print("\n--- Geocoding Complete ---")
    print(f"Original Records:        {original_count}")
    print(f"Successfully Geocoded:   {len(df_geocoded)} ({len(df_geocoded)/original_count:.1%})")
    print(f"Dropped (no match):      {dropped_count}")

    # Save only successfully geocoded data
    df_geocoded.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Geocoded data saved to '{OUTPUT_FILE}'")

    # Show sample of results
    if len(df_geocoded) > 0:
        print("\nSample of geocoded data:")
        sample = df_geocoded[['location', 'latitude', 'longitude']].head(10)
        for idx, row in sample.iterrows():
            print(f"  {row['location'][:50]:50s} → ({row['latitude']:.5f}, {row['longitude']:.5f})")