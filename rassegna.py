import os
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Stampa tutti i modelli a cui la tua chiave ha accesso
for m in client.models.list():
    print(m.name)
