# ImageGeneration.py

import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

# --- Config ---
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

DATA_DIR = r"Data"
TRIGGER_FILE = r"Frontend\Files\ImageGeneration.data"

# --- Helpers ---
def safe_filename(name: str) -> str:
    """Convert prompt into a safe filename."""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.strip())

def open_images(prompt):
    """Open generated images for the given prompt."""
    base_name = safe_filename(prompt)
    files = [f"{base_name}_{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(DATA_DIR, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except FileNotFoundError:
            print(f"File not found: {image_path}")
        except Exception as e:
            print(f"Error opening {image_path}: {e}")

async def query(payload):
    """Send generation request to Hugging Face."""
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content

async def generate_images(prompt: str):
    """Generate 4 images for the given prompt."""
    tasks = []
    safe_prompt = safe_filename(prompt)

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}"
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list, start=1):
        file_path = os.path.join(DATA_DIR, f"{safe_prompt}_{i}.jpg")
        with open(file_path, "wb") as f:
            f.write(image_bytes)

def GenerateImages(prompt: str):
    """Generate and open images for a prompt."""
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# --- Main loop ---
if __name__ == "__main__":
    while True:
        try:
            if not os.path.exists(TRIGGER_FILE):
                sleep(1)
                continue

            with open(TRIGGER_FILE, "r") as f:
                data = f.read().strip()

            if not data or "," not in data:
                sleep(1)
                continue

            prompt, status = data.split(",", 1)
            if status == "True":
                print(f"Generating images for prompt: {prompt}")
                GenerateImages(prompt)

                # Reset trigger
                with open(TRIGGER_FILE, "w") as f:
                    f.write("False,False")
                break
            else:
                sleep(1)

        except Exception as e:
            print(f"Image generation error: {e}")
            sleep(1)
