# Main.py

from .Model import FirstLayerDMM
from .RealtimeSearchEngine import RealtimeSearchEngine
from .Automation import Automation
from .SpeechToText import SpeechRecognitionFromFile
from .Chatbot import ChatBot
from .TextToSpeech import TextToSpeech

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

import requests
import re
import os
import subprocess
from typing import Optional, Tuple, Dict, Any
import signal
import multiprocessing

# NEW: for safe Automation launch inside FastAPI's event loop
import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor

# =========================
# ENV & CONSTANTS
# =========================
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
WeatherAPIKey = env_vars.get("OpenWeatherMapAPIKey", "")
DefaultLocation = env_vars.get("DefaultLocation", "Tempe,AZ,US")

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# =========================
# SAFE AUTOMATION LAUNCHER
# =========================
_executor: Optional[ThreadPoolExecutor] = None

def launch_automation(decision):
    """
    Run Automation(decision) safely from both sync and async contexts:
    - async Automation -> schedule with asyncio.create_task when a loop is running, else asyncio.run
    - sync Automation  -> offload to a thread so we don't block FastAPI's event loop
    """
    global _executor

    if inspect.iscoroutinefunction(Automation):
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(Automation(decision))
            else:
                asyncio.run(Automation(decision))
        except RuntimeError:
            asyncio.run(Automation(decision))
    else:
        try:
            loop = asyncio.get_running_loop()
            if _executor is None:
                _executor = ThreadPoolExecutor(max_workers=2)
            loop.run_in_executor(_executor, Automation, decision)  # fire-and-forget
        except RuntimeError:
            # No running loop (unlikely in FastAPI). As a last resort, call directly.
            Automation(decision) # type: ignore

# =========================
# WEATHER HELPERS (robust)
# =========================
WEATHER_KEYWORDS = {
    "weather", "current weather", "temperature", "temp", "forecast",
    "rain", "snow", "wind", "humidity", "conditions"
}
QUESTION_STOPWORDS = {
    "what", "whats", "what's", "is", "the", "current", "right", "now", "in",
    "today", "please", "tell", "me", "show", "whats", "what’s", "?", "'", "\""
}

STATE_MAP: Dict[str, str] = {
    "arizona": "AZ",
    "az": "AZ",
}

def _clean_str(s: str) -> str:
    s = s.strip()
    s = s.strip(" ?'\".,;:!()[]{}")
    s = re.sub(r"\s+", " ", s)
    return s

def _normalize_location_tokens(tokens):
    norm = []
    for tok in tokens:
        t = tok.lower()
        if t in STATE_MAP:
            norm.append(STATE_MAP[t])
        else:
            norm.append(tok)
    return norm

def canonicalize_location(loc: str) -> str:
    loc = _clean_str(loc)

    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1]
        state = STATE_MAP.get(state.lower(), state.upper())
        if len(parts) == 2:
            return f"{city.title()},{state},US"
        else:
            country = parts[2].upper()
            return f"{city.title()},{state},{country}"

    words = loc.split()
    if len(words) >= 2 and words[-1].lower() in STATE_MAP:
        state = STATE_MAP[words[-1].lower()]
        city = " ".join(words[:-1])
        return f"{city.title()},{state},US"

    return loc.title()

def extract_location_from_query(query: str) -> Optional[str]:
    """
    Extract a location from free-text queries like:
      - "What is weather in Tempe?"
      - "current weather Tempe Arizona"
      - "what’s the weather right now in 'Tempe, AZ'?"
      - "'Tempe, AZ' weather"
    Returns a string suitable for OWM geocoding, e.g. "Tempe,AZ,US".
    """
    q = _clean_str(query)

    # in <location>
    m = re.search(r"\bin\s+(.+)$", q, flags=re.IGNORECASE)
    if m:
        loc = _clean_str(m.group(1)).strip("'\"")
        if loc:
            return canonicalize_location(loc)

    # "quoted location"
    m2 = re.search(r"[\"']([^\"']+)[\"']", q)
    if m2:
        loc = _clean_str(m2.group(1))
        if loc:
            return canonicalize_location(loc)

    # strip weather words & stopwords
    tokens = [t for t in re.split(r"\s+", q) if t]
    tokens = [t.strip(" '\".,;:!?()[]{}") for t in tokens if t.strip(" '\".,;:!?()[]{}")]

    filtered = []
    for t in tokens:
        tl = t.lower()
        if tl in WEATHER_KEYWORDS or tl in QUESTION_STOPWORDS:
            continue
        filtered.append(t)

    if not filtered:
        return None

    filtered = _normalize_location_tokens(filtered)
    loc = _clean_str(" ".join(filtered))
    return canonicalize_location(loc)

def geocode_location(q: str) -> Optional[Tuple[float, float, str]]:
    if not WeatherAPIKey:
        return None
    url = "https://api.openweathermap.org/geo/1.0/direct"
    try:
        resp = requests.get(url, params={"q": q, "limit": 1, "appid": WeatherAPIKey}, timeout=10)
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        item: Dict[str, Any] = data[0]
        lat = item.get("lat")
        lon = item.get("lon")
        name = item.get("name", "")
        state = item.get("state", "")
        country = item.get("country", "")
        if lat is None or lon is None:
            return None
        label_parts = [p for p in [name, state, country] if p]
        return (float(lat), float(lon), ", ".join(label_parts))
    except Exception:
        return None

