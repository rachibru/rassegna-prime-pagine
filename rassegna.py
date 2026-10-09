import os
import time
import datetime
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# 1. Credenziali
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

if not all([GEMINI_API_KEY, BLOGGER_EMAIL, SENDER_EMAIL, SENDER_PASSWORD]):
    raise ValueError("❌ Uno o più Secrets non sono stati configurati su GitHub!")

# 2. Setup Data e Client
data_oggi = datetime.datetime.now().strftime("%d/%m/%Y")
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. Scraping prime pagine
def recupera_prime_pagine():
    html_foto = """
    <div style='margin-top: 30px;'>
      <h3 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;'>📷 Le Prime Pagine di Oggi</h3>
      <div style='display:flex; flex-wrap:wrap; gap:15px; margin-top: 15px;'>
    """
    try:
        url = "https://www.giornali.it/prime-pagine/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        images = soup.find_all('img', limit=6)
        found = False
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src and ('jpg' in src or 'png' in src or 'webp' in src):
                if not src.startswith('http'):
                    src = "https:" + src if src.startswith('//') else url + src
                html_foto += f"<div style='margin-bottom:15px;'><img src='{src}' style='max-width:100%; height:auto; border:1px solid #ccc; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);' /></div>"
                found = True
        html_foto += "</div></div>"
        return html_foto if found else ""
    except Exception as e:
        print(f"⚠️ Errore foto: {e}")
        return ""

foto_html = recupera_prime_pagine()

# 4. Prompt HTML
prompt = f"""
Sei un giornalista politico ed editor-in-chief.
Elabora un commento e una rassegna sintetica delle prime pagine dei principali quotidiani italiani di oggi ({data_oggi}).

Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza tag <html> o <body>) mantenendo esattamente questa struttura e questi stili inline:

<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #2c3e50; max-width: 800px; margin: 0 auto; padding: 10px; line-height: 1.6;">
  <h2 style="color: #1a252f; border-bottom: 2px solid #e74c3c; padding-bottom: 8px; margin-bottom: 20px;">🗞️ Rassegna Stampa & Analisi Politica - {data_oggi}</h2>
  
  <div style="background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
    <h3 style="margin-top:0; color: #2c3e50;">📌 Il Tema Centrale del Giorno</h3>
    <p>[Inserisci qui l'analisi principale e sintetica del fatto del giorno]</p>
  </div>

  <div style="background: #f8f9fa; border-left: 4px solid #e67e22; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
    <h3 style="margin-top:0; color: #2c3e50;">📊 I Punti di Vista delle Testate</h3>
    <ul style="padding-left: 20px; margin-bottom: 0;">
      <li style="margin-bottom: 8px;"><strong>Corriere della Sera e La Repubblica:</strong> [Focus principale sui temi nazionali ed esteri]</li>
      <li style="margin-bottom: 8px;"><strong>La Stampa e Il Secolo XIX:</strong> [Taglio politico, sociale e locale]</li>
      <li style="margin-bottom: 8px;"><strong>Il Foglio e La Ragione:</strong> [Opinioni, commenti ed economia]</li>
      <li style="margin-bottom: 8px;"><strong>Il Sole 24 Ore:</strong> [Analisi finanziaria, mercati e imprese]</li>
    </ul>
  </div>

  <div style="background: #fff8e1; border: 1px solid #ffe082; border-left: 4px solid #f39c12; padding: 18px 20px; font-style: italic; margin-bottom: 25px; border-radius: 0 8px 8px 0;">
    <h3 style="margin-top:0; font-style: normal; color: #d35400;">💡 Il Commento della Redazione</h3>
    <p>"[Inserisci qui la riflessione editoriale finale]"</p>
    <div style="text-align: right; font-weight: bold; font-style: normal; color: #7f8c8d; margin-top: 10px;">— Bruno Rachiele</div>
  </div>

  <div style="background: #eef9f5; border: 1px solid #c8e6c9; padding: 20px; border-radius: 8px;">
    <h4 style="margin-top:0; color: #2e7d32; font-size: 18px;">✉️ Spunti di Analisi per la Newsletter</h4>
    <ol style="padding-left: 20px; margin-bottom: 0;">
      <li style="margin-bottom: 8px;"><strong>Il nodo delle risorse:</strong> [Sintesi punto 1 per la newsletter]</li>
      <li style="margin-bottom: 8px;"><strong>Lo scenario internazionale:</strong> [Sintesi punto 2 per la newsletter]</li>
      <li style="margin-bottom: 8px;"><strong>Cosa cambia per i cittadini:</strong> [Sintesi punto 3 per la newsletter]</li>
    </ol>
  </div>
</div>
"""

# 5. Generazione testo con Scoperta Dinamica dei Modelli Abilitati
print("🧠 Rilevamento modelli disponibili sul tuo account...")

# Elenco dinamico dei modelli gratuiti attivi sulla tua API Key
modelli_abilitati = []
try:
    for m in client.models.list():
        name = m.name.replace("models/", "")
        modelli_abilitati.append(name)
except Exception as e:
    print(f"⚠️ Impossibile elencare i modelli automaticamente: {e}")

# Se la lista automatica fallisce, proviamo con una lista di default
if not modelli_abilitati:
    modelli_abilitati = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-flash']

print(f"📋 Modelli rilevati: {modelli_abilitati}")

response = None
for m in modelli_abilitati:
    for tentativo in range(2):
        try:
            print(f"🔄 Prova con il modello: {m} (tentativo {tentativo + 1})...")
            response = client.models.generate_content(
                model=m,
                contents=prompt,
            )
            if response and response.text:
                print(f"✅ Generazione riuscita con il modello: {m}")
                break
        except Exception as err:
            print(f"❌ Fallito con {m}: {err}")
            time.sleep(3)
    if response and response.text:
        break

if not response or not response.text:
    raise RuntimeError("❌ Nessun modello è riuscito a generare il contenuto. Controlla la validità della tua API Key su Google AI Studio.")

html_content = response.text
contenuto_finale = html_content + "<hr style='margin-top: 30px; border: 0; border-top: 1px solid #ccc;'/>" + foto_html

# 6. Invio via SMTP (Porta 587 con STARTTLS)
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi}"
msg.attach(MIMEText(contenuto_finale, 'html'))

try:
    print("📧 Connessione al server SMTP di Gmail (porta 587)...")
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
    server.ehlo()
    server.starttls()
    server.ehlo()
    print("🔑 Autenticazione in corso...")
    server.login(SENDER_EMAIL.strip(), SENDER_PASSWORD.strip().replace(" ", ""))
    print("📤 Invio messaggio...")
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, msg.as_string())
    server.quit()
    print("✅ RASSEGNA INVIATA E PUBBLICATA CON SUCCESSO!")
except Exception as e:
    print(f"❌ Errore durante l'invio della mail: {e}")
    raise e
