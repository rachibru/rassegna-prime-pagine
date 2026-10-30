import os
import re
import time
import datetime
import urllib.parse
import feedparser
import requests
from google import genai
from google.genai import types

HEADER_IMAGE_URL = "https://static.brunorachiele.it/rassegnastampa.png"

def get_blogger_access_token(client_id, client_secret, refresh_token):
    """Ottiene un nuovo Access Token per Blogger via OAuth 2.0."""
    print("Richiesta token di accesso a Google OAuth 2.0...")
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Errore OAuth Google: {response.status_code} - {response.text}")
    
    token_data = response.json()
    return token_data.get("access_token")

def fetch_weekly_news_rss():
    """Recupera le principali notizie della SETTIMANA tramite Google News RSS."""
    print("Estrazione notizie della settimana tramite Google News RSS...")
    
    # query con 'when:7d' per filtrare gli avvenimenti degli ultimi 7 giorni
    topics = {
        "POLITICA ED ELEZIONI": "politica+italia+governo+parlamento+sondaggi+when:7d",
        "ESTERI ED ATTUALITA": "esteri+geopolitica+mondo+attualita+when:7d",
        "ECONOMIA E GIORNALI": "economia+fisco+mercati+lavoro+when:7d"
    }
    
    news_text = ""
    total_found = 0
    
    for category, query in topics.items():
        news_text += f"\n--- {category} DELLA SETTIMANA ---\n"
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=it&gl=IT&ceid=IT:it"
        
        try:
            feed = feedparser.parse(rss_url)
            entries = feed.entries[:8]  # Prende i primi 8 fatti rilevanti
            for idx, entry in enumerate(entries, 1):
                title = entry.get("title", "")
                source = entry.get("source", {}).get("title", "Testata Giornalistica")
                published = entry.get("published", "")
                
                if title:
                    news_text += f"{idx}. [{source}] {title} (Pubblicato: {published})\n"
                    total_found += 1
        except Exception as e:
            print(f"[-] Errore nel recupero RSS per {category}: {e}")

    print(f"[+] Totale notizie estratte per la rassegna: {total_found}")
    return news_text

def generate_with_retry(gemini_client, prompt, sys_instruction, max_retries=3):
    """Chiamata con retry per la generazione con Gemini API."""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tentativo {attempt}/{max_retries}: Generazione rassegna con Gemini...")
            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            print(f"[-] Errore al tentativo {attempt}: {e}")
            if attempt < max_retries:
                time.sleep(attempt * 5)
            else:
                raise e

def publish_to_blogger(blog_id, access_token, title, html_content):
    """Pubblica il post direttamente con HTML e Schema.org in una sola operazione."""
    print("Pubblicazione post su Blogger...")
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title,
        "content": html_content,
        "labels": ["Rassegna Stampa", "Settimana"]
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        raise RuntimeError(f"Errore pubblicazione Blogger: {res.status_code} - {res.text}")
    
    post_data = res.json()
    post_id = post_data.get("id")
    post_url = post_data.get("url")
    print(f"[SUCCESS] Post pubblicato correttamente! ID: {post_id} - URL Canonico: {post_url}")
    return post_id, post_url

