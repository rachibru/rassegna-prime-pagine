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

STATIC_REPO_DIR = "static_repo/copertine"
STATIC_BASE_URL = "https://static.brunorachiele.it/copertine"

QUOTIDIANI_MAP = [
    {"slug": "corriere-della-sera", "name": "Corriere della Sera", "url": "https://giornali.it/quotidiani-nazionali/corriere-della-sera/prima-pagina/"},
    {"slug": "la-repubblica", "name": "La Repubblica", "url": "https://giornali.it/quotidiani-nazionali/la-repubblica/prima-pagina/"},
    {"slug": "la-stampa", "name": "La Stampa", "url": "https://giornali.it/quotidiani-nazionali/la-stampa/prima-pagina/"},
    {"slug": "il-sole-24-ore", "name": "Il Sole 24 Ore", "url": "https://giornali.it/quotidiani-economici/il-sole-24-ore/prima-pagina/"},
    {"slug": "libero-quotidiano", "name": "Libero Quotidiano", "url": "https://giornali.it/quotidiani-nazionali/libero-quotidiano/prima-pagina/"},
    {"slug": "il-giornale", "name": "Il Giornale", "url": "https://giornali.it/quotidiani-nazionali/il-giornale/prima-pagina/"},
    {"slug": "il-fatto-quotidiano", "name": "Il Fatto Quotidiano", "url": "https://giornali.it/quotidiani-nazionali/il-fatto-quotidiano/prima-pagina/"},
    {"slug": "la-verita", "name": "La Verità", "url": "https://giornali.it/quotidiani-nazionali/la-verita/prima-pagina/"},
    {"slug": "il-tempo", "name": "Il Tempo", "url": "https://giornali.it/quotidiani-nazionali/il-tempo/prima-pagina/"},
    {"slug": "domani", "name": "Domani", "url": "https://giornali.it/quotidiani-nazionali/domani/prima-pagina/"},
    {"slug": "qn-quotidiano-nazionale", "name": "QN Quotidiano Nazionale", "url": "https://giornali.it/quotidiani-nazionali/qn-quotidiano-nazionale/prima-pagina/"},
    {"slug": "il-secolo-xix", "name": "Il Secolo XIX", "url": "https://giornali.it/quotidiani-locali/il-secolo-xix/prima-pagina/"},
    {"slug": "gazzetta-del-sud", "name": "Gazzetta del Sud", "url": "https://giornali.it/quotidiani-locali/gazzetta-del-sud/prima-pagina/"},
    {"slug": "the-new-york-times", "name": "The New York Times", "url": "https://giornali.it/quotidiani-esteri/the-new-york-times/prima-pagina/"},
    {"slug": "the-washington-post", "name": "The Washington Post", "url": "https://giornali.it/quotidiani-esteri/the-washington-post/prima-pagina/"},
    {"slug": "financial-times", "name": "Financial Times", "url": "https://giornali.it/quotidiani-esteri/financial-times/prima-pagina/"},
    {"slug": "le-figaro", "name": "Le Figaro", "url": "https://giornali.it/quotidiani-esteri/le-figaro/prima-pagina/"},
    {"slug": "le-monde", "name": "Le Monde", "url": "https://giornali.it/quotidiani-esteri/le-monde/prima-pagina/"},
    {"slug": "el-pais", "name": "El País", "url": "https://giornali.it/quotidiani-esteri/el-pais/prima-pagina/"},
    {"slug": "el-mundo", "name": "El Mundo", "url": "https://giornali.it/quotidiani-esteri/el-mundo/prima-pagina/"},
    {"slug": "abc-es", "name": "ABC", "url": "https://giornali.it/quotidiani-esteri/abc-es/prima-pagina/"}
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


def fetch_and_save_prime_pagine(cache_bust):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://giornali.it/"
    }

    os.makedirs(STATIC_REPO_DIR, exist_ok=True)
    papers = []
    session = requests.Session()

    for item in QUOTIDIANI_MAP:
        name = item["name"]
        slug = item["slug"]
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

                # Scarica e salva l'immagine nel repository static.brunorachiele.it
                img_resp = session.get(img_src, headers=headers, timeout=15)
                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                    ext = ".webp" if ".webp" in img_src.lower() else (".png" if ".png" in img_src.lower() else ".jpg")
                    filename = f"{slug}{ext}"
                    filepath = os.path.join(STATIC_REPO_DIR, filename)

                    # Rimuove eventuali vecchie estensioni diverse dello stesso giornale
                    for old_ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        old_path = os.path.join(STATIC_REPO_DIR, f"{slug}{old_ext}")
                        if old_path != filepath and os.path.exists(old_path):
                            os.remove(old_path)

                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)

                    final_url = f"{STATIC_BASE_URL}/{filename}?v={cache_bust}"
                    papers.append({
                        "title": name,
                        "image_url": final_url
                    })
                    print(f"[+] Salvata copertina di {name} -> {filename}")
                else:
                    print(f"[-] Download immagine fallito per {name} (HTTP {img_resp.status_code})")
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
                    if title_el is not None and title_el.text:
                        clean_title = BeautifulSoup(title_el.text, "html.parser").get_text().strip()
                        if len(clean_title) > 15:
                            headlines.append({
                                "source": feed["source"],
                                "title": clean_title
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

    tz_rome = zoneinfo.ZoneInfo("Europe/Rome")
    now_rome = datetime.datetime.now(tz_rome)
    today = now_rome.date()
    cache_bust = today.strftime("%Y%m%d")

    papers = fetch_and_save_prime_pagine(cache_bust)
    if not papers:
        print("Nessuna copertina estratta. Interruzione.")
        return

    day_name = GIORNI_ITA[today.weekday()]
    month_name = MESI_ITA[today.month]
    today_formatted = f"{today.day} {month_name} {today.year}"
    today_full = f"{day_name} {today_formatted}"
    today_str = today.strftime("%d/%m/%Y")
    now_iso = now_rome.isoformat()

    # 1. AGGIORNA SEMPRE LA PAGINA EDICOLA FISSA CON LIGHTBOX + ZOOM
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
    for idx, p in enumerate(papers):
        safe_title = p["title"].replace('"', "&quot;")
        cards_html += f"""
    <div class="paper-card" onclick="openPaperLightbox({idx})" role="button" tabindex="0" aria-label="Ingrandisci prima pagina {safe_title}">
      <div class="paper-img-container">
        <img src="{p['image_url']}" alt="Prima pagina {safe_title} del {today_str}" loading="lazy" />
        <span class="zoom-badge">🔍 Ingrandisci</span>
      </div>
      <div class="paper-info">
        <h3>📰 {p['title']}</h3>
      </div>
    </div>"""

    papers_js_json = json.dumps(papers, ensure_ascii=False)

    page_html = f"""
<script type="application/ld+json">
{schema_json}
</script>
<style>
  .prime-pagine-container {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 10px; }}
  .prime-pagine-header {{ text-align: center; margin-bottom: 20px; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }}
  .prime-pagine-header p {{ font-size: 0.95rem; color: #4a5568; margin: 0; }}
  .grid-edicola {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }}
  .paper-card {{ background: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); overflow: hidden; border: 1px solid #eef2f5; display: flex; flex-direction: column; cursor: pointer; transition: transform 0.18s ease, box-shadow 0.18s ease; }}
  .paper-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 24px rgba(11,74,159,0.14); }}
  .paper-img-container {{ position: relative; overflow: hidden; background: #f1f5f9; }}
  .paper-img-container img {{ width: 100%; height: auto; display: block; }}
  .zoom-badge {{ position: absolute; right: 10px; bottom: 10px; background: rgba(15,23,42,0.78); color: #ffffff; font-size: 0.75rem; font-weight: 600; padding: 5px 10px; border-radius: 999px; backdrop-filter: blur(4px); }}
  .paper-info {{ padding: 14px; text-align: center; background: #ffffff; border-top: 1px solid #f0f4f8; }}
  .paper-info h3 {{ margin: 0; font-size: 1.02rem !important; color: #1a365d !important; font-weight: 700 !important; }}

  /* Lightbox con Zoom */
  #pp-lightbox {{ display: none; position: fixed; inset: 0; z-index: 99999; background: rgba(10, 15, 28, 0.94); flex-direction: column; }}
  #pp-lightbox.open {{ display: flex; }}
  .pp-lb-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; background: rgba(15,23,42,0.9); color: #fff; border-bottom: 1px solid rgba(255,255,255,0.12); gap: 10px; flex-wrap: wrap; }}
  .pp-lb-title {{ font-weight: 700; font-size: 1rem; }}
  .pp-lb-controls {{ display: flex; align-items: center; gap: 8px; }}
  .pp-lb-btn {{ background: rgba(255,255,255,0.14); color: #fff; border: 1px solid rgba(255,255,255,0.22); border-radius: 8px; padding: 6px 12px; font-size: 0.95rem; font-weight: 700; cursor: pointer; }}
  .pp-lb-btn:hover {{ background: rgba(255,255,255,0.26); }}
  .pp-lb-stage {{ flex: 1; overflow: auto; display: flex; align-items: flex-start; justify-content: center; padding: 20px; position: relative; }}
  #pp-lb-img {{ max-width: 92vw; max-height: 82vh; width: auto; height: auto; border-radius: 6px; box-shadow: 0 12px 40px rgba(0,0,0,0.5); transition: width 0.15s ease; cursor: zoom-in; }}
  #pp-lb-img.zoomed {{ max-width: none; max-height: none; cursor: zoom-out; }}
  @media (max-width: 600px) {{ .grid-edicola {{ grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: 12px; }} }}
</style>

<div class="prime-pagine-container">
  <div class="prime-pagine-header">
    <p>Edicola Digitale di <strong>brunorachiele.it</strong> - Aggiornata al <strong>{today_str}</strong> · Tocca una prima pagina per ingrandirla</p>
  </div>
  <div class="grid-edicola">
    {cards_html}
  </div>
</div>

<div id="pp-lightbox" aria-hidden="true">
  <div class="pp-lb-bar">
    <div class="pp-lb-title" id="pp-lb-title"></div>
    <div class="pp-lb-controls">
      <button type="button" class="pp-lb-btn" onclick="stepPaper(-1)" title="Precedente">&lsaquo;</button>
      <button type="button" class="pp-lb-btn" onclick="stepPaper(1)" title="Successiva">&rsaquo;</button>
      <button type="button" class="pp-lb-btn" onclick="changeZoom(-0.35)" title="Riduci">&minus;</button>
      <button type="button" class="pp-lb-btn" onclick="resetZoom()" id="pp-zoom-label">100%</button>
      <button type="button" class="pp-lb-btn" onclick="changeZoom(0.35)" title="Ingrandisci">+</button>
      <button type="button" class="pp-lb-btn" onclick="closePaperLightbox()" title="Chiudi">&#10005;</button>
    </div>
  </div>
  <div class="pp-lb-stage" id="pp-lb-stage" onclick="if(event.target===this) closePaperLightbox()">
    <img id="pp-lb-img" src="" alt="" onclick="toggleQuickZoom()" />
  </div>
</div>

<script>
  const PP_PAPERS = {papers_js_json};
  let ppCurrentIdx = 0;
  let ppZoom = 1;

  function renderLightbox() {{
    const p = PP_PAPERS[ppCurrentIdx];
    const img = document.getElementById("pp-lb-img");
    document.getElementById("pp-lb-title").textContent = p.title + " (" + (ppCurrentIdx + 1) + "/" + PP_PAPERS.length + ")";
    img.src = p.image_url;
    img.alt = "Prima pagina " + p.title;
    resetZoom();
  }}

  function openPaperLightbox(idx) {{
    ppCurrentIdx = idx;
    renderLightbox();
    document.getElementById("pp-lightbox").classList.add("open");
    document.body.style.overflow = "hidden";
  }}

  function closePaperLightbox() {{
    document.getElementById("pp-lightbox").classList.remove("open");
    document.body.style.overflow = "";
  }}

  function stepPaper(delta) {{
    ppCurrentIdx = (ppCurrentIdx + delta + PP_PAPERS.length) % PP_PAPERS.length;
    renderLightbox();
  }}

  function applyZoom() {{
    const img = document.getElementById("pp-lb-img");
    const label = document.getElementById("pp-zoom-label");
    label.textContent = Math.round(ppZoom * 100) + "%";
    if (ppZoom <= 1.01) {{
      img.classList.remove("zoomed");
      img.style.width = "";
    }} else {{
      img.classList.add("zoomed");
      img.style.width = Math.round(ppZoom * 90) + "vw";
    }}
  }}

  function changeZoom(delta) {{
    ppZoom = Math.min(2.75, Math.max(1, ppZoom + delta));
    applyZoom();
  }}

  function resetZoom() {{
    ppZoom = 1;
    applyZoom();
  }}

  function toggleQuickZoom() {{
    ppZoom = ppZoom > 1.01 ? 1 : 1.75;
    applyZoom();
  }}

  document.addEventListener("keydown", function(e) {{
    const lb = document.getElementById("pp-lightbox");
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") closePaperLightbox();
    if (e.key === "ArrowLeft") stepPaper(-1);
    if (e.key === "ArrowRight") stepPaper(1);
  }});
</script>
"""

    updated_page = blogger_service.pages().update(
        blogId=blog_id,
        pageId=TARGET_PAGE_ID,
        body={"id": TARGET_PAGE_ID, "title": dynamic_page_title, "content": page_html},
        publish=True
    ).execute()
    print(f"[SUCCESS] Pagina fissa aggiornata: {updated_page.get('url')}")

    # 2. LA DOMENICA (weekday == 6) SALTA IL POST BREVE: ESCE SOLO LA RASSEGNA COMPLETA
    if today.weekday() == 6:
        print("[INFO] Oggi è domenica: salto il post breve per evitare doppioni con la Rassegna Stampa Domenicale.")
        return

    # 3. DAL LUNEDÌ AL SABATO CREA IL NUOVO ARTICOLO GIORNALIERO CON SINTESI EDITORIALE PULITA
    post_title = f"Prime pagine dei quotidiani di oggi {today_full}: i titoli in edicola"
    existing_url = post_already_exists_today(blogger_service, blog_id, post_title)
    if existing_url:
        print(f"[INFO] Articolo del giorno già pubblicato ({existing_url}). Stop.")
        return

    headlines = fetch_morning_headlines()
    headlines_html = ""
    if headlines:
        blocks = []
        for h in headlines:
            blocks.append(
                f"<div style='padding:12px 14px; background:#ffffff; border:1px solid #e2e8f0; border-radius:8px;'>"
                f"<span style='display:inline-block; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:#0b4a9f; margin-bottom:4px;'>{h['source']}</span>"
                f"<p style='margin:0; font-size:0.98rem; font-weight:600; color:#0f172a; line-height:1.45;'>&laquo;{h['title']}&raquo;</p>"
                f"</div>"
            )
        cards_grid = "".join(blocks)
        headlines_html = f"""
  <div style="margin:22px 0; padding:18px; background:#f8fafc; border-left:4px solid #0b4a9f; border-radius:10px;">
    <h2 style="margin:0 0 14px; font-size:1.15rem; color:#0f172a;">I temi principali in apertura stamattina</h2>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px;">
      {cards_grid}
    </div>
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
