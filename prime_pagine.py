import os
import datetime
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PAGE_TITLE = "#primepagine"
TARGET_PAGE_ID = "4213404198440467971"

# Mappatura con gli URL esatti forniti dall'utente
QUOTIDIANI_MAP = [
    {"name": "Corriere della Sera", "url": "https://giornali.it/quotidiani-nazionali/corriere-della-sera/prima-pagina/"},
    {"name": "La Repubblica", "url": "https://giornali.it/quotidiani-nazionali/la-repubblica/prima-pagina/"},
    {"name": "La Stampa", "url": "https://giornali.it/quotidiani-nazionali/la-stampa/prima-pagina/"},
    {"name": "Libero Quotidiano", "url": "https://giornali.it/quotidiani-nazionali/libero-quotidiano/prima-pagina/"},
    {"name": "Il Giornale", "url": "https://giornali.it/quotidiani-nazionali/il-giornale/prima-pagina/"},
    {"name": "Il Secolo XIX", "url": "https://giornali.it/quotidiani-locali/il-secolo-xix/prima-pagina/"},
    {"name": "Il Sole 24 Ore", "url": "https://giornali.it/quotidiani-economici/il-sole-24-ore/prima-pagina/"},
    {"name": "Le Monde", "url": "https://giornali.it/quotidiani-esteri/le-monde/prima-pagina/"},
    {"name": "Le Figaro", "url": "https://giornali.it/quotidiani-esteri/le-figaro/prima-pagina/"},
    {"name": "El País", "url": "https://giornali.it/quotidiani-esteri/el-pais/prima-pagina/"},
    {"name": "The New York Times", "url": "https://giornali.it/quotidiani-esteri/the-new-york-times/prima-pagina/"},
    {"name": "Financial Times", "url": "https://giornali.it/quotidiani-esteri/financial-times/prima-pagina/"}
]

def fetch_prime_pagine():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://giornali.it/"
    }

    papers = []
    session = requests.Session()

    for item in QUOTIDIANI_MAP:
        name = item["name"]
        page_url = item["url"]
        
        try:
            print(f"Scraping da giornali.it per: {name}...")
            response = session.get(page_url, headers=headers, timeout=12)
            if response.status_code != 200:
                print(f"[-] HTTP {response.status_code} su {name}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            img_src = None

            # Estrazione immagine di copertina
            img_tag = soup.find("img", class_=lambda x: x and "cover" in x.lower()) or \
                      soup.find("img", id=lambda x: x and "cover" in x.lower()) or \
                      soup.find("img", alt=lambda x: x and "prima pagina" in x.lower())

            if img_tag:
                img_src = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-lazy-src")
            else:
                main_div = soup.find("div", class_=lambda x: x and ("content" in x.lower() or "entry" in x.lower())) or soup.find("article")
                if main_div:
                    for img in main_div.find_all("img"):
                        src = img.get("src") or img.get("data-src") or ""
                        if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                            if not any(bad in src.lower() for bad in ["logo", "icon", "banner", "avatar"]):
                                img_src = src
                                break

            if img_src:
                img_src = img_src.split("?")[0]
                if img_src.startswith("//"):
                    img_src = "https:" + img_src
                elif img_src.startswith("/"):
                    img_src = "https://giornali.it" + img_src

                papers.append({
                    "title": name,
                    "image_url": img_src
                })
                print(f"[+] Estratta con successo copertina di: {name}")
            else:
                print(f"[-] Copertina non trovata per: {name}")

        except Exception as e:
            print(f"[-] Errore durante l'estrazione di {name}: {e}")

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
        print("Nessuna copertina estratta. Interruzione.")
        return

    today_str = datetime.date.today().strftime("%d/%m/%Y")

    custom_css = """<style>
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
    pointer-events: none;
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
</style>"""

    cards_html = ""
    for p in papers:
        cards_html += f"""
    <div class="paper-card">
      <div class="paper-img-container">
        <img src="{p['image_url']}" alt="Prima pagina {p['title']} del {today_str}" loading="lazy" />
      </div>
      <div class="paper-info">
        <h3>📰 {p['title']}</h3>
      </div>
    </div>"""

    final_html = f"""{custom_css}
<div class="prime-pagine-container">
  <div class="prime-pagine-header">
    <p>Edicola Digitale - Ultimo aggiornamento: <strong>{today_str}</strong></p>
  </div>
  <div class="grid-edicola">
    {cards_html}
  </div>
</div>"""

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
    
    print(f"[SUCCESS] Pagina aggiornata con successo! Link: {updated_page.get('url')}")

if __name__ == "__main__":
    main()
