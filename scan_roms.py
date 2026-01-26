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
    'atari7800': 'Atari_-_7800', 
    'arcade': 'FBNeo_-_Arcade_Games' 
}

# Manual Mapping for Arcade/NeoGeo abbreviations
ARCADE_NAMES = {
    'mslug': 'Metal Slug - Super Vehicle-001',
    'mslug2': 'Metal Slug 2 - Super Vehicle-001/II',
    'mslugx': 'Metal Slug X - Super Vehicle-001',
    'mslug3': 'Metal Slug 3',
    'mslug4': 'Metal Slug 4',
    'mslug5': 'Metal Slug 5',
    'kof94': 'The King of Fighters \'94',
    'kof95': 'The King of Fighters \'95',
    'kof96': 'The King of Fighters \'96',
    'kof97': 'The King of Fighters \'97',
    'kof98': 'The King of Fighters \'98 - The Slugfest',
    'kof99': 'The King of Fighters \'99 - Millennium Battle',
    'kof2000': 'The King of Fighters 2000',
    'kof2001': 'The King of Fighters 2001',
    'kof2002': 'The King of Fighters 2002 - Challenge to Ultimate Battle',
    'kof2003': 'The King of Fighters 2003',
    'samsho': 'Samurai Shodown',
    'samsho2': 'Samurai Shodown II',
    'samsho3': 'Samurai Shodown III',
    'samsho4': 'Samurai Shodown IV - Amakusa\'s Revenge',
    'samsho5': 'Samurai Shodown V',
    'lastblad': 'The Last Blade',
    'lastbld2': 'The Last Blade 2',
    'garou': 'Garou - Mark of the Wolves',
    'fatfury1': 'Fatal Fury - King of Fighters',
    'fatfury2': 'Fatal Fury 2',
    'fatfursp': 'Fatal Fury Special',
    'rbff1': 'Real Bout Fatal Fury',
    'rbff2': 'Real Bout Fatal Fury 2 - The Newcomers',
    'rbffspec': 'Real Bout Fatal Fury Special',
    'svc': 'SNK vs. Capcom - SVC Chaos',
    'neogeo': 'Neo Geo BIOS' 
}

# --- Caching ---
_repo_cache = {} # repo_name -> {'files': [], 'clean_map': {}}

# --- Helpers ---

def clean_filename(filename):
    # check if plain filename (without extension) is in our arcade map
    name_no_ext = os.path.splitext(filename)[0].lower()
    if name_no_ext in ARCADE_NAMES:
        return ARCADE_NAMES[name_no_ext].lower()

    name = os.path.splitext(filename)[0]
    name = re.sub(r'[\(\[].*?[\)\]]', '', name)
    name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    return name.strip().lower()

def get_repo_data_cached(repo_name):
    if repo_name in _repo_cache:
        return _repo_cache[repo_name]
    
    print(f"  [API] Fetching file list for {repo_name}...")
    # Use recursive tree to get all files
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
                    # Libretro structure: Named_Boxarts/Game Name.png
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

