import os
import datetime
from duckduckgo_search import DDGS
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HEADER_IMAGE_URL = "https://static.brunorachiele.it/rassegnastampa.png"

def fetch_live_news():
    """Recupera notizie reali di OGGI divise per le macro-aree tematiche richieste."""
    print("Ricerca notizie live per temi (Politica, Esteri, Economia, Elezioni, Giornali)...")
    ddgs = DDGS()
    
    today = datetime.date.today()
    mesi = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    date_query = f"{today.day} {mesi[today.month]}"
    
    queries = {
        "POLITICA ED ELEZIONI": f"politica italia elezioni sondaggi parlamento {date_query}",
        "ESTERI ED ATTUALITA": f"esteri geopolitica mondo notizie attualita {date_query}",
        "ECONOMIA E GIORNALI": f"economia fisco mercati lavoro prime pagine giornali {date_query}"
    }
    
    news_text = ""
    for category, q in queries.items():
        news_text += f"\n--- {category} DI OGGI ---\n"
        try:
            results = ddgs.news(keywords=q, region="it-it", safesearch="off", max_results=5)
            for idx, r in enumerate(results, 1):
                source = r.get("source", "Testata Giornalistica")
                title = r.get("title", "")
                body = r.get("body", "")
                news_text += f"{idx}. [{source}] {title}: {body}\n"
        except Exception as e:
            print(f"[-] Errore durante la ricerca per {category}: {e}")
            
    return news_text

def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i secret devono essere configurati su GitHub.")

    # 1. Recupera le notizie tematiche di oggi
    live_news_context = fetch_live_news()
    print("[+] Notizie tematiche estratte con successo.")

    # 2. Inizializza Gemini Client
    gemini_client = genai.Client(api_key=gemini_api_key)
    
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
        "Basandoti sui dati ricevuti, scrivi una rassegna stampa quotidiana chiara, approfondita e formattata in HTML visivamente impeccabile. "
        "Analizza i fatti con taglio analitico, mantenendo una prospettiva favorevole alla stabilita e alle riforme liberal-conservatrici. "
        "Per ogni sezione indica espressamente le fonti o testate citate nei dati."
    )

    prompt = f"""
    Ecco i fatti e le notizie REALI estratte per la giornata di OGGI ({today_formatted}):
    {live_news_context}

    Componi la rassegna organizzando il contenuto RIGOROSAMENTE in queste 6 macro-aree tematiche:

    STRUTTURA OBBLIGATORIA DELLE SEZIONI:
    - La primissima riga in assoluto deve essere solo il titolo principale racchiuso in <h1>TITOLO</h1> (es. <h1>Rassegna Stampa del {today_formatted}: Titolo del fatto principale</h1>).
    
    Per ogni sezione successiva, racchiudi il contenuto all'interno di un box card HTML stilizzato. 
    OGNI BOX DEVE INCLUDERE IN FONDO IL TAG <div class="card-source">📰 Fonte: Nome Testata / Quotidiano</div>.

    Crea esattamente questi 6 box card:
    1. <h2>Primo Piano & Attualità</h2> (Icona: 📌) - Il fatto principale e gli avvenimenti di cronaca/attualità più caldi della giornata.
    2. <h2>Politica & Istituzioni</h2> (Icona: 🏛️) - Riforme, dibattito parlamentare, interventi istituzionali e dinamiche di governo.
    3. <h2>Esteri & Geopolitica</h2> (Icona: 🌐) - Notizie internazionali, scenari geopolitici e il ruolo dell'Italia nel mondo.
    4. <h2>Dalle Prime Pagine</h2> (Icona: 📰) - Come i principali quotidiani hanno aperto e raccontato le notizie di oggi.
    5. <h2>Elezioni & Sondaggi</h2> (Icona: 🗳️) - Tendenze elettorali, sondaggi politici, vita interna dei partiti e prossime scadenze alle urne.
    6. <h2>Economia & Mercati</h2> (Icona: 📈) - Dati economici, fisco, lavoro, imprese e andamento dei mercati finanziari.
    """

    print("Elaborazione rassegna tematica con Gemini 3.8...")
    response = gemini_client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            temperature=0.3
        )
    )
    raw_html = response.text

    lines = raw_html.strip().split("\n")
    post_title = f"Rassegna Stampa del {today_formatted}"
    body_content = raw_html

    for line in lines:
        if "<h1>" in line and "</h1>" in line:
            post_title = line.replace("<h1>", "").replace("</h1>", "").strip()
            body_content = raw_html.replace(line, "").strip()
            break

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
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )

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
    "name": "brunorachiele.it",
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

    print(f"[SUCCESS] Rassegna tematica pubblicata con successo! URL: {post_url}")

if __name__ == "__main__":
    main()
