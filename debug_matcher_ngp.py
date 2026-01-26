import requests
import difflib
import re
import os

# CONFIG
repo_name = "SNK_-_Neo_Geo_Pocket"
test_filename = "Last Blade, The (UE) [!].npc"

GITHUB_API = f"https://api.github.com/repos/libretro-thumbnails/{repo_name}/git/trees/master?recursive=1"

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[\(\[].*?[\)\]]', '', name)
    name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    return name.strip().lower()

print(f"Fetching file list for {repo_name}...")
resp = requests.get(GITHUB_API)
if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    exit()
    
data = resp.json()
remote_files = []
clean_map = {}

if 'tree' in data:
    for item in data['tree']:
        if item['path'].startswith('Named_Boxarts/') and item['path'].endswith('.png'):
            fname = os.path.basename(item['path'])
            remote_files.append(fname)
            cname = clean_filename(fname)
            clean_map[cname] = fname

print(f"Remote files found: {len(remote_files)}")

# Local Clean
raw_search = clean_filename(test_filename)
print(f"Search (Cleaned): '{raw_search}'")

# 1. Exact Clean Match
if raw_search in clean_map:
    print(f"✅ EXACT MATCH FOUND: {clean_map[raw_search]}")
else:
    print("❌ No Exact Match.")

# 2. Fuzzy Match
print("\n--- Fuzzy Candidates ---")
matches = difflib.get_close_matches(raw_search, clean_map.keys(), n=5, cutoff=0.1)
for m in matches:
    print(f"Candidate: '{m}' -> File: {clean_map[m]} (Ratio: {difflib.SequenceMatcher(None, raw_search, m).ratio():.2f})")
