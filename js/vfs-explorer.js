
// --- VFS Explorer Debug Tool ---
let currentVFSPath = '/';

function openVFSExplorer() {
    const fs = getFS();
    if (!fs) {
        alert("Emulator FileSystem not ready yet! Start a game first.");
        return;
    }

    // Try to start at a useful path
    if (localStorage.getItem('lastVFSPath')) {
        currentVFSPath = localStorage.getItem('lastVFSPath');
    } else {
        // Default to save dir
        currentVFSPath = findSaveDir(fs) || '/';
    }

    const modal = new bootstrap.Modal(document.getElementById('vfsModal'));
    modal.show();

    refreshVFS();
}

function refreshVFS() {
    loadVFSPath(currentVFSPath);
}

function vfsUpDir() {
    if (currentVFSPath === '/' || currentVFSPath === '') return;

    const parts = currentVFSPath.split('/').filter(p => p);
    parts.pop();
    currentVFSPath = '/' + parts.join('/');
    if (currentVFSPath === '') currentVFSPath = '/';

    loadVFSPath(currentVFSPath);
}

function loadVFSPath(path) {
    const fs = getFS();
    if (!fs) return;

    currentVFSPath = path;
    localStorage.setItem('lastVFSPath', path);

    document.getElementById('vfs-current-path').textContent = path;
    const listEl = document.getElementById('vfs-file-list');
    listEl.innerHTML = '<div class="text-center p-4 text-warning"><div class="spinner-border" role="status"></div></div>';

    try {
        const items = fs.readdir(path);
        const folders = [];
        const files = [];

        items.forEach(item => {
            if (item === '.' || item === '..') return;

            const fullPath = path === '/' ? `/${item}` : `${path}/${item}`;
            try {
                const stat = fs.stat(fullPath);
                if (fs.isDir(stat.mode)) {
                    folders.push({ name: item, path: fullPath, mtime: stat.mtime });
                } else {
                    files.push({ name: item, path: fullPath, size: stat.size, mtime: stat.mtime });
                }
            } catch (e) {
                console.warn("Skipping inaccesible item:", item);
            }
        });

        // Sort: Folders first, then files
        folders.sort((a, b) => a.name.localeCompare(b.name));
        files.sort((a, b) => a.name.localeCompare(b.name));

        let html = '<div class="list-group list-group-flush bg-dark">';

        if (folders.length === 0 && files.length === 0) {
            html += '<div class="list-group-item bg-dark text-secondary text-center">Empty Directory</div>';
        }

        folders.forEach(f => {
            html += `
                <button type="button" class="list-group-item list-group-item-action bg-dark text-warning border-secondary d-flex justify-content-between align-items-center" onclick="loadVFSPath('${f.path}')">
                    <span><i class="bi bi-folder-fill me-2"></i> ${f.name}</span>
                    <span class="badge bg-secondary rounded-pill">DIR</span>
                </button>`;
        });

        files.forEach(f => {
            const sizeStr = (f.size / 1024).toFixed(1) + ' KB';
            html += `
                <div class="list-group-item bg-dark text-white border-secondary d-flex justify-content-between align-items-center">
                    <span class="text-truncate" style="max-width: 70%;"><i class="bi bi-file-earmark-code me-2"></i> ${f.name}</span>
                    <div>
                        <span class="badge bg-dark border border-secondary me-2">${sizeStr}</span>
                        <button class="btn btn-sm btn-outline-success" onclick="downloadVFSFile('${f.path}')">
                            <i class="bi bi-download"></i>
                        </button>
                    </div>
                </div>`;
        });

        html += '</div>';
        listEl.innerHTML = html;

    } catch (e) {
        console.error("VFS Read Error:", e);
        listEl.innerHTML = `<div class="alert alert-danger m-3">Error reading path: ${e.message}</div>`;
    }
}

function downloadVFSFile(path) {
    const fs = getFS();
    if (!fs) return;

    try {
        const data = fs.readFile(path); // Uint8Array
        const filename = path.split('/').pop();

        const blob = new Blob([data], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log(`Downloaded ${filename} from VFS.`);
    } catch (e) {
        alert("Failed to download file: " + e.message);
    }
}

// Ensure getFS is globally available if not already
if (typeof window.getFS === 'undefined') {
    window.getFS = function () {
        if (window.EJS_emulator && window.EJS_emulator.Module && window.EJS_emulator.Module.FS) {
            return window.EJS_emulator.Module.FS;
        }
        return null;
    };
}
