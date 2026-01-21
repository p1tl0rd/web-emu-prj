import os
import json
import urllib.parse
import re
import zlib
import argparse

# Configuration
# Default paths relative to project root
ROM_DIR = 'public/roms'
OUTPUT_FILE = 'public/data/gamelist.json'
COVER_MAP_FILE = 'cover_map.json'

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
    '.md': {'system': 'segaMD', 'core': 'genesis_plus_gx'},
    '.gen': {'system': 'segaMD', 'core': 'genesis_plus_gx'},
    '.gg': {'system': 'segaGG', 'core': 'genesis_plus_gx'},
    '.sms': {'system': 'segaMS', 'core': 'smsplus'},
    '.32x': {'system': 'sega32x', 'core': 'picodrive'},
    '.sat': {'system': 'segaSaturn', 'core': 'yabause'},
    '.cue': {'system': 'segaCD', 'core': 'genesis_plus_gx'}, # Collision with PSX
    
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
    '.zip': {'system': 'arcade', 'core': 'fbneo'}, # Generic arcade
    
    # Others
    '.3do': {'system': '3do', 'core': 'opera'},
    '.pce': {'system': 'pce', 'core': 'mednafen_pce'},
    '.sgx': {'system': 'pce', 'core': 'mednafen_pce'},
    '.ngp': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.ngc': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.ws': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.wsc': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.col': {'system': 'coleco', 'core': 'gearcoleco'},
    '.adf': {'system': 'amiga', 'core': 'puae'},
    '.d64': {'system': 'c64', 'core': 'vice_x64sc'},
    '.psp': {'system': 'psp', 'core': 'ppsspp'},
}

SYSTEM_MAP_LIBRETRO = {
    'nes': 'Nintendo_-_Nintendo_Entertainment_System',
    'snes': 'Nintendo_-_Super_Nintendo_Entertainment_System',
    'n64': 'Nintendo_-_Nintendo_64',
    'gb': 'Nintendo_-_Game_Boy',
    'gbc': 'Nintendo_-_Game_Boy_Color',
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
    'ngp': 'SNK_-_Neo_Geo_Pocket',
    'atari2600': 'Atari_-_2600',
    'arcade': 'FBNeo_-_Arcade_Games' 
}

def calculate_crc32(filepath):
    """Calculates the CRC32 checksum of a file."""
    prev = 0
    try:
        with open(filepath, 'rb') as f:
            for line in f:
                prev = zlib.crc32(line, prev)
        return "%08X" % (prev & 0xFFFFFFFF)
    except Exception as e:
        print(f"Error calculating CRC32 for {filepath}: {e}")
        return None

def scan_roms():
    game_list = []
    
    if not os.path.exists(ROM_DIR):
        print(f"Error: ROM Directory '{ROM_DIR}' not found. Please create it or run from project root.")
        return

    # Load Cover Map if exists
    cover_map = {}
    if os.path.exists(COVER_MAP_FILE):
        with open(COVER_MAP_FILE, 'r', encoding='utf-8') as f:
            cover_map = json.load(f)

    # Walk through the roms directory
    for root, dirs, files in os.walk(ROM_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            
            config = None
            
            # Special handling for ambiguous extensions
            if ext == '.bin':
                if 'psx' in root.lower() or 'playstation' in root.lower():
                    config = {'system': 'psx', 'core': 'pcsx_rearmed'}
                else:
                    config = {'system': 'segaMD', 'core': 'genesis_plus_gx'}
            elif ext == '.cue':
                 if 'psx' in root.lower() or 'playstation' in root.lower():
                    config = {'system': 'psx', 'core': 'pcsx_rearmed'}
                 else:
                    config = {'system': 'segaCD', 'core': 'genesis_plus_gx'}
            elif ext == '.zip':
                 if 'neogeo' in root.lower():
                    config = {'system': 'neogeo', 'core': 'fbneo'}
                 else:
                    config = {'system': 'arcade', 'core': 'fbneo'}
            elif ext in EXTENSIONS_MAP:
                config = EXTENSIONS_MAP[ext]
            
            if config:
                full_path = os.path.join(root, file)
                # Calculate paths relative to 'public/' because webroot is likely 'public' or project root
                # Assuming index.html is in root and data is in public/data, roms in public/roms.
                # If index.html is in root, then web paths to roms should be 'public/roms/...' OR if deployed to root of domain:
                # User report says: "public/roms/{system}/".
                # Standard practice for GitHub Pages: content of 'public' might be what is served?
                # Or 'public' is just a folder. 
                # Let's assume web path follows relative structure from index.html.
                # If index.html is in root, path is 'public/roms/nes/mario.nes'
                
                rel_path = os.path.relpath(full_path, start='.')
                web_path = rel_path.replace('\\', '/')
                
                game_id = file.replace('.', '_').replace(' ', '_').lower()
                
                raw_game_name = os.path.splitext(file)[0]
                clean_name = re.sub(r'\s*\(.*?\)', '', raw_game_name)
                clean_name = re.sub(r'\s*\[.*?\]', '', clean_name).strip()
                
                if ", The" in clean_name: clean_name = "The " + clean_name.replace(", The", "")
                if ", the" in clean_name: clean_name = "The " + clean_name.replace(", the", "")
                
                # Image Path Logic
                # Check local first: public/logos/{system}/{SameName}.png
                # We expect logo path to match ROM path filename exactly as per Convention 03.
                
                system_dir = config['system']
                logo_rel_path = f"public/logos/{system_dir}/{raw_game_name}.png" 
                
                image_path = logo_rel_path # Default to local expectation
                
                # If we want to fallback to remote URL in the JSON directly (not recommended by convention 03, but good for quick start)
                # Convention 03 says: "Ưu tiên repository libretro-thumbnails." when finding.
                # But JSON usually points to a valid URL.
                # Let's check if local exists.
                
                if not os.path.exists(logo_rel_path):
                     # Fallback to map or remote (optional, but requested in report to just generate list)
                     if raw_game_name in cover_map:
                         image_path = cover_map[raw_game_name]
                     elif config['system'] in SYSTEM_MAP_LIBRETRO:
                         libretro_system = SYSTEM_MAP_LIBRETRO[config['system']]
                         safe_name = urllib.parse.quote(raw_game_name)
                         image_path = f"https://raw.githubusercontent.com/libretro-thumbnails/{libretro_system}/master/Named_Boxarts/{safe_name}.png"
                
                # CRC32
                crc = calculate_crc32(full_path)

                entry = {
                    "id": game_id,
                    "name": clean_name,
                    "system": config['system'],
                    "rom_path": web_path,
                    "core": config['core'],
                    "image": image_path,
                    "crc32": crc
                }
                
                game_list.append(entry)
                print(f"Added: {clean_name} ({config['system']})")

    # Write to JSON
    output_dir = os.path.dirname(OUTPUT_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(game_list, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccessfully generated {OUTPUT_FILE} with {len(game_list)} games.")

if __name__ == "__main__":
    scan_roms()
