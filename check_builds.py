import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_URL = "https://buildbot.libretro.com/nightly/android/"

def extract_and_download_apks(page_url, target_folder="downloaded_apks"):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    print(f"Connecting to website: {page_url}...")
    try:
        response = requests.get(page_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing website: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    dated_files = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.apk'):
            # Filter files starting with the current year
            if href.startswith("2026-"):
                dated_files.append(href)

    if not dated_files:
        print("No dated APK files found for 2026.")
        return None

    # Sort files chronologically and pick the latest one
    dated_files.sort()
    latest_file = dated_files[-1]
    latest_date_str = latest_file[:10]
    print(f"Latest build date detected: {latest_date_str}")

    # Define the three target variants requested
    targets = {
        "universal": f"{latest_date_str}-RetroArch.apk",
        "arm64": f"{latest_date_str}-RetroArch_aarch64.apk",
        "arm32": f"{latest_date_str}-RetroArch_ra32.apk"
    }

    downloaded_any = False
    for arch, file_name in targets.items():
        download_url = urljoin(page_url, file_name)
        save_path = os.path.join(target_folder, file_name)
        print(f"Downloading ({arch}): {file_name}...")
        
        try:
            with requests.get(download_url, stream=True) as r:
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Successfully downloaded: {file_name}")
                    downloaded_any = True
                else:
                    print(f"File not found on server: {file_name}")
        except Exception as e:
            print(f"Error downloading {file_name}: {e}")

    # Save tag directly to GitHub Environment file if running in Actions
    if downloaded_any and "GITHUB_ENV" in os.environ:
        with open(os.environ["GITHUB_ENV"], "a") as env_file:
            env_file.write(f"RELEASE_TAG={latest_date_str}\n")
        print(f"Saved RELEASE_TAG={latest_date_str} to GITHUB_ENV.")

    return latest_date_str if downloaded_any else None

if __name__ == "__main__":
    extract_and_download_apks(TARGET_URL)
