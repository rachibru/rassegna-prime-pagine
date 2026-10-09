import os
import time
import datetime
import json
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
data_oggi_str = datetime.datetime.now().strftime("%d/%m/%Y")
data_iso = datetime.datetime.now().strftime("%Y-%m-%d")
data_yyyymmdd = datetime.datetime.now().strftime("%Y%m%d")

client = genai.Client(api_key=GEMINI_API_KEY)

IMMAGINE_PRINCIPALE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

# 3. Recupero Prime Pagine da Link Diretti & Dinamici
def recupera_prime_pagine():
    candidate_urls = [
        # Corriere della Sera
        "https://static2.rcsobjects.it/images/corrierefc_nazionale_web-Big.jpg",
        
        # La Stampa
        "https://www.lastampa.it/edicola/api/cover.php?newspaper=LASTAMPA&edition=TORINO&width=330&height=450",
        
        # Il Sole 24 Ore (URL Dinamico)
        f"https://mobapp2.ilsole24ore.com/_deploy/S24/{data_yyyymmdd}/SOLE/{data_yyyymmdd}083258000/covers/cover_high.jpg",
        
        # Il Secolo XIX
        "https://www.gelestatic.it/storage/quotidiani-locali/testate/copertina_ilsecoloxix_genova_w510.jpeg",
        
        # Il Foglio
        "https://eu01.newsmemory.com/?pSetup=ilfoglio&getprima&editionname=Il%20Foglio",
        
        # Il Giornale (NewsMemory CDN)
        f"https://eu1-bcdn.newsmemory.com//default_native_optionspage.php?os=web&isDebug=false&pSetup=ilgiornale&version=1.11.3&action=issueImage&type=text&issue={data_yyyymmdd}&edition=Nazionale",
        
        # Libero (NewsMemory CDN)
        f"https://eu1-bcdn.newsmemory.com//default_native_optionspage.php?os=web&isDebug=false&pSetup=libero&version=1.11.3&action=issueImage&type=text&issue={data_yyyymmdd}&edition=Libero"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    immagini_valide = []

    # Verifica validità URL
    for url in candidate_urls:
        try:
            res = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            if res.status_code == 200:
                immagini_valide.append(url)
            else:
                res_get = requests.get(url, headers=headers, timeout=5, stream=True)
                if res_get.status_code == 200:
                    immagini_valide.append(url)
        except Exception as e:
            print(f"⚠️ Impossibile verificare {url}: {e}")

    # Fallback tramite scraping se le edicole dirette sono temporaneamente offline
    if len(immagini_valide) < 3:
        try:
            res = requests.get("https://www.giornali.it/prime-pagine/", headers=headers, timeout=8)
            soup = BeautifulSoup(res.text, 'html.parser')
            for img in soup.find_all('img', limit=10):
                src = img.get('src') or img.get('data-src')
                if src and any(ext in src for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if not src.startswith('http'):
                        src = "https:" + src if src.startswith('//') else "https://www.giornali.it" + src
                    if src not in immagini_valide and 'logo' not in src:
                        immagini_valide.append(src)
        except Exception as e:
            print(f"⚠️ Scraping fallback fallito: {e}")

    # Costruzione Blocco HTML Galleria
    if immagini_valide:
        html_foto = """
        <div style='margin-top: 35px; border-top: 2px solid #eee; padding-top: 20px;'>
          <h3 style='color: #1a252f; font-size: 20px; margin-bottom: 15px; text-align: center;'>📷 Le Prime Pagine dei Quotidiani di Oggi</h3>
          <div style='display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;'>
        """
        for img_url in immagini_valide:
            html_foto += f"""
            <div style='background: #fff; padding: 6px; border: 1px solid #ddd; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); max-width: 230px;'>
              <img src='{img_url}' style='width: 100%; height: auto; border-radius: 4px; display: block;' alt='Prima Pagina Quotidiano' />
            </div>
            """
        html_foto += "</div></div>"
        return html_foto

    return ""

foto_html = recupera_prime_pagine()

# 4. Schema.org JSON-LD per Indicizzazione
schema_json = {
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": f"https://brunorachiele.blogspot.com/{data_iso}-rassegna-stampa"
  },
  "headline": f"Rassegna Stampa & Analisi Politica - {data_oggi_str}",
  "image": [IMMAGINE_PRINCIPALE],
  "datePublished": f"{data_iso}T06:00:00+02:00",
  "dateModified": f"{data_iso}T06:00:00+02:00",
  "author": {
    "@type": "Person",
    "name": "Bruno Rachiele",
    "jobTitle": "Editor politico",
    "url": "https://brunorachiele.blogspot.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Rassegna Stampa & Analisi Politica",
    "logo": {
      "@type": "ImageObject",
      "url": IMMAGINE_PRINCIPALE
    }
  },
  "description": f"Analisi politica quotidiana e rassegna stampa del {data_oggi_str} a cura di Bruno Rachiele. Focus su governo, economia e stampa internazionale."
}

schema_html = f'<script type="application/ld+json">\n{json.dumps(schema_json, indent=2)}\n</script>'

# Header con Immagine
header_html = f"""
<div style="text-align: center; margin-bottom: 25px;">
  <img src="{IMMAGINE_PRINCIPALE}" alt="Rassegna Stampa Politica" style="width: 100%; max-height: 350px; object-fit: cover; border-radius: 8px;" />
</div>
"""

# 5. Prompt per Generazione Testo (Linea Editoriale & Stampa Estera)
prompt = f"""
Sei un autorevole giornalista ed editor politico d'area conservatrice e di centrodestra (vicino alla linea del Governo Meloni).
Elabora un commento analitico e una rassegna sintetica delle prime pagine dei quotidiani di oggi ({data_oggi_str}).

Mantieni uno stile autorevole, lucido e professionale, valorizzando la stabilità dell'esecutivo, il pragmatismo delle riforme economiche e la difesa dell'interesse nazionale.

Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza tag <html> o <body>) rispettando esattamente questa struttura e stili inline:

<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #2c3e50; max-width: 800px; margin: 0 auto; padding: 10px; line-height: 1.6;">
  <h2 style="color: #1a252f; border-bottom: 2px solid #003366; padding-bottom: 8px; margin-bottom: 20px;">🗞️ Rassegna Stampa & Analisi Politica - {data_oggi_str}</h2>
  
  <!-- Tema Centrale -->
  <div style="background: #f8f9fa; border-left: 4px solid #003366; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
    <h3 style="margin-top:0; color: #003366;">📌 Il Tema Centrale del Giorno</h3>
    <p>[Analisi del fatto politico principale della giornata con focus sulle riforme, l'azione del Governo Meloni e la stabilità del Paese]</p>
  </div>

  <!-- Punti di Vista Quotidiani Italiani -->
  <div style="background: #f8f9fa; border-left: 4px solid #e67e22; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
    <h3 style="margin-top:0; color: #2c3e50;">📊 I Punti di Vista della Stampa
