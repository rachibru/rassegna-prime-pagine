import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PAGE_TITLE = "#primepagine"
TARGET_PAGE_ID = "4213404198440467971"

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

def extract_image_url(img_tag):
    """Estrae il miglior URL dell'immagine valutando vari attributi."""
    if not img_tag:
        return None

    # Controlla srcset se presente (spesso contiene l'immagine ad alta risoluzione)
    srcset = img_tag.get("srcset") or img_tag.get("data-srcset") or ""
    if srcset:
        urls = [item.strip().split(" ")[0] for item in srcset.split(",") if item.strip()]
        if urls:
            return urls[-1] # Prende l'ultima (di solito la risoluzione più alta)

    # Controlla attributi standard
    for attr in ["data-src", "data-lazy-src", "src", "data-original"]:
        val = img_tag.get(attr)
        if val and not val.startswith("data:image"):
            return val

    return None

def fetch_prime_pagine():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.giornalone.it/"
    }

    papers = []
    session = requests.Session()

    for item in QUOTIDIANI_MAP:
        name = item["name"]
        page_url = item["url"]
        
        try:
            print(f"Scraping per: {name}...")
            response = session.get(page_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[-] Errore HTTP {response.status_code} su {name}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            img_src = None

            # 1. Cerca l'immagine principale con id o classe 'copertina'
            target_img = soup.find("img", id=lambda x: x and "copertina" in x.lower()) or \
                         soup.find("img", class_=lambda x: x and "copertina" in x.lower()) or \
                         soup.find("img", alt=lambda x: x and "prima pagina" in x.lower())

            img_src = extract_image_url(target_img)

            # 2. Fallback: Cerca dentro l'articolo principale
            if not img_src:
                article = soup.find("article") or soup.find("main") or soup.find("div", class_=lambda x: x and "content" in x.lower())
                if article:
                    for img in article.find_all("img"):
                        candidate = extract_image_url(img)
                        if candidate and "logo" not in candidate.lower() and "icon" not in candidate.lower():
                            img_src = candidate
                            break

            if img_src:
                # Pulisce parametri di query se presenti
                img_src = img_src.split("?")[0]

                if img_src.startswith("//"):
                    img_src = "https:" + img_src
                elif img_src.startswith("/"):
                    img_src = "https://www.giornalone.it" + img_src

                papers.append({
                    "title": name,
                    "image_url": img_src
                })
                print(f"[+] Estratto con successo {name}: {img_src}")
            else:
                print(f"[-] Immagine non individuata per {name}")

        except Exception as e:
            print(f"[-] Eccezione su {name}: {e}")

    return papers

def main():
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    papers = fetch_prime_pagine()
    print(f"\n==========================================")
    print(f"TOTALE COPERTINE ESTRATTE: {len(papers)}/{len(QUOTIDIANI_MAP)}")
    print(f"==========================================")

    if not papers:
        print("Nessuna copertina estratta. Impossibile aggiornare la pagina.")
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

    body_page = {
        "id": TARGET_PAGE_ID,
        "title": PAGE_TITLE,
        "content": final_html
    }

    print(f"Invio aggiornamento alla pagina ID {TARGET_PAGE_ID} su Blogger...")
    updated_page = blogger_service.pages().update(
        blogId=blog_id,
        pageId=TARGET_PAGE_ID,
        body=body_page,
        publish=True
    ).execute()
    
    print(f"[SUCCESS] Pagina aggiornata e pubblicata! Link: {updated_page.get('url')}")

if __name__ == "__main__":
    main()
