# PWA-AI (B‑AI)

A local personal assistant / chatbot project that combines a FastAPI backend, several AI model integrations, local automation helpers, a small desktop GUI (PyQt5), and an optional Progressive Web App frontend. The project is intended to run on a developer machine (Windows recommended) and uses local files for simple inter-process communication between components.

## What this project does

- Exposes a FastAPI backend (`Main.py`) with endpoints for chat, text-to-speech and speech-to-text.
- Uses a decision-making model (Cohere) to classify incoming queries into categories: general, realtime, or automation tasks.
- Provides a Chatbot that can answer general questions via a Groq client and perform realtime search by combining Google search results with Groq.
- Supports image generation via the Hugging Face Inference API (stabilityai/stable-diffusion-xl-base-1.0) triggered by the backend.
- Includes speech components:
  - Speech-to-text powered by a small local browser/web‑speech based helper (Selenium + headless Chrome).
  - Text-to-speech using `edge-tts` and `pygame` to produce and play audio locally.
- Desktop GUI (`frontend/GUI.py`) implemented with PyQt5 that displays conversation and integrates with the file-based IPC used by the backend.
- Optional React PWA (in `frontend/my-pwa`) for browser-based UI.

## High-level architecture

- `Main.py` — entry point and FastAPI app. Calls into the Backend modules:
  - `Backend/Model.py` — First-layer decision maker (Cohere).
  - `Backend/Chatbot.py` — Chat responses (Groq).
  - `Backend/RealtimeSearchEngine.py` — Realtime queries + Google results.
  - `Backend/ImageGeneration.py` — Generates images via Hugging Face API (triggered by writing to Frontend/Files/ImageGeneration.data).
  - `Backend/SpeechToText.py` — Selenium-based speech recognition helper (writes/reads temporary files used by the GUI).
  - `Backend/TextToSpeech.py` — Generates and plays speech audio using edge-tts and pygame.
- `frontend/GUI.py` — desktop UI that reads/writes small data files in `Frontend/Files` for simple coordination with backend scripts.

IPC / temporary files used (under `Frontend/Files`):
- `Mic.data` — microphone status toggles
- `Status.data` — assistant status text (used by GUI)
- `Responses.data` — textual responses the GUI reads and displays
- `ImageGeneration.data` — trigger for image generation (format: <prompt>,True)

Data files:
- `Data/ChatLog.json` — conversation history used by chatbot and realtime engine.

## Prerequisites

- Windows 10/11 (project developed with Windows in mind).
- Python 3.10+ (codebase contains CPython 3.13 artifacts; 3.10–3.13 should work but match your installed packages).
- Node.js + npm (only if you intend to run the React PWA in `frontend/my-pwa`).
- Google Chrome for Selenium-based speech-to-text.

## Python dependencies

All Python dependencies are listed in `requirements.txt`. Install them into a virtual environment:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

If you encounter binary wheel issues on Windows (PyQt5, pygame), install matching wheel builds for your Python version or use a supported Python version (3.10–3.11 typically has broader wheel availability).

## Environment (.env) variables

Create a `.env` file in the project root (the repo already ignores `.env`). Populate the following keys (these are the names used across the backend modules):

- `CohereAPIKey` — API key for Cohere (used by `Backend/Model.py`).
- `GroqAPIKey` — API key for Groq (used by `Backend/Chatbot.py` and `RealtimeSearchEngine.py`).
- `HuggingFaceAPIKey` — Bearer token for Hugging Face inference (used by `Backend/ImageGeneration.py`).
- `OpenWeatherMapAPIKey` — API key for OpenWeatherMap (optional; used by `Main.py` for weather queries).
- `Username` — Your display name to include in prompts (e.g. `Rajkumar Bhuva`).
- `Assistantname` — Assistant name shown in prompts and GUI (e.g. `Buddy`).
- `InputLanguage` — language code used by the speech helper (e.g. `en` for English, `gu` for Gujarati).
- `AssistantVoice` — voice id for `edge-tts` (for example `en-US-AriaNeural` or other valid Azure Edge voice ids).

Example (.env format, DO NOT commit real keys):

```text
# copy to .env and replace placeholders
CohereAPIKey=YOUR_COHERE_KEY_HERE
GroqAPIKey=YOUR_GROQ_KEY_HERE
HuggingFaceAPIKey=hf_xxx
OpenWeatherMapAPIKey=YOUR_OWM_KEY
Username=Your Name
Assistantname=Buddy
InputLanguage=en
AssistantVoice=en-US-AriaNeural
```

Notes:
- Do not commit `.env` to source control — this repo already lists `.env` in `.gitignore`.
- Keep your keys secret. The README shows the variable names only.

