import os
import re
import time
import datetime
import urllib.parse
import feedparser
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

HEADER_IMAGE_URL = "https://static.brunorachiele.it/rassegnastampa.png"

def fetch_live_news_rss():
    """Recupera notizie reali e freschissime tramite i Feed RSS di Google News Italia."""
    print("Estrazione notizie in tempo reale tramite Google News RSS...")
    
    topics = {
        "POLITICA ED ELEZIONI": "politica+italia+governo+parlamento+sondaggi",
        "ESTERI ED ATTUALITA": "esteri+geopolitica+mondo+attualita",
        "ECONOMIA E GIORNALI": "economia+fisco+mercati+lavoro+giornali"
    }
    
    news_text = ""
    total_found = 0
    
    for category, query in topics.items():
        news_text += f"\n--- {category} DI OGGI ---\n"
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=it&gl=IT&ceid=IT:it"
        
        try:
            feed = feedparser.parse(rss_url)
            entries = feed.entries[:6]
            for idx, entry in enumerate(entries, 1):
                title = entry.get("title", "")
                source = entry.get("source", {}).get("title", "Testata Giornalistica")
                published = entry.get("published", "")
                
                if title:
                    news_text += f"{idx}. [{source}] {title} (Pubblicato: {published})\n"
                    total_found += 1
        except Exception as e:
            print(f"[-] Errore nel recupero RSS per {category}: {e}")

    print(f"[+] Totale notizie reali e fresche estratte oggi: {total_found}")
    return news_text

def generate_with_retry(gemini_client, prompt, sys_instruction, max_retries=5):
    """Chiamata robusta con retry automatico per gestire eventuali 503/429 di Gemini."""
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
                wait_time = attempt * 15
                print(f"[!] Attesa di {wait_time} secondi prima del prossimo tentativo...")
                time.sleep(wait_time)
            else:
                raise e

def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i secret devono essere configurati su GitHub.")

    # Sanificazione automatica di sicurezza
    client_id = client_id.strip().strip("[").strip("]")
    client_secret = client_secret.strip().strip("[").strip("]")
    refresh_token = refresh_token.strip().strip("[").strip("]")

    live_news_context = fetch_live_news_rss()
    
    today = datetime.date.today()
    mesi = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    today_formatted = f"{today.day} {mesi[today.month]} {today.year}"

    gemini_client = genai.Client(api_key=gemini_api_key)

    sys_instruction = (
        "Sei uno studente di giurisprudenza di 23 anni, attivista politico e giornalista di orientamento liberal-conservatore. "
        "Scrivi una rassegna stampa basandoti TASSATIVAMENTE sui fatti e le notizie REALI forniti nel contesto. "
        "Sii analitico, incisivo e orientato alle riforme e alla stabilità politica."
    )

    prompt = f"""
    OGGI È IL {today_formatted}.
    Ecco l'elenco delle NOTIZIE REALI estratte dai giornali e dalle agenzie di stampa per oggi:
    {live_news_context}

    REGOLE TASSATIVE PER IL TITOLO:
    - La primissima riga dell'output DEVE essere il titolo racchiuso dentro <h1>...</h1>.
    - Il titolo DEVE essere unico, giornalistico e citare espressamente i 2 o 3 fatti principali di OGGI (es. i temi di politica o esteri emersi nelle notizie).
    - NON USARE MAI un titolo generico come solo "Rassegna Stampa del {today_formatted}".

    STRUTTURA OBBLIGATORIA DELLE SEZIONI (Formattazione HTML):
    Organizza la rassegna in 6 card HTML stilizzate per questi temi:
    1. <h2>Primo Piano & Attualità</h2> (Icona: 📌)
    2. <h2>Politica & Istituzioni</h2> (Icona: 🏛️)
    3. <h2>Esteri & Geopolitica</h2> (Icona: 🌐)
    4. <h2>Dalle Prime Pagine</h2> (Icona: 📰)
    5. <h2>Elezioni & Sondaggi</h2> (Icona: 🗳️)
    6. <h2>Economia & Mercati</h2> (Icona: 📈)

    In fondo ad ogni card inserisci il tag con la fonte reale citata nei dati:
    <div class="card-source">📰 Fonte: Nome Testata / Quotidiano</div>
    """

    raw_html = generate_with_retry(gemini_client, prompt, sys_instruction)

    # Pulizia blocchi markdown ```html
    cleaned_html = re.sub(r"^```html\s*", "", raw_html, flags=re.IGNORECASE)
    cleaned_html = re.sub(r"\s*```$", "", cleaned_html).strip()

    # Estrazione flessibile del titolo dall'<h1>
    h1_match = re.search(r"<h1>(.*?)</h1>", cleaned_html, re.IGNORECASE | re.DOTALL)

    if h1_match:
        post_title = h1_match.group(1).strip()
        body_content = re.sub(r"<h1>.*?</h1>", "", cleaned_html, count=1, flags=re.IGNORECASE | re.DOTALL).strip()
    else:
        post_title = f"Rassegna Stampa del {today_formatted}: Le Notizie di Oggi"
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

    final_article_html = f"""
{custom_css}
<div class="rassegna-container">
  <img src="{HEADER_IMAGE_URL}" alt="{post_title}" class="rassegna-header-img" />
  {body_content}
</div>
"""

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["[https://www.googleapis.com/auth/blogger](https://www.googleapis.com/auth/blogger)"]
    )

    if not creds.valid:
        creds.refresh(Request())

    blogger_service = build("blogger", "v3", credentials=creds)

    body_initial = {
        "title": post_title,
        "content": final_article_html,
        "labels": ["Rassegna Stampa"]
    }

    published_post = blogger_service.posts().insert(
        blogId=blog_id,
        body=body_initial,
        isDraft=False
    ).execute()

    post_id = published_post.get("id")
    post_url = published_post.get("url")

    iso_date = datetime.datetime.now().isoformat()
    schema_org_script = f"""
<script type="application/ld+json">
{{
  "@context": "[https://schema.org](https://schema.org)",
  "@type": "NewsArticle",
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "{post_url}"
  }},
  "headline": "{post_title}",
  "image": ["{HEADER_IMAGE_URL}"],
  "datePublished": "{iso_date}",
  "author": {{
    "@type": "Person",
    "name": "Bruno Rachiele",
    "url": "[https://bio.brunorachiele.it](https://bio.brunorachiele.it)"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "brunorachiele.it",
    "url": "[https://www.brunorachiele.it](https://www.brunorachiele.it)"
  }}
}}
</script>
"""

    updated_html = final_article_html + "\n" + schema_org_script

    body_update = {
        "title": post_title,
        "content": updated_html,
        "labels": ["Rassegna Stampa"]
    }

    blogger_service.posts().patch(
        blogId=blog_id,
        postId=post_id,
        body=body_update
    ).execute()

    print(f"[SUCCESS] Pubblicato con successo! Titolo: '{post_title}' - URL: {post_url}")

if __name__ == "__main__":
    main()
