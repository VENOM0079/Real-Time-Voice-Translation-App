import threading
threading.RLock = threading._PyRLock
import eventlet
eventlet.monkey_patch()

import os
import tempfile
import time
from datetime import datetime
from threading import Lock

from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-whisper-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize client only if key is present, otherwise we'll handle it during transcription
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

thread = None
thread_lock = Lock()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print("Client connected")
    socketio.emit('server_status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

import subprocess
import glob
import imageio_ffmpeg

RTSP_URL = "rtsp://admin:aaaa1111@50.213.183.181:9000/Streaming/Channels/302"

rtsp_process = None
rtsp_thread = None
is_streaming = False
temp_dir = None

@socketio.on('start_rtsp')
def start_rtsp():
    global rtsp_process, rtsp_thread, is_streaming, temp_dir
    
    if is_streaming:
        socketio.emit('server_status', {'message': 'RTSP stream already running'})
        return
        
    if not client:
        socketio.emit('transcription_error', {'error': 'OpenAI API key not set. Please set OPENAI_API_KEY environment variable.'})
        return
        
    is_streaming = True
    temp_dir = tempfile.mkdtemp()
    print(f"Starting RTSP stream processing in {temp_dir}")
    
    # Start ffmpeg to grab RTSP audio, convert to mp3, and segment into 3-second chunks
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe,
        '-rtsp_transport', 'tcp',
        '-i', RTSP_URL,
        '-vn', # Disable video
        '-acodec', 'libmp3lame',
        '-f', 'segment',
        '-segment_time', '3',
        '-reset_timestamps', '1',
         os.path.join(temp_dir, 'chunk_%03d.mp3')
    ]
    
    rtsp_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    socketio.emit('server_status', {'message': 'RTSP stream started'})
    
    # Start worker thread to process chunks
    rtsp_thread = eventlet.spawn(process_chunks)

def process_chunks():
    global is_streaming, temp_dir
    
    processed_files = set()
    
    while is_streaming:
        eventlet.sleep(1) # Allow other connections to be processed
        
        if not temp_dir or not os.path.exists(temp_dir):
            continue
            
        # Find all chunks produced so far
        search_pattern = os.path.join(temp_dir, 'chunk_*.mp3')
        all_chunks = sorted(glob.glob(search_pattern))
        
        if len(all_chunks) < 2:
            # We need at least one completed chunk (indicated by the presence of a newer chunk being written to)
            continue
            
        # Process all chunks EXCEPT the very last one, which is currently being written by ffmpeg
        ready_chunks = all_chunks[:-1]
        
        for chunk_path in ready_chunks:
            if chunk_path in processed_files:
                continue
                
            processed_files.add(chunk_path)
            print(f"Processing chunk {chunk_path}")
            
            try:
                with open(chunk_path, "rb") as audio_file:
                    translation = client.audio.translations.create(
                        model="whisper-1", 
                        file=audio_file,
                        response_format="text"
                    )
                    
                transcribed_text = translation if isinstance(translation, str) else translation.text
                current_time = datetime.now().strftime("%H:%M:%S")

                if transcribed_text.strip():
                    socketio.emit('transcription_result', {
                        'text': transcribed_text.strip(),
                        'timestamp': current_time
                    })
            except Exception as e:
                print(f"Error processing {chunk_path}: {e}")
                socketio.emit('transcription_error', {'error': f"Failed to process chunk: {str(e)}"})

@socketio.on('stop_rtsp')
def stop_rtsp():
    global rtsp_process, is_streaming, temp_dir
    print('Stopping RTSP stream')
    is_streaming = False
    
    if rtsp_process:
        rtsp_process.terminate()
        rtsp_process.wait()
        rtsp_process = None
        
    socketio.emit('server_status', {'message': 'RTSP stream stopped'})
    
    # Cleanup temp dir eventually
    if temp_dir and os.path.exists(temp_dir):
        try:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"Failed to cleanup {temp_dir}: {e}")

if __name__ == '__main__':
    # Start SocketIO server with eventlet for async performance
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
