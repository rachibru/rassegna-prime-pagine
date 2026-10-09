import os
import json
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
        raise ValueError("Tutti i secret (GEMINI_API_KEY, BLOGGER_BLOG_ID, BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN) devono essere configurati.")

    # 2. Inizializza il client Gemini per generare il contenuto HTML
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    prompt = """
    Genera un articolo quotidiano di rassegna stampa politica italiana SEO-ottimizzato.
    Restituisci un JSON valido con due chiavi:
    1. "title": Il titolo accattivante ed SEO-friendly dell'articolo.
    2. "content": Il corpo dell'articolo in formato HTML pulito, formattato con headings (<h2>, <h3>), paragrafi e elenchi puntati. Non includere lo script Schema.org all'interno dell'HTML.
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
    post_content_html = data.get("content")

    # 3. Autenticazione OAuth 2.0 per Blogger API v3
    creds = Credentials(
        token=None,  # Il token d'accesso verrà automaticamente rigenerato usando il refresh_token
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )

    blogger_service = build("blogger", "v3", credentials=creds)

    # 4. Step 1: Pubblicazione iniziale del Post su Blogger
    body_initial = {
        "title": post_title,
        "content": post_content_html,
        "labels": ["Rassegna Stampa"]
    }

    published_post = blogger_service.posts().insert(
        blogId=blog_id,
        body=body_initial,
        isDraft=False
    ).execute()

    post_id = published_post.get("id")
    post_url = published_post.get("url")

    print(f"Post pubblicato con successo! ID: {post_id}")
    print(f"URL generato: {post_url}")

    # 5. Step 2: Iniezione dello Schema.org allineato con l'URL effettivo
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
  "description": "Rassegna stampa politica quotidiana.",
  "url": "{post_url}",
  "publisher": {{
    "@type": "Organization",
    "name": "Bruno Rachiele",
    "url": "https://brunorachiele.it"
  }}
}}
</script>
"""

    # Unisce l'HTML dell'articolo con lo script Schema.org
    updated_content = post_content_html + "\n" + schema_org_script

    body_update = {
        "title": post_title,
        "content": updated_content,
        "labels": ["Rassegna Stampa"]
    }

    blogger_service.posts().patch(
        blogId=blog_id,
        postId=post_id,
        body=body_update
    ).execute()

    print("Schema.org iniettato e URL sincronizzati con successo!")

if __name__ == "__main__":
    main()
