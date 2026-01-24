import os
import json
import urllib.parse
import re

# Configuration
ROM_DIR = 'roms'
OUTPUT_FILE = 'gamelist.json'
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
    '.md': {'system': 'segaMD', 'core': 'picodrive'},
    '.gen': {'system': 'segaMD', 'core': 'picodrive'},
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
    '.npc': {'system': 'ngp', 'core': 'mednafen_ngp'},
    '.ws': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.wsc': {'system': 'wswan', 'core': 'mednafen_wswan'},
    '.col': {'system': 'coleco', 'core': 'gearcoleco'},
    '.adf': {'system': 'amiga', 'core': 'puae'},
    '.d64': {'system': 'c64', 'core': 'vice_x64sc'},
    '.psp': {'system': 'psp', 'core': 'ppsspp'},
}

def scan_roms():
    game_list = []
    
    # Walk through the roms directory
    for root, dirs, files in os.walk(ROM_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            
            config = None
            
            # Special handling for ambiguous extensions
            if ext == '.bin':
                # Check path for 'psx' or 'playstation'
                if 'psx' in root.lower() or 'playstation' in root.lower():
                    config = {'system': 'psx', 'core': 'pcsx_rearmed'}
                else:
                    # Default to Sega Genesis/Mega Drive
                    config = {'system': 'segaMD', 'core': 'picodrive'}
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
                # Get relative path for web
                # Replace Windows backslashes with slashes
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start='.')
                web_path = rel_path.replace('\\', '/')
                
                # Generate specific ID (simple hash based on filename)
                game_id = file.replace('.', '_').replace(' ', '_').lower()
                
                # Raw Game Name (Filename without extension) - Used for Image Matching
                raw_game_name = os.path.splitext(file)[0]

                # Clean Game Name (For Display) - Remove (...) and [...]
                clean_name = re.sub(r'\s*\(.*?\)', '', raw_game_name)
                clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
                clean_name = clean_name.strip()
                
                # Fix "Name, The" -> "The Name" for Display Name
                if ", The" in clean_name:
                     clean_name = "The " + clean_name.replace(", The", "")
                if ", the" in clean_name:
                     clean_name = "The " + clean_name.replace(", the", "")
                                
                # Image Detection -> Remote URL
                # Logic: Construct direct GitHub URL to Libretro Thumbnails
                
                # Image Detection -> Remote URL
                # Logic: Construct direct GitHub URL to Libretro Thumbnails
                
                # Load Cover Map if exists
                cover_map = {}
                if os.path.exists('cover_map.json'):
                    with open('cover_map.json', 'r', encoding='utf-8') as f:
                        cover_map = json.load(f)

                # Revert to Raw Name for URL because Libretro uses No-Intro naming (with tags)
                # Example: "Legend of Zelda, The - Majora's Mask (USA).png"
                # So we must use raw_game_name (which is just filename without extension)
                url_name = raw_game_name


                # Mapping local folder names to Libretro Repository Names
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
                
                # Get subfolder path relative to ROM_DIR (Needed for Local Asset check)
                subfolder = os.path.relpath(root, ROM_DIR)
                if subfolder == '.': subfolder = ''
                
                # Check for local override first
                image_path = "assets/default.png"
                local_asset_found = False
                
                # Check Local Assets first (in case user wants custom cover)
                for img_ext in ['.png', '.jpg', '.jpeg', '.webp']:
                    potential_img_rel = os.path.join('assets', subfolder, raw_game_name + img_ext)
                    if os.path.exists(potential_img_rel):
                        image_path = potential_img_rel.replace('\\', '/')
                        local_asset_found = True
                        break
                
                # If no local asset, use Remote URL
                # If no local asset, check Cover Map or use Remote URL
                if not local_asset_found:
                    if raw_game_name in cover_map:
                         image_path = cover_map[raw_game_name]
                         print(f"  -> Using mapped cover for: {raw_game_name}")
                    elif config['system'] in SYSTEM_MAP_LIBRETRO:
                        libretro_system = SYSTEM_MAP_LIBRETRO[config['system']]
                        # Use the raw url_name for the link to match Libretro
                        safe_name = urllib.parse.quote(url_name)
                        image_path = f"https://raw.githubusercontent.com/libretro-thumbnails/{libretro_system}/master/Named_Boxarts/{safe_name}.png"
                
                entry = {
                    "id": game_id,
                    "name": clean_name, # Use cleaned name
                    "system": config['system'],
                    "rom_path": web_path,
                    "core": config['core'],
                    "image": image_path
                }
                
                game_list.append(entry)
                print(f"Found: {clean_name} ({config['system']})")

    # Write to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(game_list, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccessfully generated {OUTPUT_FILE} with {len(game_list)} games.")

if __name__ == "__main__":
    if not os.path.exists(ROM_DIR):
        print(f"Error: Directory '{ROM_DIR}' not found.")
    else:
        scan_roms()
