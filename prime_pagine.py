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
# Sostituisci con l'URL di un'immagine 1200x675 px caricata su Blogger per ottimizzare Google Discover
COVER_IMAGE_URL = "https://static.brunorachiele.it/logo.png"

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
    """Estrae il primo titolo di apertura dai feed RSS dei principali quotidiani."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    headlines = []
    for feed in RSS_QUOTIDIANI:
        try:
            r = requests.get(feed["url"], headers=headers, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall("./channel/item"):
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
            root
