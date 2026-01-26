import os
import json
import urllib.parse
import re
import requests
import difflib
import time

# --- Configuration ---
ROM_DIR = 'roms'
ASSETS_DIR = 'assets'
OUTPUT_FILE = 'gamelist.json'

GITHUB_API_BASE = "https://api.github.com/repos/libretro-thumbnails"
RAW_BASE_URL = "https://raw.githubusercontent.com/libretro-thumbnails"
MATCH_THRESHOLD = 0.6

# Local Extensions -> System ID & Core
EXTENSIONS_MAP = {
    # Nintendo
    '.nes': {'system': 'nes', 'core': 'fceumm'},
    '.sfc': {'system': 'snes', 'core': 'snes9x'},
    '.smc': {'system': 'snes', 'core': 'snes9x'},
    '.gba': {'system': 'gba', 'core': 'mgba'},
    '.gb': {'system': 'gb', 'core': 'gambatte'},
    '.gbc': {'system': 'gbc', 'core': 'gambatte'},
    '.vb': {'system': 'vb', 'core': 'beetle_vb'},
    '.nds': {'system': 'nds', 'core': 'melonds'},
    '.z64': {'system': 'n64', 'core': 'mupen64plus_next'},
    '.n64': {'system': 'n64', 'core': 'mupen64plus_next'},
    '.v64': {'system': 'n64', 'core': 'mupen64plus_next'},
    
    # SEGA
    '.md': {'system': 'segaMD', 'core': 'segaMD'},
    '.gen': {'system': 'segaMD', 'core': 'segaMD'},
    '.gg': {'system': 'segaGG', 'core': 'genesis_plus_gx'},
    '.sms': {'system': 'segaMS', 'core': 'smsplus'},
    '.32x': {'system': 'sega32x', 'core': 'picodrive'},
    '.sat': {'system': 'segaSaturn', 'core': 'yabause'},
    '.cue': {'system': 'segaCD', 'core': 'genesis_plus_gx'}, 
    
    # PlayStation
    '.iso': {'system': 'psx', 'core': 'pcsx_rearmed'},
    '.chd': {'system': 'psx', 'core': 'pcsx_rearmed'},
    '.pbp': {'system': 'psx', 'core': 'pcsx_rearmed'},
    '.mcr': {'system': 'psx', 'core': 'pcsx_rearmed'},
    
    # Atari
    '.a26': {'system': 'atari2600', 'core': 'stella2014'},
    '.a78': {'system': 'atari7800', 'core': 'prosystem'},
    '.a52': {'system': 'atari5200', 'core': 'a5200'},
    '.lnx': {'system': 'lynx', 'core': 'handy'},
    '.j64': {'system': 'jaguar', 'core': 'virtualjaguar'},
    
    # Arcade
    '.zip': {'system': 'arcade', 'core': 'fbneo'},
    
    # Others
    '.3do': {'system': '3do', 'core': 'opera'},
    '.pce': {'system': 'pce', 'core': 'mednafen_pce'},
    '.sgx': {'system': 'pce', 'core': 'mednafen_pce'},
    '.ngp': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.ngc': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.npc': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.ws': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.wsc': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.col': {'system': 'coleco', 'core': 'gearcoleco'},
    '.adf': {'system': 'amiga', 'core': 'puae'},
    '.d64': {'system': 'c64', 'core': 'vice_x64sc'},
    '.psp': {'system': 'psp', 'core': 'ppsspp'},
}

