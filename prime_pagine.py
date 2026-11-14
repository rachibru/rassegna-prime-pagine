import os
import json
import datetime
import requests
import zoneinfo
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TARGET_PAGE_ID = "4213404198440467971"
STATIC_PAGE_URL = "https://www.brunorachiele.it/p/prime-pagine-dei-giornali.html"
COVER_IMAGE_URL = "https://static.brunorachiele.it/primepagine.png"

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

RSS_QUOTIDIANI = [
    {"source": "ANSA", "url": "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml"},
    {"source": "Corriere della Sera", "url": "https://xml2.corriereobjects.it/rss/homepage.xml"},
    {"source": "La Repubblica", "url": "https://www.repubblica.it/rss/homepage/rss2.0.xml"},
    {"source": "Il Sole 24 Ore", "url": "https://www.ilsole24ore.com/rss/italia.xml"}
]

MESI_ITA = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
    5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
    9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
}

GIORNI_ITA = {
    0: "lunedì", 1: "martedì", 2: "mercoledì", 3: "giovedì",
    4: "venerdì", 5: "sabato", 6: "domenica"
}

MGID_WIDGET_HTML = """
<div data-type="_mgwidget" data-widget-id="2120271"></div>
<script>(function(w,q){w[q]=w[q]||[];w[q].push(["_mgc.load"])})(window,"_mgq");</script>
"""


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
                print(f"[+] Estratta copertina di: {name}")
            else:
                print(f"[-] Copertina non trovata per: {name}")

        except Exception as e:
            print(f"[-] Errore durante l'estrazione di {name}: {e}")

    return papers


def fetch_morning_headlines():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    headlines = []
    for feed in RSS_QUOTIDIANI:
        try:
            r = requests.get(feed["url"], headers=headers, timeout=10)
            if r.status_code == 200:
                xml_root = ET.fromstring(r.content)
                for item in xml_root.findall("./channel/item"):
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    if title_el is not None and title_el.text:
                        clean_title = BeautifulSoup(title_el.text, "html.parser").get_text().strip()
                        clean_desc = ""
                        if desc_el is not None and desc_el.text:
                            raw_desc = BeautifulSoup(desc_el.text, "html.parser").get_text().strip()
                            if len(raw_desc) > 20 and raw_desc.lower() != clean_title.lower():
                                clean_desc = raw_desc[:180].rstrip(" ,;:") + "..."
                        if len(clean_title) > 15:
                            headlines.append({
                                "source": feed["source"],
                                "title": clean_title,
                                "summary": clean_desc
                            })
                            print(f"[+] Titolo RSS estratto da {feed['source']}: {clean_title[:60]}...")
                            break
        except Exception as e:
            print(f"[-] Errore lettura RSS {feed['source']}: {e}")
    return headlines


def fetch_latest_3_articles():
    rss_url = "https://www.brunorachiele.it/feeds/posts/default?alt=rss&max-results=10"
    articles = []
    try:
        r = requests.get(rss_url, timeout=10)
        if r.status_code == 200:
            xml_root = ET.fromstring(r.content)
            for item in xml_root.findall("./channel/item"):
                title_el = item.find("title")
                link_el = item.find("link")
                categories = [c.text.lower() for c in item.findall("category") if c.text]
                if title_el is not None and link_el is not None:
                    title = title_el.text.strip()
                    link = link_el.text.strip()
                    if "prime pagine" in categories or "prime pagine" in title.lower():
                        continue
                    articles.append({"title": title, "link": link})
                    if len(articles) == 3:
                        break
    except Exception as e:
        print(f"[-] Errore lettura RSS interno: {e}")
    return articles


def post_already_exists_today(blogger_service, blog_id, post_title):
    try:
        res = blogger_service.posts().list(
            blogId=blog_id,
            labels="Prime Pagine",
            maxResults=5,
            fields="items(id,title,url)"
        ).execute()
        for item in res.get("items", []):
            if item.get("title", "").strip().lower() == post_title.strip().lower():
                return item.get("url")
    except Exception as e:
        print(f"[-] Controllo duplicati post: {e}")
    return None


