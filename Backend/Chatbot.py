# Chatbot.py

from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

# --- Load environment variables ---
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# --- Groq client ---
client = Groq(api_key=GroqAPIKey)

# --- Globals ---
messages = []

# --- System prompt ---
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [{"role": "system", "content": System}]

# --- Ensure chat log file exists ---
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# --- Helpers ---
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    return (
        f"Please use this real-time information if needed,\n"
        f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
        f"Time: {hour} hours : {minute} minutes : {second} seconds.\n"
    )

def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def normalize_messages(msgs):
    """Ensure messages list is in correct Groq API format."""
    fixed = []
    for m in msgs:
        role = m.get("role", "").lower()
        if role not in ["system", "user", "assistant"]:
            role = "user"
        fixed.append({"role": role, "content": m.get("content", "")})
    return fixed

# --- Main chatbot function ---
def ChatBot(query):
    try:
        # Load chat history
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        # Append user's message
        messages.append({"role": "user", "content": f"{query}"})

        # Prepare messages for Groq
        formatted_msgs = normalize_messages(
            SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages
        )

        # Call Groq API
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # change to llama3-70b-8192 if needed
            messages=formatted_msgs,
            max_tokens=1024,
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

        # Save updated chat log
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(answer)

    except Exception as e:
        print(f"Error: {e}")
        # Reset chat log if something goes wrong
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(query)

# --- Test mode ---
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))