# System ID -> Libretro Repo Name (or List of Names)
SYSTEM_TO_REPO_MAP = {
    'nes': 'Nintendo_-_Nintendo_Entertainment_System',
    'snes': 'Nintendo_-_Super_Nintendo_Entertainment_System',
    'n64': 'Nintendo_-_Nintendo_64',
    'gb': ['Nintendo_-_Game_Boy', 'Nintendo_-_Game_Boy_Color'], # Fallback for dual compatible
    'gbc': ['Nintendo_-_Game_Boy_Color', 'Nintendo_-_Game_Boy'],
    'gba': 'Nintendo_-_Game_Boy_Advance',
    'nds': 'Nintendo_-_Nintendo_DS',
    'vb': 'Nintendo_-_Virtual_Boy',
    'segaMD': 'Sega_-_Mega_Drive_-_Genesis',
    'segaMS': 'Sega_-_Master_System_-_Mark_III',
    'segaGG': 'Sega_-_Game_Gear',
    'segaCD': 'Sega_-_Mega-CD_-_Sega_CD',
    'sega32x': 'Sega_-_32X',
    'psx': 'Sony_-_PlayStation',
    'psp': 'Sony_-_PlayStation_Portable',
    'neogeo': 'SNK_-_Neo_Geo',
    'ngp': ['SNK_-_Neo_Geo_Pocket_Color', 'SNK_-_Neo_Geo_Pocket'], # Search both
    'atari2600': 'Atari_-_2600',
    'arcade': 'FBNeo_-_Arcade_Games' 
}

# --- Caching ---
_repo_cache = {} # repo_name -> {'files': [], 'clean_map': {}}

# --- Helpers ---

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[\(\[].*?[\)\]]', '', name)
    name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    return name.strip().lower()

def get_repo_data_cached(repo_name):
    if repo_name in _repo_cache:
        return _repo_cache[repo_name]
    
    print(f"  [API] Fetching file list for {repo_name}...")
    url = f"{GITHUB_API_BASE}/{repo_name}/git/trees/master?recursive=1"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            files = []
            clean_map = {}
            if 'tree' in data:
                for item in data['tree']:
                    path = item['path']
                    if path.startswith('Named_Boxarts/') and path.endswith('.png'):
                        fname = os.path.basename(path)
                        files.append(fname)
                        # Pre-calc clean name
                        cname = clean_filename(fname)
                        clean_map[cname] = fname
                        
            print(f"  [API] Found {len(files)} covers.")
            cache_data = {'files': files, 'clean_map': clean_map}
            _repo_cache[repo_name] = cache_data
            return cache_data
        elif response.status_code == 403:
             print("  [API] rate limit exceeded (60 req/hr).")
             _repo_cache[repo_name] = None
             return None
        else:
             print(f"  [API] Error {response.status_code}")
             _repo_cache[repo_name] = None
             return None
    except Exception as e:
        print(f"  [API] Exception: {e}")
        _repo_cache[repo_name] = None
        return None

def download_file(repo_name, filename, save_path):
    safe_name = urllib.parse.quote(filename)
    url = f"{RAW_BASE_URL}/{repo_name}/master/Named_Boxarts/{safe_name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        pass
    return False

def get_smart_cover(system_id, raw_filename, asset_rel_path):
    """
    Attempts to find and download a cover if local one is missing.
    Returns: Path to image (local) if success, or None.
    """
    # 1. Check if we already have it locally
    base_asset_path = os.path.splitext(asset_rel_path)[0] # remove default .png
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        check_path = base_asset_path + ext
        if os.path.exists(check_path):
            return check_path.replace('\\', '/')

    # 2. Not found? Try Smart Download
    repo_entries = SYSTEM_TO_REPO_MAP.get(system_id)
    if not repo_entries:
        return None  
    
    # Normalize to list
    if isinstance(repo_entries, str):
        repos = [repo_entries]
    else:
        repos = repo_entries
        
    for repo_name in repos:
        repo_data = get_repo_data_cached(repo_name)
        if not repo_data:
            continue
        
        clean_map = repo_data['clean_map']
        clean_search = clean_filename(raw_filename)
        match_filename = None
        
        # A. Exact Clean Match
        if clean_search in clean_map:
            match_filename = clean_map[clean_search]
            print(f"    -> [Matches] Found Exact Clean in {repo_name}: {match_filename}")
        else:
            # B. Fuzzy Clean Match
            matches = difflib.get_close_matches(clean_search, clean_map.keys(), n=1, cutoff=MATCH_THRESHOLD)
            if matches:
                best_clean = matches[0]
                match_filename = clean_map[best_clean]
                print(f"    -> [Matches] Found Fuzzy in {repo_name}: {match_filename} (from '{best_clean}')")

        if match_filename:
            target_path = asset_rel_path
            if download_file(repo_name, match_filename, target_path):
                time.sleep(0.1) # Politeness
                return target_path.replace('\\', '/')
            else:
                print("    -> [Download] Failed.")
                # Don't break immediately, maybe found in next match? (Unlikely if one failed, but safe to continue or return None)
                continue 

    return None