def main():
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/blogger"]
    )
    blogger_service = build("blogger", "v3", credentials=creds)

    papers = fetch_prime_pagine()
    if not papers:
        print("Nessuna copertina estratta. Interruzione.")
        return

    tz_rome = zoneinfo.ZoneInfo("Europe/Rome")
    now_rome = datetime.datetime.now(tz_rome)
    today = now_rome.date()

    day_name = GIORNI_ITA[today.weekday()]
    month_name = MESI_ITA[today.month]
    today_formatted = f"{today.day} {month_name} {today.year}"
    today_full = f"{day_name} {today_formatted}"
    today_str = today.strftime("%d/%m/%Y")
    now_iso = now_rome.isoformat()

    # 1. AGGIORNA LA PAGINA EDICOLA FISSA (TARGET_PAGE_ID)
    dynamic_page_title = f"#primepagine del {today_formatted}"

    schema_data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": f"Prime Pagine dei Giornali del {today_formatted}",
        "description": f"Consulta le prime pagine e copertine dei principali quotidiani italiani ed esteri aggiornate al {today_formatted}.",
        "datePublished": now_iso,
        "dateModified": now_iso,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": STATIC_PAGE_URL
        },
        "author": {
            "@type": "Person",
            "name": "Bruno Rachiele",
            "url": "https://bio.brunorachiele.it/"
        },
        "publisher": {
            "@type": "Organization",
            "name": "brunorachiele.it",
            "logo": {
                "@type": "ImageObject",
                "url": COVER_IMAGE_URL
            }
        },
        "image": [p["image_url"] for p in papers[:3]]
    }
    schema_json = json.dumps(schema_data, ensure_ascii=False)

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

    page_html = f"""
<script type="application/ld+json">
{schema_json}
</script>
<style>
  .prime-pagine-container {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 10px; }}
  .prime-pagine-header {{ text-align: center; margin-bottom: 20px; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }}
  .prime-pagine-header p {{ font-size: 0.95rem; color: #4a5568; margin: 0; }}
  .grid-edicola {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
  .paper-card {{ background: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); overflow: hidden; border: 1px solid #eef2f5; display: flex; flex-direction: column; }}
  .paper-img-container img {{ width: 100%; height: auto; display: block; pointer-events: none; }}
  .paper-info {{ padding: 14px; text-align: center; background: #ffffff; border-top: 1px solid #f0f4f8; }}
  .paper-info h3 {{ margin: 0; font-size: 1.05rem !important; color: #1a365d !important; font-weight: 700 !important; }}
  @media (max-width: 600px) {{ .grid-edicola {{ grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }} }}
</style>
<div class="prime-pagine-container">
  <div class="prime-pagine-header">
    <p>Edicola Digitale di <strong>brunorachiele.it</strong> - Aggiornata al <strong>{today_str}</strong></p>
  </div>
  <div class="grid-edicola">
    {cards_html}
  </div>
</div>
"""

    updated_page = blogger_service.pages().update(
        blogId=blog_id,
        pageId=TARGET_PAGE_ID,
        body={"id": TARGET_PAGE_ID, "title": dynamic_page_title, "content": page_html},
        publish=True
    ).execute()
    print(f"[SUCCESS] Pagina fissa aggiornata: {updated_page.get('url')}")

    # 2. CREA IL NUOVO ARTICOLO GIORNALIERO CON TITOLI RSS
    post_title = f"Prime pagine dei quotidiani di oggi {today_full}: i titoli in edicola"
    existing_url = post_already_exists_today(blogger_service, blog_id, post_title)
    if existing_url:
        print(f"[INFO] Articolo del giorno già pubblicato ({existing_url}). Stop.")
        return

    headlines = fetch_morning_headlines()
    headlines_html = ""
    if headlines:
        items_headlines = ""
        for h in headlines:
            desc_part = f"<br><span style='color:#475569; font-size:0.95rem;'>{h['summary']}</span>" if h["summary"] else ""
            items_headlines += f"<li style='margin-bottom:12px;'><strong>{h['source']}:</strong> &laquo;{h['title']}&raquo;{desc_part}</li>"

        headlines_html = f"""
  <div style="margin:22px 0; padding:18px 20px; background:#f8fafc; border-left:4px solid #0b4a9f; border-radius:8px;">
    <h2 style="margin:0 0 12px; font-size:1.18rem; color:#0f172a;">I temi principali in apertura stamattina</h2>
    <ul style="margin:0; padding-left:18px; line-height:1.6;">
      {items_headlines}
    </ul>
  </div>"""

    latest_articles = fetch_latest_3_articles()
    feed_html = ""
    if latest_articles:
        items_li = "".join(f'<li><a href="{a["link"]}">{a["title"]}</a></li>' for a in latest_articles)
        feed_html = f"""
  <div style="margin-top:26px; padding:18px 20px; background:#f1f5f9; border-radius:10px; border:1px solid #cbd5e1;">
    <h2 style="margin:0 0 10px; font-size:1.15rem; color:#0f172a;">Da leggere oggi su brunorachiele.it</h2>
    <ul style="margin:0; padding-left:20px; line-height:1.65;">
      {items_li}
    </ul>
  </div>"""

    quotidiani_list_html = "".join(f"<li><strong>{p['title']}</strong> — edizione di {today_full}</li>" for p in papers)

    post_html = f"""
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; max-width:820px; margin:0 auto; line-height:1.65; color:#1e293b;">
  <div style="margin-bottom:18px; text-align:center;">
    <img src="{COVER_IMAGE_URL}" alt="Rassegna stampa prime pagine {today_full} - brunorachiele.it" style="max-width:100%; height:auto; border-radius:10px;" />
  </div>

  <p>Buongiorno da <strong>brunorachiele.it</strong>. Ecco la rassegna stampa mattutina di <strong>{today_full}</strong> con i principali titoli in apertura su politica, economia ed esteri e l'accesso diretto all'edicola digitale completa dei quotidiani oggi in uscita.</p>

  {headlines_html}

  <div style="text-align:center; margin:24px 0; padding:22px 18px; background:linear-gradient(135deg,#0b4a9f 0%,#1d4ed8 100%); border-radius:12px; color:#ffffff;">
    <p style="margin:0 0 12px; font-size:1.15rem; font-weight:700; color:#ffffff;">Sfoglia tutte le prime pagine di oggi in alta risoluzione</p>
    <a href="{STATIC_PAGE_URL}" style="display:inline-block; background:#ffffff; color:#0b4a9f !important; font-weight:700; padding:12px 24px; border-radius:50px; text-decoration:none; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
      Apri l'Edicola Digitale del {today_str} &rarr;
    </a>
  </div>

  <div style="margin:24px auto; text-align:center;">
    {MGID_WIDGET_HTML}
  </div>

  <h2 style="font-size:1.2rem; color:#0f172a; margin-top:24px;">I quotidiani disponibili nell'edizione di oggi</h2>
  <ul style="padding-left:20px; line-height:1.7;">
    {quotidiani_list_html}
  </ul>

  {feed_html}
</div>
"""

    created_post = blogger_service.posts().insert(
        blogId=blog_id,
        body={
            "title": post_title,
            "content": post_html,
            "labels": ["Prime Pagine", "Rassegna Stampa"]
        },
        isDraft=False
    ).execute()
    print(f"[SUCCESS] Nuovo articolo giornaliero pubblicato: {created_post.get('url')}")


if __name__ == "__main__":
    main()
