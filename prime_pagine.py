import requests
from bs4 import BeautifulSoup
import re

def fetch_gazzetta_front_pages():
    """Test di estrazione delle prime pagine dei principali quotidiani."""
    # Portale edicola pubblico di riferimento
    url = "https://www.gazzetta.it/primapagina/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Download della pagina edicola in corso...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Errore nel recupero pagina: status {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    papers = []

    # Cerca le immagini e i titoli delle prime pagine nel layout
    img_tags = soup.find_all("img")
    
    for img in img_tags:
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt") or ""
        
        if src and ("prime-pagine" in src or "prima_pagina" in src or "copertina" in src or "frontpage" in src):
            papers.append({
                "title": alt if alt else "Quotidiano",
                "image_url": src
            })

    return papers

if __name__ == "__main__":
    results = fetch_gazzetta_front_pages()
    print(f"\nTrovate {len(results)} prime pagine:")
    for p in results[:10]:
        print(f"- {p['title']}: {p['image_url']}")