def scan_roms():
    game_list = []
    
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    # Load Cover Map
    cover_map = {}
    if os.path.exists('cover_map.json'):
         with open('cover_map.json', 'r', encoding='utf-8') as f:
             cover_map = json.load(f)

    # Scan
    for root, dirs, files in os.walk(ROM_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            config = None
            
            # Special Handling (copied from original)
            if ext == '.bin':
                if 'psx' in root.lower() or 'playstation' in root.lower(): config = {'system': 'psx', 'core': 'pcsx_rearmed'}
                else: config = {'system': 'segaMD', 'core': 'segaMD'}
            elif ext == '.cue':
                 if 'psx' in root.lower() or 'playstation' in root.lower(): config = {'system': 'psx', 'core': 'pcsx_rearmed'}
                 else: config = {'system': 'segaCD', 'core': 'genesis_plus_gx'}
            elif ext == '.zip':
                 if 'neogeo' in root.lower(): config = {'system': 'neogeo', 'core': 'fbneo'}
                 else: config = {'system': 'arcade', 'core': 'fbneo'}
            elif ext in EXTENSIONS_MAP:
                config = EXTENSIONS_MAP[ext]
            
            if config:
                full_path = os.path.join(root, file)
                web_path = os.path.relpath(full_path, start='.').replace('\\', '/')
                
                game_id = file.replace('.', '_').replace(' ', '_').lower()
                raw_name = os.path.splitext(file)[0]
                
                # Display Name
                clean_name = re.sub(r'\s*\(.*?\)', '', raw_name)
                clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
                clean_name = clean_name.strip()
                if ", The" in clean_name: clean_name = "The " + clean_name.replace(", The", "")
                if ", the" in clean_name: clean_name = "The " + clean_name.replace(", the", "")

                # Image Logic
                image_path = "assets/default.png"
                
                # Manual Override Map check
                if raw_name in cover_map:
                    image_path = cover_map[raw_name]
                else:
                    # Determine where asset should be
                    subfolder = os.path.relpath(root, ROM_DIR)
                    if subfolder == '.': subfolder = ''
                    
                    # We usually want assets/<system>/name.png
                    # But the structure suggests assets/gba/name.png if roms/gba/name.gba
                    # Let's trust subfolder structure matches
                    
                    # Fallback asset path (where we want to save it)
                    target_asset_path = os.path.join(ASSETS_DIR, subfolder, raw_name + ".png")
                    
                    # Smart Check & Download
                    found_asset = get_smart_cover(config['system'], file, target_asset_path)
                    
                    if found_asset:
                        image_path = found_asset
                    else:
                        # Final Fallback to Remote URL (Old logic) - Only if really needed
                        # The user seems to prefer local DL. If failed, just keep default or generate a link?
                        # Generating a blind link is risky if file doesn't exist. 
                        # Let's generate the link as a last resort if we have a repo map.
                        if config['system'] in SYSTEM_TO_REPO_MAP:
                             repo = SYSTEM_TO_REPO_MAP[config['system']]
                             safe_name = urllib.parse.quote(raw_name)
                             # image_path = f"{RAW_BASE_URL}/{repo}/master/Named_Boxarts/{safe_name}.png"
                             # Commented out: Prefer default.png than broken link if Fuzzy search failed.
                             pass

                entry = {
                    "id": game_id,
                    "name": clean_name,
                    "system": config['system'],
                    "rom_path": web_path,
                    "core": config['core'],
                    "image": image_path
                }
                game_list.append(entry)
                # print(f"  Processed: {clean_name}")

    if game_list:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(game_list, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully generated {OUTPUT_FILE} with {len(game_list)} games.")
    else:
        print("No games found.")

if __name__ == "__main__":
    scan_roms()
