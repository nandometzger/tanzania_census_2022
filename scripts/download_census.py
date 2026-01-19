import requests
import os

def download_file(url, local_filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Ensure directory exists
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    
    print(f"Downloading {url} to {local_filename}...")
    try:
        # Use verify=False due to potential SSL certificate issues on some government portals
        with requests.get(url, headers=headers, stream=True, verify=False) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        print(f"Successfully downloaded: {local_filename}")
        print(f"Final Size: {os.path.getsize(local_filename)} bytes")
    except Exception as e:
        print(f"Failed to download: {e}")

if __name__ == "__main__":
    url = "https://www.nbs.go.tz/uploads/statistics/documents/en-1705484562-Administrative_units_Population_Distribution_Report_Tanzania_volume1a.pdf"
    
    # Path relative to project root
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(ROOT, "data", "raw", "TZA_2022_Census_Vol1A.pdf")
    
    download_file(url, output_path)
