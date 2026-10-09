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
        "https://static2.rcsobjects.it/images/corrierefc_nazionale_web-Big.jpg",
        "https://www.lastampa.it/edicola/api/cover.php?newspaper=LASTAMPA&edition=TORINO&width=330&height=450",
        f"https://mobapp2.ilsole24ore.com/_deploy/S24/{data_yyyymmdd}/SOLE/{data_yyyymmdd}083258000/covers/cover_high.jpg",
        "https://www.gelestatic.it/storage/quotidiani-locali/testate/copertina_ilsecoloxix_genova_w510.jpeg",
        "https://eu01.newsmemory.com/?pSetup=ilfoglio&getprima&editionname=Il%20Foglio",
        f"https://eu1-bcdn.newsmemory.com//default_native_optionspage.php?os=web&isDebug=false&pSetup=ilgiornale&version=1.11.3&action=issueImage&type=text&issue={data_yyyymmdd}&edition=Nazionale",
        f"https://eu1-bcdn.newsmemory.com//default_native_optionspage.php?os=web&isDebug=false&pSetup=libero&version=1.11.3&action=issueImage&type=text&issue={data_yyyymmdd}&edition=Libero"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    immagini_valide = []

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

header_html = f"""
<div style="text-align: center; margin-bottom: 25px;">
  <img src="{IMMAGINE_PRINCIPALE}" alt="Rassegna Stampa Politica" style="width: 100%; max-height: 350px; object-fit: cover; border-radius: 8px;" />
</div>
"""

# 5. Prompt pulito senza errori di sintassi
prompt = (
    "Sei un autorevole giornalista ed editor politico d'area conservatrice e di centrodestra (vicino alla linea del Governo Meloni).\n"
    f"Elabora un commento analitico e una rassegna sintetica delle prime pagine dei quotidiani di oggi ({data_oggi_str}).\n\n"
    "Mantieni uno stile autorevole, lucido e professionale, valorizzando la stabilità dell'esecutivo, il pragmatismo delle riforme economiche e la difesa dell'interesse nazionale.\n\n"
    "Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza tag <html> o <body>) rispettando esattamente questa struttura e stili inline:\n\n"
    "<div style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #2c3e50; max-width: 800px; margin: 0 auto; padding: 10px; line-height: 1.6;\">\n"
    f"  <h2 style=\"color: #1a252f; border-bottom: 2px solid #003366; padding-bottom: 8px; margin-bottom: 20px;\">🗞️ Rassegna Stampa & Analisi Politica - {data_oggi_str}</h2>\n\n"
    "  <div style=\"background: #f8f9fa; border-left: 4px solid #003366; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #003366;\">📌 Il Tema Centrale del Giorno</h3>\n"
    "    <p>[Analisi del fatto politico principale della giornata con focus sulle riforme, l'azione del Governo Meloni e la stabilità del Paese]</p>\n"
    "  </div>\n\n"
    "  <div style=\"background: #f8f9fa; border-left: 4px solid #e67e22; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #2c3e50;\">📊 I Punti di Vista della Stampa Nazionale</h3>\n"
    "    <ul style=\"padding-left: 20px; margin-bottom: 0;\">\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Corriere della Sera e La Repubblica:</strong> [Sintesi delle prime pagine e differenze di racconto]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Libero, Il Giornale e La Verità:</strong> [Analisi della stampa conservatrice e difesa delle scelte di governo]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>La Stampa e Il Foglio:</strong> [Retroscena istituzionali, dibattito politico ed economia]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Il Sole 24 Ore:</strong> [Mercati, dati di bilancio, crescita e imprese]</li>\n"
    "    </ul>\n"
    "  </div>\n\n"
    "  <div style=\"background: #f0f4f8; border-left: 4px solid #2980b9; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #2980b9;\">🌍 Lo Sguardo della Stampa Internazionale</h3>\n"
    "    <p>[Sintesi su come Financial Times, WSJ, Le Figaro o El País raccontano l'Italia, il ruolo dell'Italia in Europa e la figura di Giorgia Meloni sullo scenario globale]</p>\n"
    "  </div>\n\n"
    "  <div style=\"background: #fff8e1; border: 1px solid #ffe082; border-left: 4px solid #f39c12; padding: 18px 20px; font-style: italic; margin-bottom: 25px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; font-style: normal; color: #d35400;\">💡 Il Commento della Redazione</h3>\n"
    "    <p>\"[Riflessione politica chiara e incisiva a sostegno del percorso di stabilità e crescita dell'Italia]\"</p>\n"
    "    <div style=\"text-align: right; font-weight: bold; font-style: normal; color: #7f8c8d; margin-top: 10px;\">— Bruno Rachiele</div>\n"
    "  </div>\n\n"
    "  <div style=\"background: #eef9f5; border: 1px solid #c8e6c9; padding: 20px; border-radius: 8px;\">\n"
    "    <h4 style=\"margin-top:0; color: #2e7d32; font-size: 18px;\">✉️ Spunti per la Newsletter</h4>\n"
    "    <ol style=\"padding-left: 20px; margin-bottom: 0;\">\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Economia e Fisco:</strong> [Sintesi punto 1]</li>\n"
    "      <li style="margin-bottom: 8px;\"><strong>Politica Estera e UE:</strong> [Sintesi punto 2]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Riforme Strutturali:</strong> [Sintesi punto 3]</li>\n"
    "    </ol>\n"
    "  </div>\n"
    "</div>\n"
)

# 6. Generazione Testo
print("🧠 Rilevamento modelli disponibili...")

modelli_da_provare = ['gemma-4-26b-a4b-it', 'gemini-3.8-flash', 'gemini-1.5-flash']
response = None

for m in modelli_da_provare:
    try:
        print(f"🔄 Prova generazione con modello: {m}...")
        response = client.models.generate_content(
            model=m,
            contents=prompt,
        )
        if response and response.text:
            print(f"✅ Generazione completata con: {m}")
            break
    except Exception as err:
        print(f"❌ Errore con {m}: {err}")

if not response or not response.text:
    raise RuntimeError("❌ Impossibile generare il contenuto.")

html_content = response.text
contenuto_completo = schema_html + header_html + html_content + foto_html

# 7. Invio Email via SMTP
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi_str}"
msg.attach(MIMEText(contenuto_completo, 'html'))

try:
    print("📧 Connessione al server SMTP di Gmail...")
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SENDER_EMAIL.strip(), SENDER_PASSWORD.strip().replace(" ", ""))
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, msg.as_string())
    server.quit()
    print("✅ RASSEGNA STAMPA PUBBLICATA CON SUCCESSO SU BLOGGER!")
except Exception as e:
    print(f"❌ Errore durante l'invio SMTP: {e}")
    raise e
