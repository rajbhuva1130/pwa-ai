from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
import time

# Load environment variables
env_vars = dotenv_values(".env")
Inputlanguage = env_vars.get("InputLanguage") or "en"

def QueryModifier(Query):
    new_query = Query.lower().strip()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    if any(word + " " in new_query for word in question_words):
        return new_query.rstrip(".?!") + "?"
    else:
        return new_query.rstrip(".?!") + "."

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

def SpeechRecognitionFromFile(file_path: str):
    """Run Selenium webkitSpeechRecognition on a given audio file."""
    # Create temporary HTML that auto-plays audio
    HtmlCode = f'''<!DOCTYPE html>
    <html lang="en">
    <body>
        <audio id="player" autoplay>
            <source src="file:///{file_path}" type="audio/wav">
        </audio>
        <p id="output"></p>
        <script>
            const output = document.getElementById('output');
            let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = '{Inputlanguage}';
            recognition.continuous = false;
            recognition.onresult = function(event) {{
                const transcript = event.results[0][0].transcript;
                output.textContent = transcript;
            }};
            recognition.start();
        </script>
    </body>
    </html>'''

    html_path = os.path.join("Data", "VoiceFromFile.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HtmlCode)

    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("file:///" + os.path.abspath(html_path))

        # Wait up to 10 seconds for result
        for _ in range(20):
            try:
                text = driver.find_element(By.ID, "output").text
                if text:
                    if "en" in Inputlanguage.lower():
                        return QueryModifier(text)
                    else:
                        return QueryModifier(UniversalTranslator(text))
            except Exception:
                pass
            time.sleep(0.5)
        return ""
    finally:
        driver.quit()  # ✅ Always close Chrome
