import os
import datetime
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PAGE_TITLE = "Prime Pagine dei Giornali"

# Mappa dei quotidiani con la relativa pagina di riferimento
QUOTIDIANI_MAP = [
    {"name": "Corriere della Sera", "url": "https://www.giornalone.it/prima-pagina-corriere-della-sera/"},
    {"name": "La Repubblica", "url": "https://www.giornalone.it/prima-pagina-la-repubblica/"},
    {"name": "La Stampa", "url": "https://www.giornalone.it/prima-pagina-la-stampa/"},
    {"name": "Il Giornale", "url": "https://www.giornalone.it/prima-pagina-il-giornale/"},
    {"name": "Il Tempo", "url": "https://www.giornalone.it/prima-pagina-il-tempo/"},
    {"name": "Libero", "url": "https://www.giornalone.it/prima-pagina-libero/"},
    {"name": "Avvenire", "url": "https://www.giornalone.it/prima-pagina-avvenire/"},
    {"name": "Secolo d'Italia", "url": "https://www.giornalone.it/prima-pagina-secolo-d-italia/"},
    {"name": "Metro", "url": "https://www.giornalone.it/prima-pagina-metro-today/"},
    {"name": "Il Sole 24 Ore", "url": "https://www.giornalone.it/prima-pagina-il-sole-24-ore/"},
    {"name": "L'Osservatore Romano", "url": "https://www.giornalone.it/prima-pagina-l-osservatore-romano/"},
    {"name": "Corriere del Ticino", "url": "https://www.giornalone.it/prima-pagina-corriere-del-ticino/"},
    {"name": "The New York Times", "url": "https://www.giornalone.it/prima-pagina-the-new-york-times/"},
    {"name": "Le Figaro", "url": "https://www.giornalone.it/prima-pagina-le-figaro/"}
]

def fetch_prime_pagine():
    """Estrae l'immagine della prima pagina per ogni quotidiano configurato."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    papers = []

    for item in QUOTIDIANI_MAP:
        name = item["name"]
        page_url = item["url"]
        
        try:
            print(f"Estrazione prima pagina per: {name}...")
            response = requests.get(page_url, headers=headers, timeout=12)
            if response.status_code != 200:
                print(f"[-] Errore HTTP {response.status_code} su {name}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Cerca l'immagine principale della copertina nella pagina specifica
            img_tag = soup.find("img", id=lambda x: x and "copertina" in x.lower()) or \
                      soup.find("img", class_=lambda x: x and "copertina" in x.lower()) or \
                      soup.find("img", alt=lambda x: x and "prima pagina" in x.lower())

            # Se non la trova con id/class, prende la prima immagine dentro il contenuto principale
            if not img_tag:
                main_div = soup.find("div", class_="entry-content") or soup.find("article")
                if main_div:
                    img_tag = main_div.find("img")

            if img_tag:
                src = img_tag.get("src") or img_tag.get("data-src") or ""
                
                # Normalizza URL relativi
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://www.giornalone.it" + src

                if src and ("jpg" in src.lower() or "png" in src.lower() or "webp" in src.lower()):
                    papers.append({
                        "title": name,
                        "image_url": src
                    })
                    print(f"[+] Estratta copertina per {name}")
                else:
                    print(f"[-] URL immagine non valido per {name}")
            else:
                print(f"[-] Immagine non trovata per {name}")

        except Exception as e:
            print(f"[-] Errore durante l'estrazione di {name}: {e}")

    print(f"\nTotale prime pagine estratte con successo: {len(papers)}/{len(QUOTIDIANI_MAP)}")
    return papers

def main():
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([blog_id, client_id, client_secret, refresh_token]):
        raise ValueError("Tutti i Secret di Blogger devono essere configurati su GitHub.")

    papers = fetch_prime_pagine()
    if not papers:
        print("Nessuna prima pagina estratta. Interruzione.")
        return

    today_str = datetime.date.today().strftime("%d/%m/%Y")

    custom_css = """
<style>
  .prime-pagine-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 10px;
  }
  .prime-pagine-header {
    text-align: center;
    margin-bottom: 25px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }
  .prime-pagine-header p {
    font-size: 0.95rem;
    color: #4a5568;
    margin: 0;
  }
  .grid-edicola {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
  }
  .paper-card {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid #eef2f5;
    display: flex;
    flex-direction: column;
  }
  .paper-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
  }
  .paper-img-container {
    width: 100%;
    overflow: hidden;
    background: #f8fafc;
  }
  .paper-img-container img {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.3s ease;
  }
  .paper-card:hover .paper-img-container img {
    transform: scale(1.03);
  }
  .paper-info {
    padding: 14px;
    text-align: center;
    background: #ffffff;
    border-top: 1px solid #f0f4f8;
  }
  .paper-info h3 {
    margin: 0;
    font-size: 1.05rem !important;
    color: #1a365d !important;
    font-weight: 700 !important;
  }
  @media (max-width: 600px) {
    .grid-edicola {
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
    }
    .paper-info h3 {
      font-size: 0.9rem !important;
    }
  }
</style>
"""

    cards_html = ""
    for p in papers:
        # Nota: L'immagine si apre in una scheda separata direttamente alla foto originale senza link verso siti terzi
        cards_html += f"""
    <div class="paper-card">
      <div class="paper-img-container">
        <a href="{p['image_url']}" target="_blank" title="Ingrandisci {p['title']}">
          <img src="{p['image_url']}" alt="Prima pagina {p['title']} del {today_str}" loading="lazy" />
        </a>
      </div>
      <div class="paper-info">
        <h3>📰 {p['title']}</h3>
      </div>
    </div>
        """

    final_html = f"""
{custom_css}
<div class="prime-pagine-container">
  <div class="prime-pagine-header">
    <p>Edicola Digitale - Ultimo aggiornamento: <strong>{today_str}</strong></p>
  </div>
  <div class="grid-edicola">
    {cards_html}
  </div>
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

    # Cerca la pagina fissa per aggiornarla, altrimenti ne crea una nuova
    pages_list = blogger_service.pages().list(blogId=blog_id).execute()
    existing_page_id = None

    if "items" in pages_list:
        for page in pages_list["items"]:
            if page.get("title") == PAGE_TITLE:
                existing_page_id = page.get("id")
                break

    body_page = {
        "title": PAGE_TITLE,
        "content": final_html
    }

    if existing_page_id:
        print(f"Aggiornamento della Pagina fissa esistente (ID: {existing_page_id})...")
        updated_page = blogger_service.pages().patch(
            blogId=blog_id,
            pageId=existing_page_id,
            body=body_page
        ).execute()
        print(f"Pagina aggiornata con successo! URL: {updated_page.get('url')}")
    else:
        print("Creazione nuova Pagina fissa...")
        created_page = blogger_service.pages().insert(
            blogId=blog_id,
            body=body_page
        ).execute()
        print(f"Nuova Pagina creata con successo! URL: {created_page.get('url')}")

if __name__ == "__main__":
    main()
