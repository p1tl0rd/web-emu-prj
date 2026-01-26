import { db, ref, set, get, child, push, onValue } from './firebase-config.js';


// DOM Elements
const profileSelect = document.getElementById('profile-select');
const createProfileBtn = document.getElementById('create-profile-btn');
const guestBtn = document.getElementById('guest-btn');
const createProfileView = document.getElementById('create-profile-view'); // Kept for legacy ref if needed, but mostly unused now
const activeProfileView = document.getElementById('active-profile-view');
const profileSelectorView = document.getElementById('profile-selector-view');
const newProfileNameInput = document.getElementById('new-profile-name');
const confirmCreateProfileBtn = document.getElementById('confirm-create-profile');
const cancelCreateProfileBtn = document.getElementById('cancel-create-profile');
const profileNameDisplay = document.getElementById('profile-name-display');
const switchProfileBtn = document.getElementById('switch-profile-btn');

const welcomeMessage = document.getElementById('welcome-message');
// const gameListDiv = document.getElementById('game-list'); // Removed
const gameSelection = document.getElementById('game-selection');
const emulatorContainer = document.getElementById('emulator-container');
const backBtn = document.getElementById('back-btn');

let currentProfile = null; // { id: "string", name: "string" }
let currentGameConfig = null;

// --- Dev Helper: Force Update ---
window.forceUpdate = () => {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function (registrations) {
            for (let registration of registrations) {
                registration.unregister();
            }
            window.location.reload();
        });
    } else {
        window.location.reload();
    }
};

// Debug Error Handler for Mobile
window.onerror = function (msg, url, line, col, error) {
    if (isMobileDevice()) {
        alert("Error: " + msg + "\nLine: " + line + "\nCol: " + col);
    }
    return false; // Let default handler run too
};

// --- Profile System Logic ---

// Load Profiles on Start
function loadProfiles() {
    console.log("Loading profiles...");
    const profilesRef = ref(db, 'profiles');
    onValue(profilesRef, (snapshot) => {
        console.log("Profiles data received:", snapshot.val());
        profileSelect.innerHTML = '<option value="">-- Select Profile --</option>';
        if (snapshot.exists()) {
            const data = snapshot.val();
            Object.entries(data).forEach(([id, profile]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = profile.name;
                profileSelect.appendChild(option);
            });
        }

        // Auto-Login Check
        const savedProfileId = localStorage.getItem('lastProfileId');
        const savedProfileName = localStorage.getItem('lastProfileName');
        const isGuest = localStorage.getItem('isGuest');

        if (isGuest === 'true') {
            playAsGuest();
        } else if (savedProfileId && savedProfileName) {
            selectProfile(savedProfileId, savedProfileName);
        }
    }, (error) => {
        console.error("Firebase Read Error:", error);
        alert("Lỗi đọc dữ liệu từ Firebase! \nKiểm tra lại 'Rules' trên Firebase Console.\nChi tiết: " + error.message);
    });
}

// Event Listeners

// Create Profile (Modal Confirm)
confirmCreateProfileBtn.addEventListener('click', () => {
    const name = newProfileNameInput.value.trim();
    if (name) {
        // Create new profile in Firebase
        const newRef = push(ref(db, 'profiles'));
        set(newRef, { name: name }).then(() => {
            // Select the newly created user
            selectProfile(newRef.key, name);

            // Hide Bootstrap Modal
            // We assume bootstrap is available globally from the CDN
            const modalElement = document.getElementById('createProfileModal');
            // @ts-ignore
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }

            newProfileNameInput.value = '';
        }).catch((error) => {
            console.error("Firebase Write Error:", error);
            alert("Lỗi ghi dữ liệu vào Firebase! \nBạn đã chuyển Rules sang 'true' chưa?\nChi tiết: " + error.message);
        });
    }
});

// Profile Dropdown Change
profileSelect.addEventListener('change', (e) => {
    const id = e.target.value;
    if (id) {
        const name = e.target.options[e.target.selectedIndex].text;
        selectProfile(id, name);
    }
});

