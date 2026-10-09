import os
import json
import datetime
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ==============================================================================
# INSERISCI QUI IL LINK DELLA TUA IMMAGINE PREDEFINITA
# ==============================================================================
DEFAULT_IMAGE_URL = "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80"

def main():
    # 1. Recupera le credenziali dall'ambiente (GitHub Secrets)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i secret devono essere configurati su GitHub.")

    # 2. Inizializza il client Gemini per la generazione dell'articolo
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    
    prompt = f"""
    Sei un giornalista politico e analista senior. Genera un'approfondita rassegna stampa politica italiana per la giornata di oggi ({today_str}).
    
    L'articolo deve essere formattato in HTML pulito e contenere esattamente le seguenti sezioni:
    - <h2>Introduzione</h2>: Panoramica e sintesi dei fatti del giorno.
    - <h2>Governo e Maggioranza</h2>: Analisi dei principali provvedimenti, dichiarazioni e mosse del governo.
    - <h2>Opposizioni e Dibattito Parlamentare</h2>: Le posizioni e le contromosse dei partiti di opposizione.
    - <h2>Economia e Politiche Sociali</h2>: Aggiornamenti su temi economici, lavoro e manovre fiscali.
    - <h2>La Riflessione di Bruno Rachiele</h2>: Un'analisi critica, personale e approfondita sulle dinamiche politiche della giornata.
    - <h2>Conclusione</h2>: Sintesi e prospettive per i prossimi giorni.

    Restituisci esclusivamente un JSON valido con questa struttura esatta:
    {{
      "title": "Titolo SEO accattivante ed esplicativo con la data di oggi",
      "content": "CORPO_DELL_ARTICOLO_IN_HTML_CON_TUTTE_LE_SEZIONI"
    }}
    """

    response = gemini_client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    data = json.loads(response.text)
    post_title = data.get("title")
    article_html = data.get("content")

    # Inserimento dell'immagine scelta da te in cima all'articolo
    header_img_tag = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{DEFAULT_IMAGE_URL}" alt="{post_title}" style="max-width: 100%; height: auto; border-radius: 8px;" /></div>\n'
    full_content_html = header_img_tag + article_html

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

    # 4. Step 1: Pubblicazione iniziale del post
    body_initial = {
        "title": post_title,
        "content": full_content_html,
        "labels": ["Rassegna Stampa", "Politica Italiana"]
    }

    published_post = blogger_service.posts().insert(
        blogId=blog_id,
        body=body_initial,
        isDraft=False
    ).execute()

    post_id = published_post.get("id")
    post_url = published_post.get("url")

    print(f"Post pubblicato! ID: {post_id} - URL: {post_url}")

    # 5. Step 2: Iniezione dello Schema.org NewsArticle (con il tuo link immagine)
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
  "image": ["{DEFAULT_IMAGE_URL}"],
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

    updated_content = full_content_html + "\n" + schema_org_script

    body_update = {
        "title": post_title,
        "content": updated_content,
        "labels": ["Rassegna Stampa", "Politica Italiana"]
    }

    blogger_service.posts().patch(
        blogId=blog_id,
        postId=post_id,
        body=body_update
    ).execute()

    print("Post aggiornato con successo! Immagine personalizzata, sezioni tematiche e Schema.org pronti.")

if __name__ == "__main__":
    main()
