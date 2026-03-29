# This file is to not be pushed

from google import genai

# Initialize client
client = genai.Client(api_key="AIzaSyA1oqF9bFoWXpt9iRo_5dPM42CNnre3dsk")

# Fetch and print available models
for model in client.models.list():
    print(f"Model ID: {model.name}")