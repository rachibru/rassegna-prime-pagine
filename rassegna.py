# 4. Generazione Rassegna Stampa
prompt = f"""
Sei un giornalista politico ed editor-in-chief.
Elabora un commento e una rassegna sintetica delle prime pagine dei principali quotidiani italiani di oggi ({data_oggi}).

Restituisci l'output ESCLUSIVAMENTE in codice HTML pulito (senza <html> o <body>).
Struttura il testo così:
<h3>🗞️ Il Tema Centrale di Oggi</h3>
<p>[Analisi del fatto principale sui giornali]</p>

<h3>📊 I Punti di Vista delle Testate</h3>
<ul>
  <li><strong>Corriere e Repubblica:</strong> [Focus principale]</li>
  <li><strong>La Stampa e Il Secolo XIX:</strong> [Taglio politico/sociale]</li>
  <li><strong>Il Foglio e La Ragione:</strong> [Opinioni e commenti]</li>
</ul>

<h3>💡 Il Commento della Redazione</h3>
<p>[Riflessione finale di Bruno Rachiele]</p>
"""

print("🧠 Generazione testo con Gemini...")

# Usiamo l'alias generico oppure la ricerca dinamica del modello disponibile
try:
    response = client.models.generate_content(
        model='gemini-flash',
        contents=prompt,
    )
except Exception:
    # Fallback automatico cercando il primo modello che supporta la generazione
    modelli_disponibili = [
        m.name for m in client.models.list() 
        if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]
    modello_valido = modelli_disponibili[0] if modelli_disponibili else "gemini-2.0-flash"
    print(f"🔄 Uso il modello rilevato automaticamente: {modello_valido}")
    response = client.models.generate_content(
        model=modello_valido,
        contents=prompt,
    )

html_content = response.text
