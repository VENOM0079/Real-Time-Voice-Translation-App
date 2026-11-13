# Real-Time Voice Translation App

This app streams microphone audio from the user's browser, sends it to a Python Flask server via WebSocket (Socket.IO), transcribes and translates it into English using the OpenAI Whisper model (via API), and updates the frontend UI live with animations.

## Prerequisites
- Python 3.10+
- An OpenAI API Key

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API Key:**
   Create a `.env` file in the same directory as `app.py` and add your API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```
   The application will start the SocketIO server, generally available at `http://localhost:5000`.

## Usage
- Open `http://localhost:5000` in your web browser (Chrome or Firefox recommended for MediaRecorder support).
- Click **Start Recording**.
- Allow microphone permissions if prompted.
- Speak in any language; the translation will appear in the transcription feed.
- Click **Export Log** to download the transcript as a `.txt` file.