// Guest Button
guestBtn.addEventListener('click', () => {
    playAsGuest();
});

function playAsGuest() {
    currentProfile = { id: 'guest', name: 'Guest (No Save Sync)' };

    // Update Logic Storage
    localStorage.setItem('isGuest', 'true');
    localStorage.removeItem('lastProfileId');
    localStorage.removeItem('lastProfileName');

    updateUIForActiveProfile();
    loadGameList();
}

// Switch Button
switchProfileBtn.addEventListener('click', () => {
    currentProfile = null;

    // Clear Auto-Login
    localStorage.removeItem('lastProfileId');
    localStorage.removeItem('lastProfileName');
    localStorage.removeItem('isGuest');

    // UI Toggle
    activeProfileView.classList.replace('d-flex', 'd-none');
    activeProfileView.classList.add('d-none'); // ensure hidden
    profileSelectorView.classList.remove('d-none');

    profileSelect.value = "";

    // Reset Screens
    welcomeMessage.style.display = 'block';
    gameSelection.style.display = 'none';
    emulatorContainer.style.display = 'none';
});

function selectProfile(id, name) {
    currentProfile = { id, name };

    // Save for Auto-Login
    localStorage.setItem('lastProfileId', id);
    localStorage.setItem('lastProfileName', name);
    localStorage.removeItem('isGuest');

    updateUIForActiveProfile();
    loadGameList();
}

function updateUIForActiveProfile() {
    profileNameDisplay.textContent = currentProfile.name;

    activeProfileView.classList.remove('d-none');
    activeProfileView.classList.add('d-flex');
    profileSelectorView.classList.add('d-none');

    welcomeMessage.style.display = 'none';
    gameSelection.style.display = 'block';

    console.log("Selected Profile:", currentProfile);
}

// --- Game Logic ---

const gameListContainer = document.getElementById('game-list-container');
let allGames = [];

// Friendly System Names
const SYSTEM_NAMES = {
    'gba': 'Game Boy Advance',
    'gbc': 'Game Boy Color',
    'gb': 'Game Boy',
    'nes': 'Nintendo Entertainment System',
    'snes': 'Super Nintendo',
    'n64': 'Nintendo 64',
    'segaMD': 'Sega Genesis / Mega Drive',
    'psx': 'PlayStation',
    'nds': 'Nintendo DS'
};

async function loadGameList() {
    try {
        // Cache Busting
        const response = await fetch(`gamelist.json?v=${new Date().getTime()}`);
        allGames = await response.json();

        renderGroupedGames(allGames);

    } catch (error) {
        console.error("Failed to load game list:", error);
        gameListContainer.innerHTML = '<p class="text-white">Error loading game list.</p>';
    }
}

function renderGroupedGames(games) {
    gameListContainer.innerHTML = '';

    if (games.length === 0) {
        gameListContainer.innerHTML = '<p class="text-secondary text-center">No games found.</p>';
        return;
    }

    // 1. Group games by system
    const grouped = games.reduce((acc, game) => {
        const sys = game.system || 'other';
        if (!acc[sys]) acc[sys] = [];
        acc[sys].push(game);
        return acc;
    }, {});

    // 2. Render each group
    Object.keys(grouped).sort().forEach(sysKey => {
        const gamesInSys = grouped[sysKey];
        const sysDisplayName = SYSTEM_NAMES[sysKey] || sysKey.toUpperCase();

        // Create Section Container
        const section = document.createElement('div');
        section.className = 'mb-5 animate-fade-in';

        section.innerHTML = `
            <h5 class="text-white-50 mb-3 border-bottom border-secondary pb-2">
                ${sysDisplayName} <span class="badge bg-secondary text-white rounded-pill ms-2">${gamesInSys.length}</span>
            </h5>
            <div class="row row-cols-3 row-cols-sm-4 row-cols-md-5 row-cols-lg-6 g-4">
                <!-- Games injected here -->
            </div>
        `;

        // Inject games into the row
        const row = section.querySelector('.row');
        gamesInSys.forEach(game => {
            const col = document.createElement('div');
            col.className = 'col';
            col.innerHTML = `
                <button class="game-icon-card w-100 p-0 text-center" title="${game.name}">
                    <div class="game-icon-wrapper">
                        <img src="${game.image || 'assets/default.png'}" alt="${game.name}" loading="lazy">
                    </div>
                    <div class="game-title mt-2 text-white">${game.name}</div>
                </button>
            `;
            col.querySelector('button').onclick = () => startGame(game);
            row.appendChild(col);
        });

        gameListContainer.appendChild(section);
    });
}

