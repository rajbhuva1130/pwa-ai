# Automation.py

from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit.misc import search, playonyt  # fixed import path
from dotenv import dotenv_values
from urllib.parse import quote
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import requests
import subprocess
import keyboard
import asyncio
import os
import re
from typing import List, Dict

# --- Load environment variables ---
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# --- Constants ---
classes = [
    "zCubwf", "hgKElc", "LTKOO sY7ric", "ZOLcW",
    "gsrt vk_bk FzvWSb YwPhnf", "pclqee",
    "tw-data-text tw-text-small tw-ta", "IZ6rdc", "05uR6d LTKOO",
    "vlzY6d", "webanswers-webanswers_table_webanswers-table",
    "dDoNo ikb4Bb gsrt", "sXLa0e", "LWkfKe", "VQF4g",
    "qv3Wpe", "kno-rdesc", "SPZz6b"
]
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

# --- Groq client ---
client = Groq(api_key=GroqAPIKey)

# --- Globals ---
messages: List[Dict[str, str]] = []
SystemChatBot = [
    {
        "role": "system",
        "content": f"Hello, I am {os.environ.get('Username')}. "
                   "You're a content writer. You have to write content, like letters, codes, applications, essays, notes, songs, poem etc."
    }
]

# ---------- NEW: Friendly names → official URLs (browser fallback) ----------
APP_URLS: Dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "yt": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "maps": "https://maps.google.com",
    "drive": "https://drive.google.com",
    "calendar": "https://calendar.google.com",
    "meet": "https://meet.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "slides": "https://slides.google.com",
    "chatgpt": "https://chat.openai.com",
    "whatsapp": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "prime video": "https://www.primevideo.com",
    "discord": "https://discord.com/app",
    "slack": "https://slack.com/signin",
    "teams": "https://teams.microsoft.com",
    "onedrive": "https://onedrive.live.com",
    "outlook": "https://outlook.live.com/mail",
    "office": "https://www.office.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://github.com",
    "gitlab": "https://gitlab.com",
    "notion": "https://www.notion.so",
    "figma": "https://www.figma.com/files",
    "canva": "https://www.canva.com",
}

# --- Helper: normalize messages for Groq ---
def normalize_messages(msgs):
    fixed = []
    for m in msgs:
        role = m.get("role", "").lower()
        if role not in ["system", "user", "assistant"]:
            role = "user"
        fixed.append({"role": role, "content": m.get("content", "")})
    return fixed

# --- Core functions ---
def GoogleSearch(topic):
    search(topic)
    return True

def Content(topic):
    """Generate content using Groq AI and save to file."""
    def OpenNotepad(file_path):
        subprocess.Popen(["notepad.exe", file_path])

    def ContentAI(prompt):
        formatted_msgs = normalize_messages(SystemChatBot + messages)
        formatted_msgs.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=formatted_msgs,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content

        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})
        return answer

    clean_topic = topic.replace("Content", "").strip()
    content_by_ai = ContentAI(clean_topic)

    file_path = rf"Data\{clean_topic.lower().replace(' ', '')}.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content_by_ai)

    OpenNotepad(file_path)
    return True

def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webopen(url)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

# ---------- NEW: safer fallback if local app not found ----------
def _best_url_for_app(name: str) -> str:
    key = name.lower().strip()
    # direct match
    if key in APP_URLS:
        return APP_URLS[key]
    # fuzzy partial match
    for k, url in APP_URLS.items():
        if k in key or key in k:
            return url
    # default to Google search
    query = name
    return f"https://www.google.com/search?q={quote(query)}"

def OpenApp(app_name, sess=requests.session()):
    """
    Try to open a local desktop app using AppOpener.
    If not present, fall back to opening the official web app (or Google search) in the browser.
    """
    name = app_name.strip().strip("\"'")  # sanitize quotes
    try:
        # Attempt local app open (AppOpener does fuzzy matching with match_closest=True)
        appopen(name, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as app_open_error:
        print(f"[OpenApp] AppOpener failed for '{name}': {app_open_error}")

        # 1) Known web app?
        url = _best_url_for_app(name)
        try:
            webopen(url)
            print(f"[OpenApp] Opened in browser: {url}")
            return True
        except Exception as e:
            print(f"[OpenApp] Browser open failed: {e}")

        # 2) (Optional) Try a lightweight HTML extraction path if you really want first result.
        #    Keeping your original logic, but only as a last-ditch fallback.
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            # Try general link extraction if jsname selector fails
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            # Filter to https
            links = [l for l in links if l and l.startswith("http")]
            return links

        def search_google(query):
            url = f"https://www.google.com/search?q={quote(query)}"
            headers = {"User-Agent": useragent}
            try:
                response = sess.get(url, headers=headers, timeout=8)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"[OpenApp] Google search failed: {e}")
                return None

        html = search_google(name)
        if html:
            links = extract_links(html)
            if links:
                try:
                    webopen(links[0])
                    print(f"[OpenApp] Fallback opened first result: {links[0]}")
                    return True
                except Exception as e:
                    print(f"[OpenApp] Fallback browser open failed: {e}")

        return False

def CloseApp(app_name):
    if "chrome" in app_name.lower():
        return False
    try:
        close(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

def System(command):
    cmd = command.lower().strip()
    if cmd == "mute":
        keyboard.press_and_release("volume mute")
    elif cmd == "unmute":
        keyboard.press_and_release("volume mute")
    elif cmd == "volume up":
        keyboard.press_and_release("volume up")
    elif cmd == "volume down":
        keyboard.press_and_release("volume down")
    return True

# --- Async command executor ---
async def TranslateAndExecute(commands: List[str]):
    funcs = []
    for command in commands:
        c = command.strip()
        if c.startswith("open") and "open it" not in c and "open file" != c:
            funcs.append(asyncio.to_thread(OpenApp, c.removeprefix("open ").strip()))
        elif c.startswith("close"):
            funcs.append(asyncio.to_thread(CloseApp, c.removeprefix("close ").strip()))
        elif c.startswith("play"):
            funcs.append(asyncio.to_thread(PlayYoutube, c.removeprefix("play ").strip()))
        elif c.startswith("content"):
            funcs.append(asyncio.to_thread(Content, c.removeprefix("content ").strip()))
        elif c.startswith("google search"):
            funcs.append(asyncio.to_thread(GoogleSearch, c.removeprefix("google search ").strip()))
        elif c.startswith("youtube search"):
            funcs.append(asyncio.to_thread(YouTubeSearch, c.removeprefix("youtube search ").strip()))
        elif c.startswith("system"):
            funcs.append(asyncio.to_thread(System, c.removeprefix("system ").strip()))
        else:
            print(f"[Automation] No Function Found. For command: {command}")

    if funcs:
        results = await asyncio.gather(*funcs, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                print(f"[Automation] Task error: {r}")
            else:
                yield r
    else:
        # nothing to do, but keep generator contract
        if False:
            yield None

async def Automation(commands: List[str]):
    async for _ in TranslateAndExecute(commands):
        pass
    return True

# --- Quick test ---
if __name__ == "__main__":
    # Examples:
    #  - first will try local "calculator" (may succeed on Windows via AppOpener)
    #  - second will fall back to opening YouTube in the browser if the app isn't installed
    asyncio.run(Automation([
        "open calculator",
        "open youtube",
        "open spotify",
        "open something-that-does-not-exist-abc"
    ]))
