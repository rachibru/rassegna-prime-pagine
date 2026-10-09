import os
import time
import datetime
import json
import smtplib
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

client = genai.Client(api_key=GEMINI_API_KEY)

IMMAGINE_PRINCIPALE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

# 3. Schema.org JSON-LD per Indicizzazione SEO Avanzata
schema_json = {
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": f"https://www.brunorachiele.it/{datetime.datetime.now().strftime('%Y/%m')}/rassegna-stampa-{data_iso}.html"
  },
  "headline": f"Rassegna Stampa & Analisi Politica - {data_oggi_str}",
  "image": [IMMAGINE_PRINCIPALE],
  "datePublished": f"{data_iso}T06:00:00+02:00",
  "dateModified": f"{data_iso}T06:00:00+02:00",
  "author": {
    "@type": "Person",
    "name": "Bruno Rachiele",
    "jobTitle": "Editor politico",
    "url": "https://www.brunorachiele.it"
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

# 4. Prompt per la generazione del testo
prompt = (
    "Sei un autorevole giornalista ed editor politico d'area conservatrice e di centrodestra (vicino alla linea del Governo Meloni).\n"
    f"Elabora un commento analitico e una rassegna sintetica dei titoli e temi effettivamente presenti sulle prime pagine dei quotidiani di oggi ({data_oggi_str}).\n\n"
    "Assicurati che la discesa dei temi certifichi in modo accurato quanto riportato in edicola dalle testate nazionali ed estere.\n"
    "Mantieni uno stile autorevole, lucido e professionale, valorizzando la stabilità dell'esecutivo, il pragmatismo delle riforme economiche e la difesa dell'interesse nazionale.\n\n"
    "Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza tag <html> o <body>) rispettando esattamente questa struttura e stili inline:\n\n"
    "<div style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #2c3e50; max-width: 800px; margin: 0 auto; padding: 10px; line-height: 1.6;\">\n"
    f"  <h2 style=\"color: #1a252f; border-bottom: 2px solid #003366; padding-bottom: 8px; margin-bottom: 20px;\">🗞️ Rassegna Stampa & Analisi Politica - {data_oggi_str}</h2>\n\n"
    "  <div style=\"background: #f8f9fa; border-left: 4px solid #003366; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #003366;\">📌 Il Tema Centrale del Giorno</h3>\n"
    "    <p>[Analisi certificata del fatto politico principale della giornata con focus sulle riforme, l'azione del Governo Meloni e la stabilità del Paese]</p>\n"
    "  </div>\n\n"
    "  <div style=\"background: #f8f9fa; border-left: 4px solid #e67e22; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #2c3e50;\">📊 I Titoli della Stampa Nazionale</h3>\n"
    "    <ul style=\"padding-left: 20px; margin-bottom: 0;\">\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Corriere della Sera e La Repubblica:</strong> [Verifica dei titoli d'apertura e differenze di racconto]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Libero, Il Giornale e La Verità:</strong> [Titoli di testa della stampa conservatrice e difesa delle scelte di governo]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>La Stampa e Il Foglio:</strong> [Retroscena istituzionali, dibattito politico ed economia]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Il Sole 24 Ore:</strong> [Mercati, dati di bilancio, crescita e imprese]</li>\n"
    "    </ul>\n"
    "  </div>\n\n"
    "  <div style=\"background: #f0f4f8; border-left: 4px solid #2980b9; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;\">\n"
    "    <h3 style=\"margin-top:0; color: #2980b9;\">🌍 Lo Sguardo della Stampa Internazionale</h3>\n"
    "    <p>[Sintesi di come Financial Times, WSJ, Le Figaro o El País raccontano l'Italia, il ruolo dell'Italia in Europa e la figura di Giorgia Meloni sullo scenario globale]</p>\n"
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
    "      <li style=\"margin-bottom: 8px;\"><strong>Politica Estera e UE:</strong> [Sintesi punto 2]</li>\n"
    "      <li style=\"margin-bottom: 8px;\"><strong>Riforme Strutturali:</strong> [Sintesi punto 3]</li>\n"
    "    </ol>\n"
    "  </div>\n"
    "</div>\n"
)

# 5. Generazione Testo
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
contenuto_completo = schema_html + header_html + html_content

# 6. Invio Email via SMTP con solo il Tag [Rassegna Stampa]
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL

# Solo il tag [Rassegna Stampa] per la categorizzazione automatica
msg['Subject'] = f"Prime Pagine e Commento del Giorno - {data_oggi_str} [Rassegna Stampa]"

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
    print("✅ RASSEGNA STAMPA PUBBLICATA CON SUCCESSO SU BLOGGER CON TAG RASSEGNA STAMPA!")
except Exception as e:
    print(f"❌ Errore durante l'invio SMTP: {e}")
    raise e
