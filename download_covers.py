import os
import requests
import re
import urllib.parse
import time

# Configuration
ROM_DIR = 'roms'
ASSETS_DIR = 'assets'

# Mapping local folder names to Libretro Repository Names
# URL Format: https://raw.githubusercontent.com/libretro-thumbnails/{SYSTEM_NAME}/master/Named_Boxarts/{GAME_NAME}.png
SYSTEM_MAP = {
    'nes': 'Nintendo_-_Nintendo_Entertainment_System',
    'snes': 'Nintendo_-_Super_Nintendo_Entertainment_System',
    'n64': 'Nintendo_-_Nintendo_64',
    'gb': 'Nintendo_-_Game_Boy',
    'gbc': 'Nintendo_-_Game_Boy_Color',
    'gba': 'Nintendo_-_Game_Boy_Advance',
    'nds': 'Nintendo_-_Nintendo_DS',
    'vb': 'Nintendo_-_Virtual_Boy',
    
    'sega_md': 'Sega_-_Mega_Drive_-_Genesis',
    'sega_ms': 'Sega_-_Master_System_-_Mark_III',
    'sega_gg': 'Sega_-_Game_Gear',
    'sega_cd': 'Sega_-_Mega-CD_-_Sega_CD',
    'sega_32x': 'Sega_-_32X',
    
    'psx': 'Sony_-_PlayStation',
    'psp': 'Sony_-_PlayStation_Portable',
    
    'neogeo': 'SNK_-_Neo_Geo',
    'ngp': 'SNK_-_Neo_Geo_Pocket',
    
    'atari2600': 'Atari_-_2600',
    'arcade': 'FBNeo_-_Arcade_Games' 
}

def clean_name_for_url(filename):
    # Libretro chars to replace: &*/:<>?\| with _
    # But usually, just cleaning the extension is enough for the base check
    name = os.path.splitext(filename)[0]
    
    # URL Encode special chars (like spaces becomes %20, but Libretro usually uses spaces)
    # Actually Libretro raw urls use normal encoding. 
    # Important: Libretro filenames usually match No-Intro.
    # e.g. "Super Mario Bros. 3 (USA)" -> "Super Mario Bros. 3 (USA).png"
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

def main():
    print("--- RetroCloud Cover Art Downloader ---")
    print("Source: Libretro Thumbnails (GitHub)")
    
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    for local_system, libretro_system in SYSTEM_MAP.items():
        rom_system_path = os.path.join(ROM_DIR, local_system)
        asset_system_path = os.path.join(ASSETS_DIR, local_system)
        
        if not os.path.exists(rom_system_path):
            continue
            
        if not os.path.exists(asset_system_path):
            os.makedirs(asset_system_path)
            
        print(f"\nScanning: {local_system} -> {libretro_system}")
        
        for file in os.listdir(rom_system_path):
            if file.endswith(('.txt', '.db')): continue
            
            # Check if image already exists
            game_name = os.path.splitext(file)[0]
            img_path = os.path.join(asset_system_path, game_name + ".png")
            
            if os.path.exists(img_path):
                print(f"  [SKIP] {game_name} (Exists)")
                continue
                
            # Construct URL
            # Url format: https://raw.githubusercontent.com/libretro-thumbnails/{Repo}/master/Named_Boxarts/{Name}.png
            # Special chars handling for URL
            safe_name = urllib.parse.quote(game_name)
            # Libretro replaces some chars with _ in filenames mostly on filesystem, but raw URL should handle standard encoding
            # However, quotes " might differ. Let's try direct map first.
            
            url = f"https://raw.githubusercontent.com/libretro-thumbnails/{libretro_system}/master/Named_Boxarts/{safe_name}.png"
            
            print(f"  [DOWNLOADING] {game_name}...", end=" ")
            if download_file(url, img_path):
                print("OK!")
            else:
                print("Not Found (404)")
                # Optional: Try fuzzy or removing brackets? 
                # For now let's keep it simple. If not found, user manually fixes name.

if __name__ == "__main__":
    main()
