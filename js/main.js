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

        // --- Save Injection Hook ---
        // --- Save Injection Hook ---
        // window.EJS_onGameStart = async function () {
        //     console.log("Emulator Started. Checking cloud saves for:", currentProfile.name);
        //     if (!currentProfile) return;
        //     ... 
        // };

        // --- Save Extraction Hook ---
        // window.EJS_onSaveUpdate = function () {
        //     ...
        // };

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
