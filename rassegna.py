import os
import time
import datetime
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Immagine di copertina personalizzata
HEADER_IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjq3FXgvCfB7U1IhNZqrVmya6z-SKVDZtDCTcAsGD_lnNK-cB9ULPamEQidtUtHkqFbPPQa0MeYZTRV8A7hf5ZQc3Ypx1bSBl730QKQgDvUOa1_m05p0DCa7OuHchRWleVms_oBzSOUPX2jTSQ9u-dsWdXuwUalpoE_7Ae5KmzDvVjbnkLFv8QaF8YvYyk/s1600/NUOVE%20GRAFICHE%20SITO%20%281%29.png"

def get_gemini_content(client, prompt, sys_instruction):
    """Richiesta leggera a Gemini con meccanismo di retry."""
    for attempt in range(1, 5):
        try:
            print(f"Generazione articolo in corso (tentativo {attempt})...")
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.4
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
    today_str = datetime.date.today().strftime("%d/%m/%Y")

    sys_instruction = (
        "Sei un autorevole analista politico e giornalista di orientamento liberal-conservatore e di centro-destra. "
        "Scrivi rassegne stampa politiche quotidiane chiare, ben strutturate, trasmettendo una visione favorevole all'operato del Governo, "
        "evidenziando i risultati della maggioranza e analizzando in modo critico le posizioni dell'opposizione."
    )

    prompt = f"""
    Scrivi una rassegna stampa politica per la giornata di oggi ({today_str}).

    STRUTTURA OBBLIGATORIA (usa solo tag HTML come <h2>, <p>, <ul>, <li>, <strong>):
    - La prima riga in assoluto deve essere il titolo dell'articolo formattato come <h1>TITOLO DELL'ARTICOLO</h1> (fai un titolo SEO accattivante con la data di oggi).
    - <h2>In Primo Piano</h2>: Sintesi e fatti principali dei giornali di oggi.
    - <h2>Governo e Maggioranza</h2>: I provvedimenti, le riforme e i successi del Governo.
    - <h2>Le Opposizioni</h2>: Analisi critica del dibattito e delle contromosse dell'opposizione.
    - <h2>Economia e Lavoro</h2>: Focus sui dati economici e le politiche di crescita.
    - <h2>La Riflessione di Bruno Rachiele</h2>: Un paragrafo incisivo con una tua riflessione personale d'autore a sostegno della stabilita politica e dello sviluppo del Paese.
    - <h2>Conclusione</h2>: Un breve commento di chiusura.
    """

    raw_html = get_gemini_content(gemini_client, prompt, sys_instruction)

    # Estrae il titolo <h1> e il resto del corpo
    lines = raw_html.strip().split("\n")
    post_title = f"Rassegna Stampa Politica del {today_str}"
    body_content = raw_html

    for line in lines:
        if "<h1>" in line and "</h1>" in line:
            post_title = line.replace("<h1>", "").replace("</h1>", "").strip()
            body_content = raw_html.replace(line, "").strip()
            break

    # Costruzione HTML con l'immagine in evidenza in cima
    header_html = (
        f'<div style="text-align: center; margin-bottom: 25px;">'
        f'<img src="{HEADER_IMAGE_URL}" alt="{post_title}" style="max-width: 100%; height: auto; border-radius: 8px;" />'
        f'</div>\n'
    )
    final_article_html = header_html + body_content

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
        "labels": ["Rassegna Stampa", "Politica Italiana"]
    }

    published_post = blogger_service.posts().insert(
        blogId=blog_id,
        body=body_initial,
        isDraft=False
    ).execute()

    post_id = published_post.get("id")
    post_url = published_post.get("url")

    print(f"Post pubblicato con successo! URL: {post_url}")

    # 5. Step 2: Iniezione Schema.org NewsArticle sincronizzato
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
    "url": "https://brunorachiele.it"
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
        "labels": ["Rassegna Stampa", "Politica Italiana"]
    }

    blogger_service.posts().patch(
        blogId=blog_id,
        postId=post_id,
        body=body_update
    ).execute()

    print("Schema.org iniettato correttamente!")

if __name__ == "__main__":
    main()
