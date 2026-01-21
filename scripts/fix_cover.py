import os
import requests
import urllib.parse
import difflib
import argparse

# Configuration
# Paths relative to project root
ROM_BASE = 'public/roms'
LOGO_BASE = 'public/logos'

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

def clean_name_for_url(filename):
    # Libretro uses replacements for specific chars: &*/:`<>?\| -> _
    # Ref: https://github.com/libretro-thumbnails/libretro-thumbnails#naming-conventions
    name = os.path.splitext(filename)[0]
    for char in '&*/:`<>?\|':
        name = name.replace(char, '_')
    return name

def download_file(url, save_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading: {e}")
    return False

def get_remote_file_list(libretro_system):
    # This is expensive/hard without GitHub API. 
    # For fuzzy matching locally, we simply try the Exact Name first.
    # If using --fuzzy, we might need a trusted list or index. 
    # For now, we implement a simple fuzzy strategy by trying modifications of the name.
    return []

def main():
    parser = argparse.ArgumentParser(description="Fix Cover Art for EmulatorJS")
    parser.add_argument("--system", help="Specific system to scan (e.g., nes, snes)", required=False)
    parser.add_argument("--fuzzy", help="Enable fuzzy matching (experimental)", action="store_true")
    args = parser.parse_args()

    systems_to_scan = [args.system] if args.system else SYSTEM_MAP_LIBRETRO.keys()

    for system in systems_to_scan:
        if system not in SYSTEM_MAP_LIBRETRO:
            print(f"Skipping unknown system: {system}")
            continue

        libretro_system = SYSTEM_MAP_LIBRETRO[system]
        rom_dir = os.path.join(ROM_BASE, system)
        logo_dir = os.path.join(LOGO_BASE, system)

        if not os.path.exists(rom_dir):
            if args.system: print(f"ROM directory not found: {rom_dir}")
            continue
        
        if not os.path.exists(logo_dir):
            os.makedirs(logo_dir)

        print(f"\nProcessing System: {system} -> {libretro_system}")

        for file in os.listdir(rom_dir):
            if file.startswith('.'): continue
            
            game_name = os.path.splitext(file)[0]
            # Convention: Logo name must match ROM name
            logo_path = os.path.join(logo_dir, game_name + ".png")
            
            if os.path.exists(logo_path):
                continue # Already exists
            
            # 1. Try Exact Match (with Special Char replacement)
            safe_name = clean_name_for_url(file)
            url_name = urllib.parse.quote(safe_name)
            url = f"https://raw.githubusercontent.com/libretro-thumbnails/{libretro_system}/master/Named_Boxarts/{url_name}.png"
            
            print(f"  [MISSING] {game_name}")
            print(f"    -> Trying: {url} ...", end=" ")
            
            if download_file(url, logo_path):
                print("OK")
            else:
                print("FAIL")
                if args.fuzzy:
                    # Very basic fuzzy: Try removing (...) brackets or regions
                    # E.g. "Mario (USA)" -> "Mario"
                    short_name = re.sub(r'\s*\(.*?\)', '', safe_name).strip()
                    if short_name != safe_name:
                         url_name = urllib.parse.quote(short_name)
                         url = f"https://raw.githubusercontent.com/libretro-thumbnails/{libretro_system}/master/Named_Boxarts/{url_name}.png"
                         print(f"    -> Retrying Fuzzy: {url} ...", end=" ")
                         if download_file(url, logo_path):
                             print("OK")
                         else:
                             print("FAIL")

if __name__ == "__main__":
    main()
