import os
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

# 2. Setup Data e Client
data_oggi = datetime.datetime.now().strftime("%d/%m/%Y")
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. Scraping Immagini
def recupera_prime_pagine():
    html_foto = "<h3>📷 Le Prime Pagine di Oggi</h3><div style='display:flex; flex-wrap:wrap; gap:10px;'>"
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
                html_foto += f"<div style='margin-bottom:15px;'><img src='{src}' style='max-width:100%; height:auto; border:1px solid #ccc; border-radius:5px;' /></div>"
                found = True
        html_foto += "</div>"
        return html_foto if found else ""
    except Exception as e:
        print(f"⚠️ Errore foto: {e}")
        return ""

foto_html = recupera_prime_pagine()

# 4. Prompt
prompt = f"""
Sei un giornalista politico ed editor-in-chief.
Elabora un commento e una rassegna sintetica delle prime pagine dei principali quotidiani italiani di oggi ({data_oggi}).

Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza <html> o <body>).
Struttura il testo così:
<h3>🗞️ Il Tema Centrale di Oggi</h3>
<p>[Analisi del fatto principale sui giornali]</p>

<h3>📊 I Punti di Vista delle Testate</h3>
<ul>
  <li><strong>Corriere e Repubblica:</strong> [Focus principale]</li>
  <li><strong>La Stampa e Il Secolo XIX:</strong> [Taglio politico/sociale]</li>
  <li><strong>Il Foglio e La Ragione:</strong> [Opinioni e commenti]</li>
</ul>

<h3>💡 Il Commento della Redazione</h3>
<p>[Riflessione finale di Bruno Rachiele]</p>
"""

# 5. Generazione Testo con Fallback Modello
print("🧠 Generazione testo...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
except Exception as e:
    print(f"⚠️ Fallback modello a causa di: {e}")
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt,
    )

html_content = response.text
contenuto_finale = html_content + "<hr/>" + foto_html

# 6. Invio Email SSL (Porta 465)
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi}"
msg.attach(MIMEText(contenuto_finale, 'html'))

try:
    print("📧 Invio email a Blogger...")
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, server.as_string())
    server.quit()
    print("✅ PUBBLICAZIONE RIUSCITA!")
except Exception as e:
    print(f"❌ Errore SMTP: {e}")
    raise e