## How to run (development)

1. Activate your virtualenv and install requirements (see above).

2. Start the backend API (FastAPI + uvicorn). From the project root use cmd:

```cmd
REM ensure virtual env is activated
python Main.py

or

uvicorn backend.Main:app --host 0.0.0.0 --port 8000 --reload

```

This runs `uvicorn` from `Main.py` and serves the API at http://0.0.0.0:8000

3. (Optional) Desktop GUI

Open a new terminal with the same virtual environment active and run:

```cmd
python frontend\GUI.py
```

The GUI reads `Frontend/Files/Responses.data` and displays responses. The backend writes to those files or the GUI writes commands — both sides coordinate via these files.

4. (Optional) React PWA frontend

If you want the web PWA UI located in `frontend/my-pwa`:

```cmd
cd frontend\my-pwa
npm install
npm start
```

This runs the React development server (typically http://localhost:3000). The PWA is separate and may need additional wiring to call the FastAPI endpoints.

## API usage examples

Simple curl examples (Windows cmd):

```cmd
curl -X POST -F "prompt=who is the president of the united states" http://127.0.0.1:8000/chat

curl -X POST -F "text=hello world" http://127.0.0.1:8000/tts

REM For STT the endpoint expects an uploaded file; use tools or the GUI frontend to upload audio.
```

## Important implementation details

- The decision layer (`Backend/Model.py`) uses Cohere to return a comma-separated list of classified tasks. The main process (`Main.py`) interprets those and either routes to the Chatbot, RealtimeSearchEngine, triggers Automation tasks, or starts ImageGeneration.
- Image generation is triggered by writing a line like: `<prompt>,True` to `Frontend/Files/ImageGeneration.data`. `Main.py` will spawn `Backend/ImageGeneration.py` which calls the Hugging Face inference API and saves images into the `Data/` directory.
- Speech-to-text uses a headless Chrome started by Selenium and `webdriver-manager`. Make sure a compatible Chrome is installed and the virtual environment allows launching Chrome. The `SpeechToText` script writes/reads temporary HTML and files used by the GUI.
- Text-to-speech uses `edge-tts` to save a file at `Data/speech.mp3` and `pygame` to play it. On headless servers or without audio devices it may fail to play.

## Troubleshooting

- Module install errors (PyQt5 / pygame): Use a Python version with prebuilt wheels (3.10/3.11). If pip fails, search for matching wheels or install via conda.
- Selenium / ChromeDriver errors:
  - Ensure Google Chrome is installed. `webdriver-manager` should download the proper driver automatically but mismatched Chrome versions can cause failure.
  - If you see errors in `SpeechToText.py`, run the script directly to view stack traces.
- Hugging Face / API rate limits: The ImageGeneration code posts to the public inference endpoint; you may need an account and token with allowed usage. Large images can be slow or rejected.
- Groq / Cohere auth failures: Make sure keys are set in `.env` and valid. The APIs will raise authorization errors if invalid.
- Uvicorn binding or port in use: if port 8000 is unavailable, modify `Main.py` uvicorn.run parameters or run `uvicorn Main:app --port 8001`.
- GUI shows blank content: confirm `Frontend/Files/Responses.data` is readable and is updated by an API call that writes responses (Main.py writes responses into the `Frontend/Files` under some flows).

## Security & privacy

- This project stores conversation logs in `Data/ChatLog.json`. Do not include private data if you plan to share the repository.
- Keep API keys in `.env` and do not commit them.

## Next steps / improvements

- Replace file-based IPC with a local websocket or HTTP based mechanism for cleaner coordination between GUI and backend.
- Add automated tests for core functions (location parsing, weather, and the decision model glue).
- Provide a minimal frontend integration that calls the FastAPI endpoints directly.

## Where to look in the code

- `Main.py` — entry point and routing logic.
- `Backend/Model.py` — Cohere-based classifier for queries.
- `Backend/Chatbot.py` and `Backend/RealtimeSearchEngine.py` — responsible for LLM responses and augmented realtime search.
- `Backend/ImageGeneration.py` — Hugging Face image generation helper.
- `Backend/SpeechToText.py` — browser-based speech recognition helper.
- `Backend/TextToSpeech.py` — TTS using edge-tts.
- `frontend/GUI.py` — desktop GUI using PyQt5.

---

If you want, I can:
- generate a sample `.env.example` file (without secrets) in the repo,
- add a short script to create the necessary `Frontend/Files` placeholders at first run,
- or add a small test script that calls `/chat` and verifies the service is up.

Tell me which of those you'd like me to create next.