def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip("[] ")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "").strip("[] ")
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "").strip("[] ")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "").strip("[] ")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "").strip("[] ")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Verifica che tutte le variabili d'ambiente/secrets siano configurate.")

    # 1. Autenticazione
    access_token = get_blogger_access_token(client_id, client_secret, refresh_token)

    # 2. Estrazione dati settimanali
    live_news_context = fetch_weekly_news_rss()
    
    now = datetime.datetime.now(datetime.timezone.utc)
    today_formatted = now.strftime("%d/%m/%Y")

    # 3. Inizializzazione Gemini Client
    gemini_client = genai.Client(api_key=gemini_api_key)

    sys_instruction = (
        "Sei uno studente di giurisprudenza di 23 anni, attivista politico e giornalista di orientamento liberal-conservatore. "
        "Scrivi la rassegna stampa domenicale basandoti TASSATIVAMENTE sulle notizie REALI della settimana fornite. "
        "Sii analitico, incisivo e orientato alle riforme, alla stabilità e allo sviluppo economico."
    )

    prompt = f"""
    OGGI È LA RASSEGNA STAMPA DOMENICALE DEL {today_formatted}.
    Ecco le NOTIZIE REALI estratte dagli ultimi 7 giorni:
    {live_news_context}

    REGOLE PER IL TITOLO:
    - La prima riga DEVE essere il titolo della rassegna dentro <h1>...</h1>.
    - Deve evidenziare i 2 o 3 fatti politici/economici chiave della settimana.

    STRUTTURA IN 6 CARD TEMATICHE (Solo tag HTML, no Markdown):
    1. <div class="news-card"><div class="card-header"><h2>📌 Primo Piano & Attualità Settimanale</h2></div>...</div>
    2. <div class="news-card"><div class="card-header"><h2>🏛️ Politica & Istituzioni</h2></div>...</div>
    3. <div class="news-card"><div class="card-header"><h2>🌐 Esteri & Geopolitica</h2></div>...</div>
    4. <div class="news-card"><div class="card-header"><h2>📰 Dalle Prime Pagine del Weekend</h2></div>...</div>
    5. <div class="news-card"><div class="card-header"><h2>🗳️ Elezioni & Sondaggi</h2></div>...</div>
    6. <div class="news-card"><div class="card-header"><h2>📈 Economia & Mercati</h2></div>...</div>

    Ogni card deve contenere una sintesi e terminare con la fonte:
    <div class="card-source">📰 Fonti della settimana: Nome Testata</div>
    """

    raw_html = generate_with_retry(gemini_client, prompt, sys_instruction)

    # Pulizia Output dell'AI
    cleaned_html = re.sub(r"^```html\s*", "", raw_html, flags=re.IGNORECASE)
    cleaned_html = re.sub(r"\s*```$", "", cleaned_html).strip()

    h1_match = re.search(r"<h1>(.*?)</h1>", cleaned_html, re.IGNORECASE | re.DOTALL)

    if h1_match:
        post_title = h1_match.group(1).strip()
        body_content = re.sub(r"<h1>.*?</h1>", "", cleaned_html, count=1, flags=re.IGNORECASE | re.DOTALL).strip()
    else:
        post_title = f"Rassegna Stampa Domenicale ({today_formatted}) – I fatti della settimana"
        body_content = cleaned_html

    custom_css = """
<style>
  .rassegna-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #2c3e50;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 10px;
  }
  .rassegna-header-img {
    width: 100%;
    height: auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 25px;
    display: block;
  }
  .news-card {
    background: #ffffff;
    border: 1px solid #eef2f5;
    border-left: 5px solid #1a365d;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    margin-bottom: 24px;
    padding: 20px 24px;
  }
  .card-header h2 {
    font-size: 1.25rem !important;
    color: #1a365d !important;
    margin: 0 !important;
    font-weight: 700 !important;
  }
  .card-body p {
    font-size: 1.02rem;
    color: #4a5568;
    margin-bottom: 12px;
  }
  .card-source {
    margin-top: 15px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #2b6cb0;
    background: #ebf8ff;
    display: inline-block;
  }
</style>
"""

    iso_date = now.isoformat()

    # Schema.org dinamico inserito DIRETTAMENTE nel codice finale
    schema_org_script = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{post_title}",
  "image": ["{HEADER_IMAGE_URL}"],
  "datePublished": "{iso_date}",
  "dateModified": "{iso_date}",
  "author": {{
    "@type": "Person",
    "name": "Bruno Rachiele",
    "url": "https://www.brunorachiele.it/"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "Bruno Rachiele",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiOeKLAFzNySkI5ahC_uZiv0Asne6shnjr1QndoMNmRBtkNdQfe59GGO3nY5nc5C4OCXNMXGXu1XtHm0X7gPqbvTgFjqszFGQrPD3G5R4c2MIJPiZCk5OX6dLbnYKeU1itEVo7OcJB9I0N-Wi9z9WP64l5_btoNMrZ111Ex8i-W9UcKwOJPv5uDnl6LwhA/s1600/2ed26cc2-38e4-4d67-a1c5-5e522b654c90%20%281%29.png"
    }}
  }}
}}
</script>
"""

    final_article_html = f"""
{custom_css}
<div class="rassegna-container">
  <img src="{HEADER_IMAGE_URL}" alt="{post_title}" class="rassegna-header-img" />
  {body_content}
</div>
{schema_org_script}
"""

    # Pubblica su Blogger in una sola chiamata
    publish_to_blogger(blog_id, access_token, post_title, final_article_html)

if __name__ == "__main__":
    main()
