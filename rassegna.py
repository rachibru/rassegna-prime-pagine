import os
import time
import datetime
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Immagine di copertina personalizzata
HEADER_IMAGE_URL = "https://static.brunorachiele.it/rassegnastampa.png"

def get_gemini_content(client, prompt, sys_instruction):
    """Richiesta a Gemini con Google Search Grounding attivo e retry."""
    for attempt in range(1, 5):
        try:
            print(f"Ricerca notizie live e generazione articolo in corso (tentativo {attempt})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Modello consigliato e nativo con Google Search Grounding
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.3,
                    tools=[{"google_search": {}}]  # <-- ABILITA LA RICERCA GOOGLE IN TEMPO REALE
                )
            )
            return response.text
        except Exception as e:
            print(f"Server temporaneamente occupato: {e}")
            if attempt < 4:
                time.sleep(attempt * 5)
            else:
                raise e

def main():
    # 1. Recupera i Secret
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i secret devono essere configurati su GitHub.")

    # 2. Inizializza Gemini Client
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    # Formattazione data italiana
    today = datetime.date.today()
    mesi = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    today_formatted = f"{today.day} {mesi[today.month]} {today.year}"
    today_str = today.strftime("%d/%m/%Y")

    sys_instruction = (
        "Sei un autorevole analista politico e giornalista di orientamento liberal-conservatore e di centro-destra. "
        "Usa la ricerca Google per estrarre le notizie POLITICHE ed ECONOMICHE ITALIANE REALI pubblicate OGGI. "
        "Scrivi rassegne stampa quotidiane chiare, ben strutturate e formattate in HTML visivamente impeccabile, "
        "trasmettendo una visione favorevole all'operato del Governo, evidenziando i risultati della maggioranza e "
        "analizzando in modo critico ma elegante le posizioni dell'opposizione. "
        "Per ogni notizia riportata indica espressamente la testata o la fonte giornalistica di riferimento reali (es. Il Giornale, Il Messaggero, Libero, Corriere della Sera, ANSA)."
    )

    prompt = f"""
    Cerca le notizie politiche ed economiche italiane di OGGI ({today_formatted}) e scrivi la rassegna stampa quotidiana.

    STRUTTURA OBBLIGATORIA DELLE SEZIONI:
    - La primissima riga in assoluto deve essere solo il titolo principale racchiuso in <h1>TITOLO</h1> (es. <h1>Rassegna Stampa del {today_formatted}: Titolo della Notizia Principale</h1>).
    
    Per ogni sezione successiva, racchiudi il contenuto all'interno di un box card HTML stilizzato. 
    OGNI BOX DEVE INCLUDERE IN FONDO IL TAG <div class="card-source">📰 Fonte: Nome Testata / Quotidiano</div>.

    Esempio di struttura della card:
    <div class="news-card">
      <div class="card-header">
        <span class="card-icon">📌</span>
        <h2>In Primo Piano</h2>
      </div>
      <div class="card-body">
        <p>Sintesi dei fatti reali principali di oggi...</p>
      </div>
      <div class="card-source">📰 Fonte principale: Il Giornale / Il Messaggero</div>
    </div>

    Crea esattamente questi 6 box card basati sulle notizie di OGGI:
    1. <h2>In Primo Piano</h2> (Icona: 📌) - Il fatto principale della giornata di oggi. (Aggiungi <div class="card-source"> con le fonti reali)
    2. <h2>Governo e Maggioranza</h2> (Icona: 🏛️) - Provvedimenti, riforme e dichiarazioni della maggioranza di oggi. (Aggiungi <div class="card-source"> con le fonti)
    3. <h2>Le Opposizioni</h2> (Icona: 🗣️) - Le reazioni e le mosse dell'opposizione di oggi. (Aggiungi <div class="card-source"> con le fonti)
    4. <h2>Economia e Lavoro</h2> (Icona: 📈) - Dati economici, mercati o norme della giornata. (Aggiungi <div class="card-source"> con le fonti)
    5. <h2>La Riflessione di Bruno Rachiele</h2> (Icona: ✍️) - Un paragrafo incisivo d'autore sui fatti odierni a sostegno della stabilità politica. (Aggiungi <div class="card-source">📰 Commento di Bruno Rachiele</div>)
    6. <h2>In Sintesi</h2> (Icona: 🎯) - Breve commento finale. (Aggiungi <div class="card-source">📰 Sintesi Rassegna Stampa del {today_str}</div>)
    """

    raw_html = get_gemini_content(gemini_client, prompt, sys_instruction)

    # Estrae il titolo <h1> e isola il contenuto
    lines = raw_html.strip().split("\n")
    post_title = f"Rassegna Stampa del {today_formatted}"
    body_content = raw_html

    for line in lines:
        if "<h1>" in line and "</h1>" in line:
            post_title = line.replace("<h1>", "").replace("</h1>", "").strip()
            body_content = raw_html.replace(line, "").strip()
            break

    # Stili CSS incorporati, Mobile-Friendly e Fonte Badge
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
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .news-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
  }
  .card-header {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #f0f4f8;
    padding-bottom: 10px;
    margin-bottom: 14px;
  }
  .card-icon {
    font-size: 1.4rem;
    margin-right: 10px;
  }
  .card-header h2 {
    font-size: 1.25rem !important;
    color: #1a365d !important;
    margin: 0 !important;
    padding: 0 !important;
    font-weight: 700 !important;
    border: none !important;
  }
  .card-body p {
    font-size: 1.02rem;
    color: #4a5568;
    margin-bottom: 12px;
  }
  .card-body p:last-child {
    margin-bottom: 0;
  }
  .card-body ul {
    padding-left: 20px;
    margin: 10px 0;
  }
  .card-body li {
    margin-bottom: 6px;
    color: #4a5568;
  }
  .card-source {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px dashed #e2e8f0;
    font-size: 0.88rem;
    font-weight: 600;
    color: #2b6cb0;
    display: inline-block;
    background: #ebf8ff;
    padding: 6px 12px;
    border-radius: 6px;
  }
  @media (max-width: 600px) {
    .rassegna-container {
      padding: 5px;
    }
    .news-card {
      padding: 16px 18px;
      margin-bottom: 18px;
    }
    .card-header h2 {
      font-size: 1.1rem !important;
    }
    .card-source {
      font-size: 0.82rem;
    }
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

    # 3. Autenticazione OAuth 2.0 per Blogger API v3
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )

    blogger_service = build("blogger", "v3", credentials=creds)

    # 4. Step 1: Pubblicazione del post su Blogger
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

    print(f"Post pubblicato con successo! URL: {post_url}")

    # 5. Step 2: Iniezione Schema.org NewsArticle
    iso_date = datetime.datetime.now().isoformat()
    schema_org_script = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
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
    "url": "https://www.bio.brunorachiele.it"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "Bruno Rachiele",
    "url": "https://brunorachiele.it"
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

    print("Rassegna live con notizie reali pubblicata con successo su Blogger!")

if __name__ == "__main__":
    main()
