import streamlit as st
import pandas as pd
import yfinance as yf
import math
import time
import json
import urllib.request

st.set_page_config(
    page_title="Global Wheel Strategy Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Global Market Wheel Strategy Scanner")

# Initialisation des 10 listes personnalisées dans la session Streamlit
if "custom_lists" not in st.session_state:
    st.session_state.custom_lists = {
        f"Liste Personnalisée {i}": "SHOP.TO, CSU.TO, RY.TO, TD.TO, AAPL, MSFT" for i in range(1, 11)
    }

# ==============================================================================
# 1. VERSION US (DYNAMIQUE VIA NASDAQ TRADER) - NE PAS MODIFIER
# ==============================================================================
@st.cache_data(ttl=86400)
def charger_marche_us_dynamique():
    secteurs_us = {
        "Technologie - US (Dynamique)": [],
        "Santé - US (Dynamique)": [],
        "Finance - US (Dynamique)": [],
        "Énergie - US (Dynamique)": [],
        "Industriels - US (Dynamique)": [],
        "Tous les US (Global)": []
    }
    mots_cles = {
        "Technologie": ["TECH", "SOFTWARE", "SEMICONDUCTOR", "COMPUTER", "INTERNET", "CYBER", "CLOUD", "DATA", "CHIP", "ELECTRONIC", "SYSTEMS"],
        "Santé": ["PHARMACEUTICAL", "BIOTECHNOLOGY", "MEDICAL", "HEALTH", "THERAPEUTICS", "LABORATORIES"],
        "Finance": ["BANK", "FINANCIAL", "CAPITAL", "INVESTMENT", "INSURANCE", "BANCORP", "TRUST"],
        "Énergie": ["ENERGY", "OIL", "GAS", "PETROLEUM", "POWER", "RESOURCES", "COAL"],
        "Industriels": ["INDUSTRIES", "MANUFACTURING", "LOGISTICS", "AEROSPACE", "DEFENSE", "MACHINERY"]
    }
    try:
        for url in [
            "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
            "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
        ]:
            with urllib.request.urlopen(url) as response:
                for line in response.read().decode('utf-8').split('\n'):
                    parts = line.split('|')
                    if len(parts) > 1 and parts[0] not in ["Symbol", "ACT Symbol", "File Creation Time", ""]:
                        sym = parts[0].strip()
                        name = parts[1].strip().upper()
                        if "$" not in sym and "." not in sym:
                            secteurs_us["Tous les US (Global)"].append(sym)
                            for sec, mots in mots_cles.items():
                                if any(m in name for m in mots):
                                    secteurs_us[f"{sec} - US (Dynamique)"].append(sym)
                                    break
    except Exception as e:
        st.error(f"Erreur chargement US : {e}")

    for k in secteurs_us:
        secteurs_us[k] = list(set(secteurs_us[k]))
    return secteurs_us

# ==============================================================================
# 2. CANADA GLOBAL - TSX + TSX VENTURE
# ==============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def charger_marche_canada_global():
    """Charge les symboles TSX et TSX Venture depuis symbol-list.io.
    Lève une erreur détaillée si le format ne correspond pas."""

    url = "https://symbol-list.io/data/daily-symbol-list.json"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Accept": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            donnees = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as e:
        raise RuntimeError(f"Téléchargement impossible depuis {url} : {e}")

    # Accepte une liste directe ou un objet qui contient la liste
    if isinstance(donnees, list):
        lignes = donnees
    elif isinstance(donnees, dict):
        lignes = next(
            (donnees[k] for k in ("data", "symbols", "items", "results")
             if isinstance(donnees.get(k), list)),
            []
        )
    else:
        lignes = []
    lignes = [ligne for ligne in lignes if isinstance(ligne, dict)]

    if not lignes:
        cles = list(donnees.keys())[:15] if isinstance(donnees, dict) else "-"
        raise RuntimeError(
            f"Format inattendu (type : {type(donnees).__name__}, clés : {cles})"
        )

    tsx, venture = set(), set()
    for ligne in lignes:
        ex = str(ligne.get("exchange") or ligne.get("exchange_short_name") or "").upper()
        if "VENT" in ex or "TSXV" in ex or "TSX-V" in ex:
            cible, suffixe = venture, ".V"
        elif "TSX" in ex:
            cible, suffixe = tsx, ".TO"
        else:
            continue

        yahoo = str(ligne.get("yahoo_symbol") or "").strip().upper()
        if not yahoo:
            brut = str(ligne.get("symbol") or "").strip().upper()
            if not brut:
                continue
            yahoo = brut.replace(".", "-") + suffixe

        if yahoo in {"", "NAN", "NONE"} or " " in yahoo:
            continue
        cible.add(yahoo)

    if not tsx and not venture:
        cles_ex = list(lignes[0].keys())
        raise RuntimeError(
            f"Aucun titre TSX/TSXV reconnu. Clés du 1er élément : {cles_ex}"
        )

    return {
        "Tous les Canada (Global)": sorted(tsx | venture),
        "TSX - Bourse de Toronto": sorted(tsx),
        "TSX Venture": sorted(venture),
    }

# ==============================================================================
# 3. ETF
# ==================================================================