def fetch_weather_by_coords(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    if not WeatherAPIKey:
        return None
    url = "https://api.openweathermap.org/data/2.5/weather"
    try:
        resp = requests.get(url, params={"lat": lat, "lon": lon, "appid": WeatherAPIKey, "units": "metric"}, timeout=10)
        return resp.json()
    except Exception:
        return None

def format_weather_response(label: str, payload: Optional[Dict[str, Any]]) -> str:
    if not payload or payload.get("cod") != 200:
        return f"Could not get weather for {label}."
    main = payload.get("main", {}) or {}
    weather_list = payload.get("weather", []) or []
    wind = payload.get("wind", {}) or {}
    temp = main.get("temp")
    feels = main.get("feels_like")
    hum = main.get("humidity")
    desc = (weather_list[0]["description"].capitalize() if weather_list else "Conditions unavailable")
    wind_spd = wind.get("speed")

    parts = [f"The current weather in {label} is {temp}°C ({desc})."]
    if feels is not None:
        parts.append(f"Feels like {feels}°C")
    if hum is not None:
        parts.append(f"Humidity {hum}%")
    if wind_spd is not None:
        parts.append(f"Wind {wind_spd} m/s")
    return ", ".join(parts) + "."

def get_weather(query: str) -> str:
    if not WeatherAPIKey:
        return "Weather API key not set. Please add OpenWeatherMapAPIKey to your .env."

    loc_str: Optional[str] = extract_location_from_query(query)
    if not loc_str:
        loc_str = DefaultLocation  # ensure a non-None string

    geo = geocode_location(loc_str) # type: ignore
    if not geo:
        return f"Could not find weather for {loc_str}."

    lat, lon, label = geo
    wx = fetch_weather_by_coords(lat, lon)
    return format_weather_response(label, wx)

# =========================
# CORE AI
# =========================
def process_query(Query: str) -> str:
    """
    Handles AI decision making for both general & realtime queries.
    Weather is handled directly via OpenWeatherMap APIs.
    """
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    # Weather first (direct API)
    if any(k in Query.lower() for k in ["weather", "temperature", "forecast"]):
        return get_weather(Query)

    Decision = FirstLayerDMM(Query)

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    # Force realtime for certain keywords
    if any(word in Query.lower() for word in ["time", "today", "news"]):
        R = True
        G = False
        Decision = [f"realtime {Query}"]

    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    # Image generation side-effects (kept as in your code)
    for queries in Decision:
        if "generate" in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                # SAFE: no asyncio.run() inside FastAPI
                launch_automation(list(Decision))
                TaskExecution = True

    if ImageExecution:
        try:
            os.makedirs(r"Frontend\Files", exist_ok=True)
            with open(r"Frontend\Files\ImageGeneration.data", "w", encoding="utf-8") as file:
                file.write(f"{ImageGenerationQuery},True")
            p1 = subprocess.Popen(
                ['python', r'ImageGeneration.py'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, shell=False
            )
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

        if G and R or R:
            return RealtimeSearchEngine(Query)

    # Automation answers first
    for Queries in Decision:
        if any(Queries.startswith(func) for func in Functions):
            try:
                asyncio.run(Automation(list(Decision)))
                return f"Executing: {Queries}"
            except Exception as e:
                # Fallback to browser if app not found
                import webbrowser
                search_term = Queries.replace("open", "").replace("close", "").strip()
                if search_term:
                    webbrowser.open(f"https://www.google.com/search?q={search_term}")
                    return f"Could not open {search_term} as an app. Opened in browser instead."
                else:
                    return f"Automation failed: {e}"

    # General / Realtime answers
    for Queries in Decision:
        if "general" in Queries:
            QueryFinal = Queries.replace("general", "")
            return ChatBot(QueryFinal)
        elif "realtime" in Queries:
            QueryFinal = Queries.replace("realtime", "")
            return RealtimeSearchEngine(QueryFinal)
        elif "exit" in Queries:
            return "Okay, Bye!"

    return "No valid action detected."

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="B-AI API", version="1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(prompt: str = Form(...)):
    Answer = process_query(prompt)
    return {"response": Answer}

processes = {}

def run_stt(path, queue):
    try:
        text = SpeechRecognitionFromFile(path)
        queue.put(text)
    except Exception as e:
        queue.put(f"Error: {e}")

@app.post("/stt")
async def speech_to_text_endpoint(file: UploadFile = File(...)):
    temp_path = f"Data/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        text = SpeechRecognitionFromFile(temp_path)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/tts")
async def text_to_speech_endpoint(text: str = Form(...)):
    audio_path = TextToSpeech(text)
    return {"audio_file": audio_path}

# Keep track of subprocesses
running_processes = []

@app.post("/stop")
async def stop_process():
    killed = 0
    for pid, proc_info in list(processes.items()):
        if proc_info["process"].is_alive():
            proc_info["process"].terminate()
            killed += 1
        del processes[pid]
    return {"status": "stopped", "killed": killed}
    

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Main:app", host="0.0.0.0", port=8000, reload=True)
