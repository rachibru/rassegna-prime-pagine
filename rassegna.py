import os
import smtplib
import google.generativeai as genai

# 1. Recupero Secret
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

print("🔍 CONTROLLO CREDENZIALI IN CORSO...")

# Test 1: Verifica Gemini API Key
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    res = model.generate_content("Dimmi 'OK'")
    print(f"✅ TEST GEMINI API KEY: RIUSCITO! (Risposta: {res.text.strip()})")
except Exception as e:
    print(f"❌ TEST GEMINI API KEY FALLITO: {e}")

# Test 2: Verifica Connessione Gmail SMTP
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.quit()
    print("✅ TEST GMAIL SMTP: RIUSCITO! Credenziali email corrette.")
except Exception as e:
    print(f"❌ TEST GMAIL SMTP FALLITO: {e}")
