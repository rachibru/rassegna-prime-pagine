import os
import json
import datetime
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    # 1. Recupera le credenziali dall'ambiente (GitHub Secrets)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([gemini_api_key, blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i secret devono essere configurati.")

    # 2. Inizializza il client Gemini per la generazione dell'articolo
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    
    prompt = f"""
    Sei un giornalista politico e analista senior. Genera una rassegna stampa politica italiana per la giornata di oggi ({today_str}).
    
    L'articolo deve essere strutturato in HTML pulito e contenere le seguenti sezioni precise:
    1. **Immagine di copertina**: Usa un tag <img> in testa al contenuto con un'immagine royalty-free da Unsplash (es. https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80 o un'immagine a tema politica/giornali).
    2. **Introduzione**: Breve panoramica della giornata politica.
    3. **Divisione per Temi**:
       - <h2>Governo e Maggioranza</h2> (con analisi e punti chiave)
       - <h2>Opposizioni e Dibattito Parlamentare</h2> (con analisi e punti chiave)
       - <h2>Economia e Politiche Sociali</h2> (con analisi e punti chiave)
    4. **La Riflessione di Bruno Rachiele**: Un paragrafo dedicato con <h2>La Riflessione di Bruno Rachiele</h2> contenente una spiccata analisi critica e personale sui fatti del giorno.
    5. **Conclusione**: Breve sintesi finale.

    Restituisci esclusivamente un JSON valido con questa struttura:
    {{
      "title": "Titolo SEO accattivante con la data di oggi",
      "featured_image": "URL_DELL_IMMAGINE_PRINCIPALE",
      "content": "CORPO_DELL_ARTICOLO_IN_HTML_CON_TAG_IMG_IMMAGINE_E_SEZIONI"
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
    featured_image = data.get("featured_image", "https://images.unsplash.com/photo-1541872703-74c5e44368f9")
    post_content_html = data.get("content")

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

    # 4. Step 1: Pubblicazione iniziale su Blogger
    body_initial = {
        "title": post_title,
        "content": post_content_html,
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

    # 5. Step 2: Iniezione Schema.org completo (con immagine e autore)
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
  "image": ["{featured_image}"],
  "datePublished": "{datetime.datetime.now().isoformat()}",
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

    updated_content = post_content_html + "\n" + schema_org_script

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

    print("Post aggiornato con sezioni tematiche, riflessione e Schema.org avanzato!")

if __name__ == "__main__":
    main()
