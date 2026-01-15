---
trigger: always_on
---

2. Project Structure
*   **ROM Loading**: ROMs are loaded locally from `roms/system/game.ext`.
*   **Core Loading**: Emulator core files are loaded locally from `data/`.
*   **Firebase**: Configuration is in `js/firebase-config.js`. Do NOT overwrite user's API credentials with placeholders if they are already set.

3. Deployment
*   Use `python -m http.server 8000` for local testing to satisfy COOP/COEP security headers (handled by `coi-serviceworker.js`).