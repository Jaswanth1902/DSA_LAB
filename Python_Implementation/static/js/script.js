// Global State
let selectedFile = null;
let sizeChart = null;

// DOM Elements (Initialized in setup)
let dropZone, fileInput, fileInfo, compressBtn, decompressBtn, consoleContent, resultsSection;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM Elements
    dropZone = document.getElementById('dropZone');
    fileInput = document.getElementById('fileInput');
    fileInfo = document.getElementById('fileInfo');
    compressBtn = document.getElementById('compressBtn');
    decompressBtn = document.getElementById('decompressBtn');
    consoleContent = document.getElementById('consoleContent');
    resultsSection = document.getElementById('resultsSection');

    // Verify critical elements
    if (!compressBtn || !decompressBtn) {
        console.error("Critical elements missing!");
        return;
    }

    console.log("DSA EL Initialized");
    fetchStats();

    // Explicit Button Binding
    compressBtn.addEventListener('click', () => processFile('compress'));
    decompressBtn.addEventListener('click', () => processFile('decompress'));

    const resetBtn = document.getElementById('resetStatsBtn');
    if (resetBtn) resetBtn.addEventListener('click', resetStats);

    // Drop Zone Binding
    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag and drop handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#3b82f6';
            dropZone.style.backgroundColor = 'rgba(59, 130, 246, 0.05)';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '';
            dropZone.style.backgroundColor = '';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '';
            dropZone.style.backgroundColor = '';
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });
    }
});

function handleFile(file) {
    selectedFile = file;
    fileInfo.textContent = `Loaded: ${file.name} (${formatBytes(file.size)})`;
    fileInfo.classList.remove('hidden');
    clearLog();
    log(`File ready: ${file.name}`);
    resultsSection.style.display = 'none';
}

async function processFile(mode) {
    if (!selectedFile) {
        alert("Please load a file first!");
        return;
    }

    // Disable buttons
    compressBtn.disabled = true;
    decompressBtn.disabled = true;

    // showLoader(); // Undefined in original code? Assuming implicit or not needed.
    log(`Starting ${mode} process...`);
    // Simulation Logs
    if (mode === 'compress') {
        log("DSA EL: Starting Smart Compression...", 'info');
        await wait(200);
        log("Analysing Entropy...", 'info');
        await wait(300);
        log("Building Huffman Tree...", 'info');
    } else {
        log("DSA EL: Starting Restoration...", 'info');
        await wait(300);
        log("Reading Flag Bytes...", 'info');
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('mode', mode);

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.error) {
            log(`Error: ${result.error}`, 'error');
            alert(result.error);
        } else {
            if (result.is_identity) {
                log("Note: File appears incompressible (e.g. already a .docx/zip). Stored in Identity Mode to prevent size explosion.", 'info');
            }
            log(mode === 'compress' ? "Optimization Success." : "Restoration Success.");
            displayResults(result);
            downloadFile(result.download_url, result.filename);
            fetchStats();
        }
    } catch (e) {
        console.error(e);
        log("Network/Server Error.", 'error');
    } finally {
        if (compressBtn) compressBtn.disabled = false;
        if (decompressBtn) decompressBtn.disabled = false;
    }
}

function displayResults(data) {
    document.getElementById('originalSize').textContent = formatBytes(data.original_size);
    document.getElementById('processedSize').textContent = formatBytes(data.processed_size);

    resultsSection.style.display = 'block';

    renderChart(data.original_size, data.processed_size);
}

function renderChart(original, processed) {
    const ctx = document.getElementById('sizeChart').getContext('2d');
    if (sizeChart) {
        sizeChart.destroy();
        sizeChart = null;
    }

    if (typeof Chart === 'undefined') {
        console.warn("Chart.js not loaded.");
        return;
    }

    sizeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Original', 'Compressed'],
            datasets: [{
                label: 'Size (Bytes)',
                data: [original, processed],
                backgroundColor: ['rgba(255, 255, 255, 0.1)', '#06b6d4'],
                borderRadius: 4,
                barThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { display: false },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function downloadFile(url, filename) {
    const link = document.getElementById('downloadLink');
    if (!link) return;
    link.href = url;
    link.download = filename;
    link.click();
    log("Download initiated automatically.");
}

async function fetchStats() {
    try {
        const r = await fetch('/stats');
        const d = await r.json();
        const cElem = document.getElementById('compressedCount');
        const dElem = document.getElementById('decompressedCount');
        if (cElem) cElem.textContent = d.compressed;
        if (dElem) dElem.textContent = d.decompressed;
    } catch (e) {
        console.warn("Stats fetch failed");
    }
}

async function resetStats() {
    if (!confirm("Are you sure you want to reset the statistics count?")) return;

    try {
        const r = await fetch('/reset_stats', { method: 'POST' });
        const d = await r.json();
        if (d.status === 'success') {
            const cElem = document.getElementById('compressedCount');
            const dElem = document.getElementById('decompressedCount');
            if (cElem) cElem.textContent = 0;
            if (dElem) dElem.textContent = 0;
            log("Statistics counter reset.", 'info');
        }
    } catch (e) {
        console.error("Reset failed", e);
    }
}

// Helpers
function log(msg, type) {
    const div = document.createElement('div');
    div.className = 'log-line';
    const time = new Date().toLocaleTimeString().split(' ')[0];
    div.innerHTML = `<span style="color:#64748b">[${time}]</span> ${msg}`;
    if (consoleContent) {
        consoleContent.appendChild(div);
        consoleContent.scrollTop = consoleContent.scrollHeight;
    }
}

function clearLog() {
    if (consoleContent) {
        consoleContent.innerHTML = '';
        log("// System Ready.");
    }
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 B';
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals < 0 ? 0 : decimals))} ${['B', 'KB', 'MB', 'GB'][i]}`;
}
