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
    """Standardizes location strings for robust matching."""
    if not isinstance(text, str) or pd.isna(text):
        return ''

    text = text.lower().strip()

    # Remove leading/trailing quotes and extra whitespace
    text = text.strip('"').strip()

    # Standardize station abbreviations - handle truncated names
    text = re.sub(r'\bstatio\b', 'station', text)  # "PIONEER VILLAGE STATIO" → "station"
    text = re.sub(r'\bsta\b', 'station', text)      # "STA" → "station"
    text = re.sub(r'\bstn\b', 'station', text)      # "stn" → "station"

    # Standardize street type abbreviations
    text = re.sub(r'\bave\.?\b', 'ave', text)
    text = re.sub(r'\brd\.?\b', 'rd', text)
    text = re.sub(r'\bblvd\.?\b', 'blvd', text)
    text = re.sub(r'\bst\.?\b', 'st', text)
    text = re.sub(r'\bdr\.?\b', 'dr', text)

    # Normalize intersection separators
    text = re.sub(r'\s+(at|and|&)\s+', ' at ', text)

    # Remove extra punctuation
    text = re.sub(r'[^\w\s]', ' ', text)

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# --- Geocoding Logic ---

def geocode_with_stops(df, stops_df):
    """Geocode ALL location types accurately using TTC stops.txt."""
    print("\n--- Geocoding using TTC GTFS stops.txt ---")

    # Clean stop names
    stops_df['cleaned_name'] = stops_df['stop_name'].apply(clean_location_string)

    # Strategy 1: Exact match lookup
    print("Building exact match index...")
    coordinate_map = stops_df.groupby('cleaned_name')[['stop_lat', 'stop_lon']].mean()
    exact_dict = coordinate_map.to_dict('index')

    # Strategy 2: Station name index (for "KENNEDY STATION" → "... at Kennedy Station")
    print("Building station index...")
    station_dict = {}
    for idx, row in stops_df.iterrows():
        cleaned = row['cleaned_name']
        if 'station' in cleaned:
            parts = cleaned.split()
            for i, word in enumerate(parts):
                if word == 'station' and i > 0:
                    # Extract station name (up to 3 words before "station")
                    station_words = []
                    for j in range(max(0, i-3), i+1):
                        if j < len(parts):
                            station_words.append(parts[j])
                    station_key = ' '.join(station_words)
                    if station_key not in station_dict:
                        station_dict[station_key] = []
                    station_dict[station_key].append((row['stop_lat'], row['stop_lon']))

    # Average station coordinates
    station_avg_dict = {}
    for key, coords_list in station_dict.items():
        avg_lat = sum(c[0] for c in coords_list) / len(coords_list)
        avg_lon = sum(c[1] for c in coords_list) / len(coords_list)
        station_avg_dict[key] = (avg_lat, avg_lon)

    # Strategy 3: Intersection index (for "BATHURST AND WILSON" → "Bathurst St at Wilson Ave")
    print("Building intersection index...")
    # Create a searchable structure: {('bathurst', 'wilson'): [(lat, lon), ...]}
    intersection_dict = {}
    for idx, row in stops_df.iterrows():
        cleaned = row['cleaned_name']
        # Check if this is an intersection (contains "at")
        if ' at ' in cleaned:
            parts = cleaned.split(' at ')
            if len(parts) == 2:
                # Extract key street names (first word from each part)
                street1_words = parts[0].split()
                street2_words = parts[1].split()

                if street1_words and street2_words:
                    # Use first word from each street (e.g., "bathurst", "wilson")
                    key = tuple(sorted([street1_words[0], street2_words[0]]))
                    if key not in intersection_dict:
                        intersection_dict[key] = []
                    intersection_dict[key].append((row['stop_lat'], row['stop_lon']))

    # Average intersection coordinates
    intersection_avg_dict = {}
    for key, coords_list in intersection_dict.items():
        avg_lat = sum(c[0] for c in coords_list) / len(coords_list)
        avg_lon = sum(c[1] for c in coords_list) / len(coords_list)
        intersection_avg_dict[key] = (avg_lat, avg_lon)

    print(f"Built {len(exact_dict)} exact, {len(station_avg_dict)} station, {len(intersection_avg_dict)} intersection patterns")

    # Clean location column
    df['cleaned_location'] = df['location'].apply(clean_location_string)

    # Geocoding with all strategies
    stats = {'exact': 0, 'station': 0, 'intersection': 0, 'partial': 0, 'failed': 0}

    def get_coords(cleaned_loc):
        if not cleaned_loc:
            stats['failed'] += 1
            return None, None

        # Strategy 1: Exact match
        if cleaned_loc in exact_dict:
            stats['exact'] += 1
            coords = exact_dict[cleaned_loc]
            return coords['stop_lat'], coords['stop_lon']

        # Strategy 2: Station match (for locations containing "station")
        if 'station' in cleaned_loc:
            if cleaned_loc in station_avg_dict:
                stats['station'] += 1
                return station_avg_dict[cleaned_loc]
            # Try progressive patterns
            words = cleaned_loc.split()
            if 'station' in words:
                station_idx = words.index('station')
                for start in range(max(0, station_idx - 3), station_idx):
                    key = ' '.join(words[start:station_idx + 1])
                    if key in station_avg_dict:
                        stats['station'] += 1
                        return station_avg_dict[key]

        # Strategy 3: Intersection match (for "X at Y" or "X and Y")
        if ' at ' in cleaned_loc:
            parts = cleaned_loc.split(' at ')
            if len(parts) == 2:
                street1 = parts[0].split()[0] if parts[0].split() else None
                street2 = parts[1].split()[0] if parts[1].split() else None
                if street1 and street2:
                    key = tuple(sorted([street1, street2]))
                    if key in intersection_avg_dict:
                        stats['intersection'] += 1
                        return intersection_avg_dict[key]

        # Strategy 4: Partial word match (for loops, garages, truncated names)
        # Only if location has 2+ words to avoid false matches
        loc_words = set(cleaned_loc.split())
        if len(loc_words) >= 2:
            best_match = None
            best_score = 0

            for stop_name, coords in exact_dict.items():
                stop_words = set(stop_name.split())
                # Count common words (excluding very common ones)
                common_words = loc_words & stop_words - {'at', 'and', 'the', 'station', 'st', 'ave', 'rd'}

                # Require at least 2 meaningful words in common
                if len(common_words) >= 2:
                    # Score = number of common words / total unique words
                    score = len(common_words) / len(loc_words | stop_words)
                    if score > best_score:
                        best_score = score
                        best_match = coords

            # Only accept if score is high enough (50%+ overlap)
            if best_match and best_score >= 0.5:
                stats['partial'] += 1
                return best_match['stop_lat'], best_match['stop_lon']

        stats['failed'] += 1
        return None, None

    print("Matching locations...")
    df[['latitude', 'longitude']] = df['cleaned_location'].apply(
        lambda x: pd.Series(get_coords(x))
    )

    matched_count = df['latitude'].notna().sum()
    total_count = len(df)
    print(f"-> Matched {matched_count}/{total_count} locations ({matched_count/total_count:.1%})")
    print(f"   Exact: {stats['exact']}, Station: {stats['station']}, Intersection: {stats['intersection']}, Partial: {stats['partial']}, Failed: {stats['failed']}")

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
