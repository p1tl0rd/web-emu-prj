import os
import requests
import json

# Config
CDN_BASE = "https://cdn.emulatorjs.org/latest/data/cores"
LOCAL_CORES_DIR = "data/cores"
GAMELIST = "gamelist.json"

def download_file(url, path):
    print(f"Downloading {url} -> {path}...")
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Done.")
            return True
        else:
            print(f"Failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    if not os.path.exists(LOCAL_CORES_DIR):
        print(f"Error: {LOCAL_CORES_DIR} does not exist.")
        return

    # Get list of required cores from gamelist
    required_cores = set()
    if os.path.exists(GAMELIST):
        try:
            with open(GAMELIST, 'r', encoding='utf-8') as f:
                games = json.load(f)
                for g in games:
                    if 'core' in g:
                        required_cores.add(g['core'])
        except Exception as e:
            print(f"Error reading gamelist: {e}")
    
    print(f"Required Cores: {required_cores}")

    for core in required_cores:
        # Try different naming conventions
        # Based on local files being named like "mgba-wasm.data", the wasm is likely "mgba-wasm.wasm"
        candidates = [
            f"{core}-wasm.wasm",
            f"{core}.wasm",
            f"{core}_libretro.wasm"
        ]
        
        success = False
        for filename in candidates:
            local_path = os.path.join(LOCAL_CORES_DIR, filename)
            url = f"{CDN_BASE}/{filename}"
            
            # Check if we already have it (optional, but good for speed)
            if os.path.exists(local_path):
                 print(f"Exists: {filename}")
                 success = True
                 break

            if download_file(url, local_path):
                success = True
                break
        
        if not success:
            print(f"FAILED to find core: {core}")

if __name__ == "__main__":
    main()