function startGame(game) {
    try {
        if (!game) throw new Error("Game object is undefined");
        currentGameConfig = game;

        // UI Switch
        gameSelection.style.display = 'none';
        emulatorContainer.style.display = 'block';

        // Mobile Fullscreen Auto-Trigger
        if (isMobileDevice()) {
            document.body.classList.add('game-active'); // Trigger CSS Fullscreen

            const docEl = document.documentElement;
            const requestFull = docEl.requestFullscreen || docEl.webkitRequestFullscreen || docEl.msRequestFullscreen;
            if (requestFull) {
                try {
                    requestFull.call(docEl).catch(err => console.warn("Fullscreen blocked:", err));
                } catch (e) {
                    // Ignore errors
                }
            }
        }

        // Configure EmulatorJS
        const gameWrapper = document.getElementById('emulator');
        gameWrapper.innerHTML = '<div id="game"></div>'; // Reset container

        window.EJS_player = "#game";
        window.EJS_core = game.core;
        window.EJS_gameUrl = game.rom_path;
        window.EJS_pathtodata = "data/";
        window.EJS_startOnLoaded = true;
        window.EJS_language = "en-US"; // Keep this fix to avoid 404

        // --- Custom Control Mapping (WASD + IJKL + UO) ---
        window.EJS_defaultControls = {
            0: {
                0: { 'value': 'k', 'value2': 'BUTTON_2' },  // B (Bottom) -> K
                1: { 'value': 'j', 'value2': 'BUTTON_4' },  // Y (Left) -> J
                2: { 'value': 'v', 'value2': 'SELECT' },    // Select -> V
                3: { 'value': 'enter', 'value2': 'START' }, // Start -> Enter
                4: { 'value': 'w', 'value2': 'DPAD_UP' },
                5: { 'value': 's', 'value2': 'DPAD_DOWN' },
                6: { 'value': 'a', 'value2': 'DPAD_LEFT' },
                7: { 'value': 'd', 'value2': 'DPAD_RIGHT' },
                8: { 'value': 'l', 'value2': 'BUTTON_1' },  // A (Right) -> L
                9: { 'value': 'i', 'value2': 'BUTTON_3' },  // X (Top) -> I
                10: { 'value': 'q', 'value2': 'LEFT_TOP_SHOULDER' },  // L -> Q
                11: { 'value': 'o', 'value2': 'RIGHT_TOP_SHOULDER' }, // R -> O
                12: { 'value': 'u', 'value2': 'LEFT_BOTTOM_SHOULDER' }, // L2 -> U
                13: { 'value': 'e', 'value2': 'RIGHT_BOTTOM_SHOULDER' }, // R2 -> E
                14: { 'value': '', 'value2': 'LEFT_STICK' },
                15: { 'value': '', 'value2': 'RIGHT_STICK' },
                16: { 'value': 'd', 'value2': 'LEFT_STICK_X:+1' },
                17: { 'value': 'a', 'value2': 'LEFT_STICK_X:-1' },
                18: { 'value': 's', 'value2': 'LEFT_STICK_Y:+1' },
                19: { 'value': 'w', 'value2': 'LEFT_STICK_Y:-1' },

                20: { 'value': 'l', 'value2': 'RIGHT_STICK_X:+1' },
                21: { 'value': 'j', 'value2': 'RIGHT_STICK_X:-1' },
                22: { 'value': 'i', 'value2': 'RIGHT_STICK_Y:-1' },
                23: { 'value': 'k', 'value2': 'RIGHT_STICK_Y:+1' },

                27: { 'value': 'add' },
                28: { 'value': 'space' },
                29: { 'value': 'subtract' }
            },
            1: {
                0: { 'value': '2', 'value2': 'BUTTON_2' },  // B (Bottom) -> 2
                1: { 'value': '1', 'value2': 'BUTTON_4' },  // Y (Left) -> 1
                4: { 'value': 'arrowup', 'value2': 'DPAD_UP' },
                5: { 'value': 'arrowdown', 'value2': 'DPAD_DOWN' },
                6: { 'value': 'arrowleft', 'value2': 'DPAD_LEFT' },
                7: { 'value': 'arrowright', 'value2': 'DPAD_RIGHT' },
                8: { 'value': '3', 'value2': 'BUTTON_1' },  // A (Right) -> 3
                9: { 'value': '5', 'value2': 'BUTTON_3' },  // X (Top) -> 5
                10: { 'value': '4', 'value2': 'LEFT_TOP_SHOULDER' },  // L -> 4
                11: { 'value': '6', 'value2': 'RIGHT_TOP_SHOULDER' }, // R -> 6
                2: { 'value': '7', 'value2': 'SELECT' },    // Select -> 7
                3: { 'value': '9', 'value2': 'START' }      // Start -> 9
            },
            2: {},
            3: {}
        };

        // --- COI / SharedArrayBuffer Fix for Edge/GH Pages ---
        console.log("Environment Check:", {
            crossOriginIsolated: window.crossOriginIsolated,
            secureContext: window.isSecureContext,
            sharedArrayBuffer: typeof window.SharedArrayBuffer !== 'undefined',
            userAgent: navigator.userAgent
        });

        // FORCE FIX: Edge often reports COI=true via service worker but still crashes with SharedArrayBuffer
        const isEdge = /Edg/.test(navigator.userAgent);

        if (!window.crossOriginIsolated || (isEdge && window.location.hostname.includes("github.io"))) {
            if (isEdge) {
                console.warn("⚠️ Edge + GitHub Pages detected. Force disabling threads to prevent 'memory access out of bounds' crash.");
            } else {
                console.warn("⚠️ Cross-Origin Isolation failed. Disabling EmulatorJS threads to prevent WASM crash.");
            }
            window.EJS_threads = false;
        } else {
            console.log("✅ Cross-Origin Isolation active. Threads enabled.");
        }


        // --- Save Injection Hook ---
        // --- Save Injection Hook ---
        // --- Helper: Get Emscripten FileSystem ---
        function getFS() {
            if (window.Module && window.Module.FS) return window.Module.FS;
            if (window.EJS_emulator && window.EJS_emulator.Module && window.EJS_emulator.Module.FS) return window.EJS_emulator.Module.FS;
            if (window.EJS_emulator && window.EJS_emulator.gameManager && window.EJS_emulator.gameManager.Module && window.EJS_emulator.gameManager.Module.FS) return window.EJS_emulator.gameManager.Module.FS;
            return null;
        }

        // --- Helper: Find Save Directory ---
        function findSaveDir(fs) {
            const candidates = [
                '/home/web_user/retroarch/userdata/saves',
                '/home/web_user/retroarch/saves',
                '/data/saves',
                '/saves',
                '/userdata/saves'
            ];

            for (const path of candidates) {
                try {
                    // Try to list directory. If it succeeds, the dir exists.
                    if (fs.readdir(path)) {
                        console.log("   🔍 [FS] Found valid save dir:", path);
                        return path;
                    }
                } catch (e) {
                    // Path not found or not accessible
                }
            }

            console.warn("   ⚠️ [FS] No standard save dir found. Defaulting to standard.");
            return '/home/web_user/retroarch/userdata/saves';
        }

        // --- Save Injection Hook ---
        window.EJS_onGameStart = async function () {
            console.log("🔥 [LOAD] EJS_onGameStart triggered!");
            console.log("   - Current Profile:", currentProfile ? currentProfile.name : "NULL");
            if (!currentProfile) return;

            // Stop any existing interval
            if (saveInterval) clearInterval(saveInterval);
            lastSaveData = null; // Reset cache

            const gameId = currentGameConfig.id;
            const romName = currentGameConfig.rom_path.split('/').pop();
            const saveFileName = romName.replace(/\.\w+$/, '.srm');

            // Wait for FS to be ready (sometimes slight delay)
            let fs = getFS();
            let retries = 0;
            while (!fs && retries < 10) {
                await new Promise(r => setTimeout(r, 500));
                console.log("   ⏳ Waiting for FS...");
                fs = getFS();
                retries++;
            }

            if (!fs) {
                console.error("   ❌ [LOAD] FS not found after waiting!");
                return;
            }

            const saveDir = findSaveDir(fs);
            const virtualPath = `${saveDir}/${saveFileName}`;

            console.log("   - Game ID:", gameId);
            console.log("   - Target Virtual Path:", virtualPath);

            try {
                console.log("   - Fetching from Firebase...");
                const snapshot = await get(child(ref(db), `users/${currentProfile.id}/saves/${gameId}`));

                if (snapshot.exists()) {
                    const cloudData = snapshot.val();
                    console.log("   ✅ [LOAD] Save found in cloud!");
                    console.log("   - Timestamp:", new Date(cloudData.timestamp).toLocaleString());
                    console.log("   - Size (Base64):", cloudData.srm_data.length);

                    const saveBytes = base64ToUint8Array(cloudData.srm_data);
                    lastSaveData = saveBytes; // Cache initial cloud state

                    console.log("   - Writing to virtual FS...");
                    // Ensure dir exists (createPath params: parent, name, canRead, canWrite)
                    // We need to recursively create path if findSaveDir returned a default that doesn't exist
                    // But fs.createPath implementation usually needs parent to exist.
                    // Simplified: just try writing. If parent invalid, we might need mkdirp.
                    // Start simple:

                    try {
                        // Attempt to ensure directory exists (non-recursive check)
                        const parts = saveDir.split('/').filter(p => p);
                        let currentPath = '';
                        for (let i = 0; i < parts.length; i++) {
                            const parent = currentPath || '/';
                            const name = parts[i];
                            currentPath = (currentPath ? currentPath + '/' : '/') + name;
                            try { fs.stat(currentPath); } catch (e) {
                                fs.createPath(parent, name, true, true);
                            }
                        }

                        fs.writeFile(virtualPath, saveBytes);
                        console.log(`   ✅ [LOAD] Restored save to ${virtualPath}`);
                    } catch (e) {
                        console.error("   ❌ [LOAD] Error writing file:", e);
                    }

                } else {
                    console.log("   ⚠️ [LOAD] No save found in cloud for this game.");
                }
            } catch (err) {
                console.error("   ❌ [LOAD] Error fetching save:", err);
            }

            // Start Polling for new saves
            console.log("   ⏳ [POLL] Starting Save Poller (1s interval)...");
            saveInterval = setInterval(() => checkForSaveUpdate(virtualPath, gameId), 1000);
        };

        // --- Helper: Compare Byte Arrays ---
        function arraysEqual(a, b) {
            if (a === b) return true;
            if (a == null || b == null) return false;
            if (a.length !== b.length) return false;
            for (let i = 0; i < a.length; ++i) {
                if (a[i] !== b[i]) return false;
            }
            return true;
        }

        // --- Polling Function ---
        function checkForSaveUpdate(virtualPath, gameId) {
            if (!currentProfile || currentProfile.id === 'guest') return;

            try {
                const fs = getFS();
                if (fs) {
                    try {
                        // Check if file exists
                        fs.stat(virtualPath); // Throws if missing

                        // Read file
                        const fileData = fs.readFile(virtualPath);

                        // SMART CHECK: Only upload if different from last cache
                        if (arraysEqual(fileData, lastSaveData)) {
                            // console.log("   💤 [POLL] No changes detected.");
                            return;
                        }

                        console.log("   💾 [POLL] Save changed! Uploading... (" + fileData.length + " bytes)");
                        const base64String = uint8ArrayToBase64(fileData);

                        set(ref(db, `users/${currentProfile.id}/saves/${gameId}`), {
                            srm_data: base64String,
                            timestamp: Date.now()
                        }).then(() => {
                            console.log("   ✅ [POLL] Cloud Sync Success!");
                            lastSaveData = fileData; // Update cache after success
                        }).catch(e => {
                            console.error("   ❌ [POLL] Upload failed:", e);
                        });

                    } catch (e) {
                        // File not found yet
                        // console.warn("   ⚠️ [POLL] Save file not found yet at:", virtualPath);
                        // Suppress warn to avoid spamming console every 1s
                    }
                } else {
                    // console.warn("   ⚠️ [POLL] FS not ready.");
                }
            } catch (e) {
                console.error("   ❌ [POLL] Unexpected Error:", e);
            }
        }

        // --- Native Event Hooks (RomM Style) ---
        window.EJS_onSaveSave = function (e) {
            // e is likely the Uint8Array or an object containing it
            console.log("🔥 [EVENT] EJS_onSaveSave triggered!", e);

            if (!currentProfile || currentProfile.id === 'guest') return;

            // If e represents the file content (Uint8Array)
            if (e && (e instanceof Uint8Array || e.byteLength !== undefined)) {
                const fileData = new Uint8Array(e);

                // Smart check
                if (arraysEqual(fileData, lastSaveData)) {
                    console.log("   💤 [EVENT] Content matches cache. Skipping upload.");
                    return;
                }

                console.log("   💾 [EVENT] Uploading via Native Hook... (" + fileData.length + " bytes)");
                const base64String = uint8ArrayToBase64(fileData);

                const gameId = currentGameConfig.id; // Global var

                set(ref(db, `users/${currentProfile.id}/saves/${gameId}`), {
                    srm_data: base64String,
                    timestamp: Date.now()
                }).then(() => {
                    console.log("   ✅ [EVENT] Native Upload Success!");
                    lastSaveData = fileData; // Update cache
                }).catch(err => {
                    console.error("   ❌ [EVENT] Upload failed:", err);
                });
            }
        };

        // Keep Event hook just in case, but delegate to poller logic?
        window.EJS_onSaveUpdate = function () {
            console.log("🔥 [EVENT] EJS_onSaveUpdate triggered (Rare)!");
            // We can trigger an immediate check
            if (saveInterval) {
                // Logic likely handled by poller, but good to know if it fires.
            }
        };

        // Load loader - EXACT LEGACY WAY -> Just append, do not check/remove
        const script = document.createElement('script');
        script.src = "data/loader.js";
        script.async = true;
        document.body.appendChild(script);

    } catch (e) {
        alert("StartGame Error: " + e.message);
        console.error(e);
    }
}

// --- Helpers ---
// --- Helpers ---
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function base64ToUint8Array(base64) {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
}

function uint8ArrayToBase64(bytes) {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

backBtn.addEventListener('click', () => {
    document.body.classList.remove('game-active'); // Cleanup
    location.reload();
});

// Initialize
detectPWAEnvironment();
loadProfiles();

function detectPWAEnvironment() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    // @ts-ignore
    const isStandalone = window.navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;

    if (isIOS && !isStandalone) {
        const prompt = document.getElementById('ios-install-prompt');
        if (prompt) {
            prompt.classList.remove('d-none');
            prompt.classList.add('d-flex');

            document.getElementById('close-install-prompt')?.addEventListener('click', () => {
                prompt.classList.remove('d-flex');
                prompt.classList.add('d-none');
            });
        }
    }
}
