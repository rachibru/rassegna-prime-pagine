import os
import datetime
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# 1. Recupera le credenziali da GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# Controllo credenziali essenziali
if not GEMINI_API_KEY or not BLOGGER_EMAIL or not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("❌ Errore: Uno o più Secrets su GitHub non sono impostati correttamente!")

# 2. Configura Gemini IA
genai.configure(api_key=GEMINI_API_KEY)
data_oggi = datetime.datetime.now().strftime("%d/%m/%Y")

# 3. Recupera le immagini delle prime pagine del giorno
def recupera_prime_pagine():
    html_foto = "<h3>📷 Le Prime Pagine di Oggi</h3><div style='display:flex; flex-wrap:wrap; gap:10px;'>"
    try:
        url = "https://www.giornali.it/prime-pagine/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
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
        print(f"⚠️ Impossibile recuperare le immagini: {e}")
        return ""

foto_html = recupera_prime_pagine()

# 4. Prompt per la rassegna di Gemini
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

# Utilizza il modello aggiornato di Gemini
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    html_content = response.text
except Exception as e:
    print(f"Tentativo con gemini-2.5-flash fallito ({e}), provo con gemini-1.5-flash...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    html_content = response.text

# Unisce le foto recuperate al commento dell'IA
contenuto_finale = html_content + "<hr/>" + foto_html

# 5. Invia l'email a Blogger per la pubblicazione
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi}"

msg.attach(MIMEText(contenuto_finale, 'html'))

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, server.as_string())
    server.quit()
    print("✅ Rassegna e foto inviate con successo a Blogger!")
except Exception as e:
    print(f"❌ Errore durante l'invio SMTP: {e}")
    raise e
