import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TARGET_PAGE_ID = "4213404198440467971"

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

MESI_ITA = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
    5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
    9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
}

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

    today = datetime.date.today()
    month_name = MESI_ITA.get(today.month, today.strftime("%B"))
    today_formatted = f"{today.day} {month_name} {today.year}"
    today_str = today.strftime("%d/%m/%Y")

    dynamic_page_title = f"#primepagine del {today_formatted}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    schema_data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": f"Prime Pagine dei Giornali del {today_formatted}",
        "description": f"Consulta le prime pagine e copertine dei principali quotidiani italiani ed esteri aggiornate al {today_formatted}.",
        "datePublished": now_iso,
        "dateModified": now_iso,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": "https://www.brunorachiele.it/p/prime-pagine-dei-giornali.html"
        },
        "author": {
            "@type": "Person",
            "name": "Bruno Rachiele",
            "url": "https://www.brunorachiele.it/"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Bruno Rachiele",
            "logo": {
                "@type": "ImageObject",
                "url": "https://www.brunorachiele.it/favicon.ico"
            }
        },
        "image": [p["image_url"] for p in papers[:3]]
    }

    schema_json = json.dumps(schema_data, ensure_ascii=False)

    custom_css = """<style>
  .prime-pagine-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 10px;
  }
  .prime-pagine-header {
    text-align: center;
    margin-bottom: 20px;
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
  
  .commento-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: #ffffff;
    border-radius: 12px;
    padding: 20px 25px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.25);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .commento-banner h2 {
    margin: 0;
    font-size: 1.35rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    letter-spacing: -0.02em;
  }
  .commento-banner p {
    margin: 0;
    font-size: 1rem;
    color: #e0f2fe;
    max-width: 750px;
    font-weight: 600;
  }
  .commento-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #ffffff;
    color: #1e3a8a !important;
    font-weight: 700;
    font-size: 1rem;
    padding: 12px 24px;
    border-radius: 50px;
    text-decoration: none !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-top: 5px;
  }
  .commento-btn:hover {
    background-color: #f8fafc;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
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
    .commento-banner {
      padding: 18px 15px;
    }
    .commento-banner h2 {
      font-size: 1.15rem !important;
    }
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

    # HTML con script JS dinamico per leggere il post più recente in tempo reale lato client
    final_html = f"""
<script type="application/ld+json">
{schema_json}
</script>

{custom_css}
<div class="prime-pagine-container">
  <div class="prime-pagine-header">
    <p>Edicola Digitale - Ultimo aggiornamento: <strong>{today_str}</strong></p>
  </div>

  <!-- Box Promo Commento Ultima Rassegna Stampa -->
  <div class="commento-banner">
    <h2>✍️ Il Commento di Oggi</h2>
    <p id="rassegna-post-title">Caricamento dell'ultimo commento in corso...</p>
    <a href="https://www.brunorachiele.it/search/label/Rassegna%20Stampa" id="rassegna-post-link" class="commento-btn" target="_blank">
      Leggi il commento alle notizie di oggi &rarr;
    </a>
  </div>

  <div class="grid-edicola">
    {cards_html}
  </div>
</div>

<script>
  (function() {{
    var feedUrl = "https://www.brunorachiele.it/feeds/posts/default/-/Rassegna%20Stampa?alt=json&max-results=1";
    fetch(feedUrl)
      .then(function(response) {{ return response.json(); }})
      .then(function(data) {{
        if (data.feed && data.feed.entry && data.feed.entry.length > 0) {{
          var entry = data.feed.entry[0];
          var title = entry.title.$t;
          var link = "https://www.brunorachiele.it/search/label/Rassegna%20Stampa";
          if (entry.link) {{
            for (var i = 0; i < entry.link.length; i++) {{
              if (entry.link[i].rel === "alternate") {{
                link = entry.link[i].href;
                break;
              }}
            }}
          }}
          var titleElem = document.getElementById("rassegna-post-title");
          var linkElem = document.getElementById("rassegna-post-link");
          if (titleElem) titleElem.innerText = '"' + title + '"';
          if (linkElem) linkElem.href = link;
        }}
      }})
      .catch(function(err) {{
        console.error("Errore durante il caricamento dinamico della Rassegna Stampa:", err);
      }});
  }})();
</script>
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
        "title": dynamic_page_title,
        "content": final_html
    }

    print(f"Invio aggiornamento a Blogger (Titolo: '{dynamic_page_title}', ID: {TARGET_PAGE_ID})...")
    updated_page = blogger_service.pages().update(
        blogId=blog_id,
        pageId=TARGET_PAGE_ID,
        body=body_page,
        publish=True
    ).execute()
    
    print(f"[SUCCESS] Pagina aggiornata e pubblicata! Link: {updated_page.get('url')}")

if __name__ == "__main__":
    main()
