name: Aggiornamento Edicola e Rassegna Domenicale

on:
  schedule:
    # 04:12 UTC = 06:12 ora italiana (ora legale CEST)
    # 05:12 UTC = 06:12 ora italiana (ora solare CET)
    - cron: '12 4 * * *'
    - cron: '12 5 * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository principale
        uses: actions/checkout@v4

      - name: Checkout repository static.brunorachiele.it
        uses: actions/checkout@v4
        with:
          repository: TUO_USERNAME/TUO_REPO_STATIC
          token: ${{ secrets.STATIC_REPO_TOKEN }}
          path: static_repo

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 feedparser google-genai google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

      - name: Run Prime Pagine script
        env:
          BLOGGER_BLOG_ID: ${{ secrets.BLOGGER_BLOG_ID }}
          BLOGGER_CLIENT_ID: ${{ secrets.BLOGGER_CLIENT_ID }}
          BLOGGER_CLIENT_SECRET: ${{ secrets.BLOGGER_CLIENT_SECRET }}
          BLOGGER_REFRESH_TOKEN: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
        run: python prime_pagine.py

      - name: Pubblica copertine su static.brunorachiele.it
        working-directory: static_repo
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add copertine/
          git commit -m "Aggiornamento copertine quotidiane" || exit 0
          git push

      - name: Run Rassegna Stampa Domenicale
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          BLOGGER_BLOG_ID: ${{ secrets.BLOGGER_BLOG_ID }}
          BLOGGER_CLIENT_ID: ${{ secrets.BLOGGER_CLIENT_ID }}
          BLOGGER_CLIENT_SECRET: ${{ secrets.BLOGGER_CLIENT_SECRET }}
          BLOGGER_REFRESH_TOKEN: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
        run: python rassegna.py
