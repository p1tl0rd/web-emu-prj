import { db, ref, set, get, child, push, onValue } from './firebase-config.js';

// DOM Elements
const profileSelect = document.getElementById('profile-select');
const createProfileBtn = document.getElementById('create-profile-btn');
const createProfileView = document.getElementById('create-profile-view');
const activeProfileView = document.getElementById('active-profile-view');
const profileSelectorView = document.getElementById('profile-selector-view');
const newProfileNameInput = document.getElementById('new-profile-name');
const confirmCreateProfileBtn = document.getElementById('confirm-create-profile');
const cancelCreateProfileBtn = document.getElementById('cancel-create-profile');
const profileNameDisplay = document.getElementById('profile-name-display');
const switchProfileBtn = document.getElementById('switch-profile-btn');

const welcomeMessage = document.getElementById('welcome-message');
const gameListDiv = document.getElementById('game-list');
const gameSelection = document.getElementById('game-selection');
const emulatorContainer = document.getElementById('emulator-container');
const backBtn = document.getElementById('back-btn');

let currentProfile = null; // { id: "string", name: "string" }
let currentGameConfig = null;

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
            // Data format: { "randomId1": { name: "Tung" }, "randomId2": { name: "Nam" } }
            Object.entries(data).forEach(([id, profile]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = profile.name;
                profileSelect.appendChild(option);
            });
        }
        // If there was a previously selected profile (stored in localStorage?), we could restore it here
    }, (error) => {
        console.error("Firebase Read Error:", error);
        alert("Lỗi đọc dữ liệu từ Firebase! \nKiểm tra lại 'Rules' trên Firebase Console.\nChi tiết: " + error.message);
    });
}

// Event Listeners for UI switching
createProfileBtn.addEventListener('click', () => {
    profileSelectorView.style.display = 'none';
    createProfileView.style.display = 'flex';
    newProfileNameInput.focus();
});

cancelCreateProfileBtn.addEventListener('click', () => {
    createProfileView.style.display = 'none';
    profileSelectorView.style.display = 'flex';
    newProfileNameInput.value = '';
});

confirmCreateProfileBtn.addEventListener('click', () => {
    const name = newProfileNameInput.value.trim();
    if (name) {
        // Create new profile in Firebase
        const newRef = push(ref(db, 'profiles'));
        set(newRef, { name: name }).then(() => {
            // Select the newly created user
            selectProfile(newRef.key, name);

            // Reset UI
            createProfileView.style.display = 'none';
            profileSelectorView.style.display = 'none'; // Will show active view
            newProfileNameInput.value = '';
        }).catch((error) => {
            console.error("Firebase Write Error:", error);
            alert("Lỗi ghi dữ liệu vào Firebase! \nBạn đã chuyển Rules sang 'true' chưa?\nChi tiết: " + error.message);
        });
    }
});

profileSelect.addEventListener('change', (e) => {
    const id = e.target.value;
    if (id) {
        const name = e.target.options[e.target.selectedIndex].text;
        selectProfile(id, name);
    }
});

switchProfileBtn.addEventListener('click', () => {
    currentProfile = null;
    activeProfileView.style.display = 'none';
    profileSelectorView.style.display = 'flex';
    profileSelect.value = "";

    // Hide game elements
    welcomeMessage.style.display = 'block';
    gameSelection.style.display = 'none';
    emulatorContainer.style.display = 'none';
});

function selectProfile(id, name) {
    currentProfile = { id, name };

    // Update UI
    profileNameDisplay.textContent = `Player: ${name}`;
    activeProfileView.style.display = 'flex';
    profileSelectorView.style.display = 'none';
    welcomeMessage.style.display = 'none';
    gameSelection.style.display = 'block';

    console.log("Selected Profile:", currentProfile);
    loadGameList();
}

// --- Game Logic ---

async function loadGameList() {
    try {
        const response = await fetch('gamelist.json');
        const games = await response.json();

        gameListDiv.innerHTML = '';
        games.forEach(game => {
            const card = document.createElement('div');
            card.className = 'game-card';
            card.innerHTML = `
                <img src="${game.image || 'assets/default.png'}" alt="${game.name}">
                <h3>${game.name}</h3>
            `;
            card.onclick = () => startGame(game);
            gameListDiv.appendChild(card);
        });
    } catch (error) {
        console.error("Failed to load game list:", error);
        gameListDiv.innerHTML = '<p>Error loading game list.</p>';
    }
}

function startGame(game) {
    currentGameConfig = game;

    // UI Switch
    gameSelection.style.display = 'none';
    emulatorContainer.style.display = 'block';

    // Configure EmulatorJS
    const gameWrapper = document.getElementById('emulator');
    gameWrapper.innerHTML = '<div id="game"></div>'; // Reset container

    window.EJS_player = "#game";
    window.EJS_core = game.core;
    window.EJS_gameUrl = game.rom_path;
    window.EJS_pathtodata = "data/"; // Local data
    window.EJS_startOnLoaded = true;

    // --- Save Injection Hook ---
    window.EJS_onGameStart = async function () {
        console.log("Emulator Started. Checking cloud saves for:", currentProfile.name);
        if (!currentProfile) return;

        const gameId = currentGameConfig.id;
        const romName = currentGameConfig.rom_path.split('/').pop();
        const saveFileName = romName.replace(/\.\w+$/, '.srm');

        // Fetch from Firebase using Profile ID instead of Auth UID
        const snapshot = await get(child(ref(db), `users/${currentProfile.id}/saves/${gameId}`));

        if (snapshot.exists()) {
            const cloudData = snapshot.val();
            console.log("Found save!", new Date(cloudData.timestamp).toLocaleString());

            const saveBytes = base64ToUint8Array(cloudData.srm_data);
            const virtualPath = `/home/web_user/retroarch/userdata/saves/${saveFileName}`;

            try {
                if (window.Module && window.Module.FS) {
                    window.Module.FS.createPath('/home/web_user/retroarch/userdata', 'saves', true, true);
                    window.Module.FS.writeFile(virtualPath, saveBytes);
                    console.log(`Restored save to ${virtualPath}`);
                }
            } catch (e) {
                console.error("Failed to inject save:", e);
            }
        }
    };

    // --- Save Extraction Hook ---
    window.EJS_onSaveUpdate = function () {
        console.log("Save update detected!");
        if (!currentProfile) return;

        const romName = currentGameConfig.rom_path.split('/').pop();
        const saveFileName = romName.replace(/\.\w+$/, '.srm');
        const virtualPath = `/home/web_user/retroarch/userdata/saves/${saveFileName}`;

        try {
            if (window.Module && window.Module.FS) {
                const fileData = window.Module.FS.readFile(virtualPath);
                const base64String = uint8ArrayToBase64(fileData);

                const updatePayload = {
                    srm_data: base64String,
                    timestamp: Date.now()
                };

                // Save to Profile ID path
                set(ref(db, `users/${currentProfile.id}/saves/${currentGameConfig.id}`), updatePayload)
                    .then(() => console.log("Synced to Cloud successfully"))
                    .catch((err) => console.error("Sync failed", err));
            }
        } catch (e) {
            console.error("Error extracting save:", e);
        }
    };

    // Load loader
    const script = document.createElement('script');
    script.src = "data/loader.js";
    script.async = true;
    document.body.appendChild(script);
}

// --- Helpers ---
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
    location.reload();
});

// Initialize
loadProfiles();
