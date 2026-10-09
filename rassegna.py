import os
import datetime
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# 1. Recupera le credenziali dai secrets di GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

if not all([GEMINI_API_KEY, BLOGGER_EMAIL, SENDER_EMAIL, SENDER_PASSWORD]):
    raise ValueError("❌ Uno o più Secrets non sono stati configurati su GitHub!")

# 2. Inizializzazione della data e del client Gemini
data_oggi = datetime.datetime.now().strftime("%d/%m/%Y")
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. Scraping delle prime pagine di giornali.it
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
        print(f"⚠️ Errore durante lo scraping delle foto: {e}")
        return ""

foto_html = recupera_prime_pagine()

# 4. Prompt per generare la struttura HTML desiderata
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

# 5. Generazione testo tramite Gemini con fallback dinamico
print("🧠 Generazione testo in corso...")

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )
    html_content = response.text
except Exception as e:
    print(f"⚠️ Modello predefinito non disponibile ({e}). Ricerca automatica in corso...")
    
    modelli_disponibili = []
    try:
        for m in client.models.list():
            if hasattr(m, "supported_generation_methods") and "generateContent" in m.supported_generation_methods:
                modelli_disponibili.append(m.name)
            elif hasattr(m, "supported_actions") and "generateContent" in m.supported_actions:
                modelli_disponibili.append(m.name)
    except Exception as list_err:
        print(f"Impossibile recuperare l'elenco dei modelli: {list_err}")

    modello_scelto = modelli_disponibili[0] if modelli_disponibili else 'gemini-1.5-flash-8b'
        
    print(f"🔄 Utilizzo il modello alternativo: {modello_scelto}")
    response = client.models.generate_content(
        model=modello_scelto,
        contents=prompt,
    )
    html_content = response.text

# Unione del testo generato e delle immagini delle prime pagine
contenuto_finale = html_content + "<hr style='margin-top: 30px; border: 0; border-top: 1px solid #ccc;'/>" + foto_html

# 6. Invio via SMTP SSL (Porta 465)
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi}"
msg.attach(MIMEText(contenuto_finale, 'html'))

try:
    print("📧 Invio email a Blogger tramite SSL (porta 465)...")
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, server.as_string())
    server.quit()
    print("✅ Rassegna inviata con successo!")
except Exception as e:
    print(f"❌ Errore durante l'invio della mail: {e}")
    raise e
