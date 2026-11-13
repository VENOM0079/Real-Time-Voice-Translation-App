const socket = io();

// UI Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const exportBtn = document.getElementById('exportBtn');
const recordingIndicator = document.getElementById('recordingIndicator');
const transcriptionFeed = document.getElementById('transcriptionFeed');
const placeholder = document.getElementById('placeholder');
const statusMessage = document.getElementById('statusMessage');
const spinnerContainer = document.getElementById('spinnerContainer');

// State
let mediaRecorder;
let audioChunks = [];
let transcriptionLog = []; // Used for export
let chunkInterval;
const CHUNK_TIME_MS = 3000; // 3 seconds chunks

// Connect to Socket.IO
socket.on('connect', () => {
    statusMessage.innerHTML = '<span class="text-success"><i class="fa fa-check-circle"></i> Connected to server</span>';
});

socket.on('disconnect', () => {
    statusMessage.innerHTML = '<span class="text-danger"><i class="fa fa-exclamation-triangle"></i> Disconnected from server</span>';
    stopRecording();
});

socket.on('server_status', (data) => {
    console.log(data.message);
});

// Receive translation result
socket.on('transcription_result', (data) => {
    // Hide spinner since we got a result
    spinnerContainer.style.display = 'none';

    const text = data.text;
    const timestamp = data.timestamp;

    // Check if the placeholder still exists
    if (placeholder) {
        placeholder.style.display = 'none';
    }

    // Save to log for export
    transcriptionLog.push(`[${timestamp}] ${text}`);

    // Create entry element
    const entryContainer = document.createElement('div');
    entryContainer.className = 'feed-entry card animate__animated animate__fadeInUp';

    entryContainer.innerHTML = `
        <div class="card-body py-2 px-3">
            <div class="time-badge "><i class="fa fa-clock"></i> ${timestamp}</div>
            <div class="translated-text mt-1" style="font-size: 1.1em;">${text}</div>
        </div>
    `;

    transcriptionFeed.appendChild(entryContainer);
    // Scroll to bottom
    transcriptionFeed.scrollTop = transcriptionFeed.scrollHeight;
});

// Receive error
socket.on('transcription_error', (data) => {
    spinnerContainer.style.display = 'none';
    alert(`Error: ${data.error}`);
    stopRecording();
});


// RTSP Control functions
function startRtspStream() {
    // Tell the server to start the RTSP stream ingestion
    spinnerContainer.style.display = 'block';
    socket.emit('start_rtsp');

    // Update UI
    startBtn.disabled = true;
    stopBtn.disabled = false;
    recordingIndicator.style.display = 'inline-block';
    statusMessage.textContent = 'Processing RTSP Stream...';
}

function stopRtspStream() {
    socket.emit('stop_rtsp');

    // Update UI
    startBtn.disabled = false;
    stopBtn.disabled = true;
    recordingIndicator.style.display = 'none';
    spinnerContainer.style.display = 'none';
    statusMessage.textContent = 'RTSP Stream processing stopped.';
}

// Export Log as TXT
function exportAsTxt() {
    if (transcriptionLog.length === 0) {
        alert("No transcriptions to export yet.");
        return;
    }

    const logText = transcriptionLog.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `translation_log_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
    a.click();

    URL.revokeObjectURL(url);
}

// Event Listeners
startBtn.addEventListener('click', startRtspStream);
stopBtn.addEventListener('click', stopRtspStream);
exportBtn.addEventListener('click', exportAsTxt);