def download_file(repo_name, filename, save_path, depth=0):
    if depth > 3: # Prevention for circular symlinks
        print(f"    -> [Error] Too many symlink jumps for {filename}")
        return False

    safe_name = urllib.parse.quote(filename)
    url = f"{RAW_BASE_URL}/{repo_name}/master/Named_Boxarts/{safe_name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.content
            
            # Check if it's a PNG or a Symlink (text file pointing to another .png)
            if content.startswith(b'\x89PNG'):
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(content)
                return True
            else:
                # Might be a symlink text
                try:
                    link_target = content.decode('utf-8').strip()
                    if link_target.endswith('.png'):
                        print(f"    -> [Link] Following symlink: {filename} -> {link_target}")
                        return download_file(repo_name, link_target, save_path, depth + 1)
                except:
                    pass
                
                print(f"    -> [Error] Content is not a PNG for {filename}")
    except Exception as e:
        print(f"    -> [Exception] Download error: {e}")
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
            # Check if valid file (not corrupted/text)
            if os.path.getsize(check_path) > 200:
                return check_path.replace('\\', '/')

    # 2. Not found? Try Smart Download
    repo_entries = SYSTEM_TO_REPO_MAP.get(system_id)
    if not repo_entries:
        return None  
    
    # Normalize to list
    repos = [repo_entries] if isinstance(repo_entries, str) else repo_entries
        
    for repo_name in repos:
        repo_data = get_repo_data_cached(repo_name)
        if not repo_data: continue
        
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
            else:
                # C. Substring/Prefix Fallback (For titles like "The Last Blade" vs "Last Blade, The...")
                # We check if clean_search is IN the clean_remote or vice versa
                for c_remote, r_file in clean_map.items():
                    if clean_search in c_remote or c_remote in clean_search:
                        # Only accept if they are reasonably similar or one contains the other significantly
                        if len(clean_search) > 5 and len(c_remote) > 5:
                             match_filename = r_file
                             print(f"    -> [Matches] Found Substring in {repo_name}: {match_filename}")
                             break

        if match_filename:
            if download_file(repo_name, match_filename, asset_rel_path):
                time.sleep(0.1) # Politeness
                return asset_rel_path.replace('\\', '/')
            
    return None

def cleanup_corrupted_assets():
    """Delete files < 200 bytes in assets/ as they are likely corrupted symlinks."""
    if not os.path.exists(ASSETS_DIR): return
    print("--- Cleaning up corrupted assets ---")
    count = 0
    for root, dirs, files in os.walk(ASSETS_DIR):
        for f in files:
            path = os.path.join(root, f)
            if os.path.isfile(path) and os.path.getsize(path) < 200:
                try:
                    os.remove(path)
                    count += 1
                except:
                    pass
    if count > 0:
        print(f"  Deleted {count} corrupted files.")


def scan_roms():
    game_list = []
    
    cleanup_corrupted_assets()
    
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
                
                # Determine display name
                display_name = raw_name
                
                # Try to resolve arcade name for better display
                name_key = display_name.lower()
                if name_key in ARCADE_NAMES:
                    display_name = ARCADE_NAMES[name_key]
                else:
                    clean_display = re.sub(r'\s*\(.*?\)', '', display_name)
                    clean_display = re.sub(r'\s*\[.*?\]', '', clean_display)
                    display_name = clean_display.strip()

                
                game_entry = {
                    "id": f"{config['system']}_{display_name.replace(' ', '_').replace('/', '')}", # unique id
                    "name": display_name,
                    "system": config['system'],
                    "rom_path": web_path,
                    "core": config['core'],
                    "image": "assets/default.png" # Default
                }
                
                # Check for cover override
                if raw_name in cover_map:
                     game_entry["image"] = cover_map[raw_name]
                else:
                    # Smart Cover Discovery
                    system_dir = os.path.join(ASSETS_DIR, config['system'])
                    if not os.path.exists(system_dir): os.makedirs(system_dir)
                    
                    # If we have a resolved name, use it for the asset filename too to match repo
                    asset_filename = display_name if display_name != raw_name else raw_name
                    # Sanitize for filesystem
                    asset_filename = re.sub(r'[^a-zA-Z0-9\s\-\.]', '', asset_filename) + ".png"
                    
                    asset_rel_path = os.path.join(ASSETS_DIR, config['system'], asset_filename)
                    
                    found_cover = get_smart_cover(config['system'], file, asset_rel_path)
                    
                    if found_cover:
                        game_entry["image"] = found_cover
                    else:
                        print(f"[Cover] Missing for {file} ({config['system']})")
                
                game_list.append(game_entry)

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(game_list, f, indent=4)
        print(f"\nSuccessfully generated {OUTPUT_FILE} with {len(game_list)} games.")

if __name__ == '__main__':
    scan_roms()
