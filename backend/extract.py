import os
import requests
import zipfile
import io

# --- Configuration ---
# The target folder where 'stops.txt' will be saved.
TARGET_DIR = 'gtfs_data'
STOPS_FILE_PATH = os.path.join(TARGET_DIR, 'stops.txt')

def find_gtfs_download_url():
    """
    Searches the CKAN API to dynamically find the correct, current URL 
    for the TTC GTFS zip file.
    """
    # The API endpoint for searching datasets
    search_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_search"
    
    # We will search for a dataset containing these keywords. This is a stable search.
    params = {'q': 'TTC Routes and Schedules'}
    
    print("Searching the City of Toronto Open Data portal for the correct dataset...")
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # The search returns a list of results. We'll check the most relevant ones.
        for result in data['result']['results']:
            # The 'resources' key contains the list of files in the dataset
            for resource in result['resources']:
                # We are looking for a ZIP file with 'GTFS' in its name.
                resource_name = resource.get('name', '').lower()
                resource_format = resource.get('format', '').lower()

                if 'zip' in resource_format and 'gtfs' in resource_name:
                    found_url = resource['url']
                    print(f"Success! Found a valid download link: {found_url}")
                    return found_url
        
        # If the loop completes without finding a suitable link
        print("ERROR: Search was successful, but no valid GTFS zip file was found in the results.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not connect to the Open Data API. Reason: {e}")
        return None
    except KeyError:
        print("ERROR: The API response structure was not as expected. It may have changed.")
        return None

def download_and_extract(url):
    """
    Takes a URL, downloads the content, and extracts 'stops.txt'.
    """
    if not url:
        print("\nAborting download due to missing URL.")
        return

    print(f"\nDownloading data from the discovered URL...")
    try:
        headers = {'User-Agent': 'TTC Data Analysis Script (Python/Requests)'}
        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()
        print("Download complete.")

        print("Extracting 'stops.txt' from the zip file...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extract('stops.txt', path=TARGET_DIR)
            
        print("\n---------------- SUCCESS ----------------")
        print(f"The file 'stops.txt' has been saved to the '{TARGET_DIR}' folder.")

    except Exception as e:
        print(f"\nAn error occurred during download or extraction. Reason: {e}")


def main():
    """
    Main function to run the process.
    """
    print("--- TTC GTFS Stop Data Fetcher (Dynamic Search Version) ---")
    
    # Check if the file already exists
    if os.path.exists(STOPS_FILE_PATH):
        print(f"'{STOPS_FILE_PATH}' already exists. No action needed.")
        print("To get a fresh copy, delete the 'gtfs_data' folder and run this script again.")
        return

    # Create the target directory
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 1. Dynamically find the correct URL
    download_url = find_gtfs_download_url()
    
    # 2. Download and extract using the URL found
    download_and_extract(download_url)

# Run the script
if __name__ == "__main__":
    main()