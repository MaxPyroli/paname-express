import streamlit as st
import requests
from datetime import datetime, timedelta
import re
import time
import pytz
import os
from PIL import Image
import base64
import json
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import streamlit.components.v1 as components  # <--- AJOUT INDISPENSABLE

# ==========================================
#              CONFIGURATION
# ==========================================
try:
    API_KEY = st.secrets["IDFM_API_KEY"]
except (FileNotFoundError, KeyError):
    API_KEY = "TA_CLE_ICI_SI_BESOIN_EN_LOCAL"

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

try:
    icon_image = Image.open("app_icon.png")
except FileNotFoundError:
    icon_image = "🚆"

# 1. CONFIGURATION
st.set_page_config(
    page_title="Grand Paname",
    page_icon=icon_image,
    layout="centered"
)

# 2. FONCTION POLICE (CORRIGÉE : PROTECTION DES LIGATURES)
def charger_police_locale(file_path, font_name):
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.split('.')[-1].lower()
        format_str = "opentype" if ext == "otf" else "truetype"
        css = f"""
            <style>
            /* 1. Chargement de la police */
            @font-face {{
                font-family: '{font_name}';
                src: url('data:font/{ext};base64,{b64}') format('{format_str}');
            }}
            
            /* 2. Application globale sur le corps */
            html, body, [class*="css"] {{
                font-family: '{font_name}', sans-serif;
            }}
            
            /* 3. Application sur les balises de TEXTE (On évite 'span' et 'i' ici) */
            h1, h2, h3, h4, h5, h6, p, a, li, button, input, label, textarea, div, td, th {{
                font-family: '{font_name}', sans-serif !important;
            }}
            
            /* 4. On force la police sur vos classes perso (au cas où elles utilisent des spans) */
            .station-title, .rail-dest, .bus-dest, .version-badge, .last-dep-label {{
                font-family: '{font_name}', sans-serif !important;
            }}
            
            /* 5. Cible les zones de texte Streamlit */
            .stMarkdown, .stButton, .stTextInput, .stSelectbox, .stExpander {{
                font-family: '{font_name}', sans-serif !important;
            }}
            
            /* 6. FIX NUCLÉAIRE POUR LES ICÔNES DU MENU */
            /* On force le retour à la police d'icônes pour les boutons de la sidebar */
            button[data-testid="stSidebarCollapsedControl"] *,
            button[data-testid="stSidebarExpandedControl"] * {{
                font-family: "Material Symbols Rounded", sans-serif !important;
                font-weight: normal !important;
                font-style: normal !important;
                letter-spacing: normal !important;
                text-transform: none !important;
                white-space: nowrap !important;
                direction: ltr !important;
            }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        pass
charger_police_locale("GrandParis.otf", "Grand Paris")

# ==========================================
#                  STYLE CSS
# ==========================================
st.markdown("""
<style>
    /* --- CSS NINJA : SUPPRESSIONS VISUELLES --- */
    
    /* 1. Cache l'instruction "Press Enter to submit form" */
    div[data-testid="InputInstructions"] { display: none !important; }
    
    /* 2. Cache les liens d'ancrage (le petit maillon à côté des titres) */
    [data-testid="stHeaderAction"] { display: none !important; }
    
    /* 3. Force l'opacité à 100% (Anti-grisement) */
    div[data-testid="stFragment"] { opacity: 1 !important; transform: none !important; transition: none !important; filter: none !important; }
    div.element-container { opacity: 1 !important; filter: none !important; }
    
    /* 4. Cache les éléments de chargement par défaut */
    div[data-testid="stSpinner"] { display: none !important; }
    .stApp > header { visibility: hidden !important; }
    /* ----------------------------------------- */
    /* NOUVEAU : Animation Clignotement (Blink) */
    @keyframes blink-live {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    .live-icon {
        display: inline-block;
        /* Animation plus rapide (1s) pour un vrai clignotement */
        animation: blink-live 1.5s infinite step-start; 
        /* step-start fait un clignotement net (on/off). 
           Si tu préfères une transition douce, retire 'step-start' et laisse juste 'infinite' */
        animation: blink-live 1s infinite; 
        margin: 0 4px;
        vertical-align: middle;
        font-size: 0.6em;
    }

    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1s linear infinite; font-weight: bold; }
    
    @keyframes yellow-pulse {
        0% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); }
        50% { border-color: #fff; box-shadow: 0 0 15px rgba(241, 196, 15, 0.6); }
        100% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); }
    }
    
    @keyframes float { 
        0% { transform: translateY(0px); } 
        50% { transform: translateY(-6px); } 
        100% { transform: translateY(0px); } 
    } 
    .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }

    /* Header en Flexbox pour un alignement parfait (Mobile & Desktop) */
    h1 {
        display: flex !important;
        align-items: center !important;
        flex-wrap: wrap !important; /* Permet au badge de passer à la ligne proprement */
        gap: 15px !important;       /* Espace entre le titre et le badge */
        margin-bottom: 0.5rem !important;
    }

    .custom-loader {
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-left-color: #3498db; border-radius: 50%; width: 14px; height: 14px;
        animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    .text-red { color: #e74c3c; font-weight: bold; }
    .text-orange { color: #f39c12; font-weight: bold; }
    .text-green { color: #2ecc71; font-weight: bold; }
    .text-blue { color: #3498db; font-weight: bold; }
    
    .line-badge {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-weight: 900; color: white; text-align: center; min-width: 35px;
        margin-right: 12px; font-size: 16px; text-shadow: 0px 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        flex-shrink: 0; /* Empêche le badge d'être écrasé */
    }
    
    .footer-container { display: flex; align-items: center; margin-bottom: 8px; }
    .footer-icon { 
        display: inline-flex !important; /* Force l'icône et le texte à rester côte à côte */
        align-items: center !important;  /* Aligne verticalement l'icône et le texte */
        flex-shrink: 0 !important;       /* Interdit au bloc de rétrécir ou de se casser */
        margin-right: 10px; 
        font-size: 14px; 
        color: var(--text-color); 
        opacity: 0.7; 
        white-space: nowrap !important;  /* Sécurité supplémentaire anti-retour à la ligne */
    }
    .footer-badge { font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important; }

    .time-sep { color: #888; margin: 0 8px; font-weight: lighter; }
    
    .section-header {
        /* AJOUTS FLEXBOX POUR CENTRAGE */
        display: flex !important;
        align-items: center !important; /* Centre verticalement */
        
        /* Tes styles existants conservés */
        margin-top: 25px; 
        margin-bottom: 15px; 
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5); 
        font-size: 20px; 
        font-weight: bold; 
        color: var(--text-color); 
        letter-spacing: 1px;
    }
    
    .station-title {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .rer-direction {
        margin-top: 12px; font-size: 13px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 1px solid #444; padding-bottom: 4px; margin-bottom: 0px; 
    }
    
    /* DESIGN DES CARTES (COULEUR FIXE) */
    .bus-card, .rail-card {
        background-color: #041b3b !important; /* Le bleu demandé */
        padding: 12px; 
        margin-bottom: 15px; 
        border-radius: 8px; 
        
        /* La bordure gauche reste gérée par le code Python (couleur de la ligne) */
        border-left-width: 5px !important; 
        border-left-style: solid !important;
        
        color: #ffffff !important; /* Texte blanc forcé */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* Destinations en gris très clair pour la lisibilité sur fond bleu */
    .bus-dest, .rail-dest { 
        color: #e0e0e0 !important; 
        font-size: 15px; 
        font-weight: 500; 
        overflow: hidden;
        text-overflow: ellipsis; 
        white-space: nowrap; 
        margin-right: 10px; 
        flex: 1;
    }
    
    /* Séparateurs discrets */
    .bus-row, .rail-row {
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding-top: 8px; 
        padding-bottom: 2px; 
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important; 
    }
    
    /* Les heures restent bien blanches */
    .bus-row > span:last-child, .rail-row > span:last-child {
        color: #ffffff !important;
    }

    /* --- CORRECTION MOBILE --- */
    .bus-row, .rail-row {
        display: flex; 
        justify-content: space-between; 
        align-items: center; /* Aligne verticalement si les hauteurs diffèrent */
        padding-top: 8px; padding-bottom: 2px; border-top: 1px solid #333; 
    }
    
    .rer-direction + .rail-row { border-top: none; padding-top: 8px; }
    
    .bus-dest, .rail-dest { 
        color: #ccc; 
        font-size: 15px; 
        font-weight: 500; 
        overflow: hidden;
        text-overflow: ellipsis; /* Ajoute "..." si trop long */
        white-space: nowrap; /* Empêche le retour à la ligne du nom */
        margin-right: 10px; /* Espace min avec l'heure */
        flex: 1; /* Prend toute la place dispo */
    }

    /* Le bloc des horaires ne doit JAMAIS passer à la ligne */
    .bus-row > span:last-child, .rail-row > span:last-child {
        white-space: nowrap;
        flex-shrink: 0; /* Empêche d'être écrasé */
        text-align: right;
    }
    
    .service-box { 
        text-align: left; padding: 10px 12px; color: #888; font-style: italic; font-size: 0.95em;
        background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-top: 5px; margin-bottom: 5px; border-left: 3px solid #444;
    }
    .service-end { color: #999; font-style: italic; font-size: 0.9em; }

    /* --- GESTION DERNIER DÉPART --- */
    .last-dep-box {
        border: 2px solid #f1c40f; border-radius: 6px; padding: 8px 10px; margin-top: 8px; margin-bottom: 8px;
        background-color: rgba(241, 196, 15, 0.1); animation: yellow-pulse 2s infinite;
    }
    .last-dep-label { display: block; font-size: 0.75em; text-transform: uppercase; font-weight: bold; color: #f1c40f; margin-bottom: 4px; letter-spacing: 1px; }
    .last-dep-box .rail-row, .last-dep-box .bus-row { border-top: none !important; padding-top: 0 !important; margin-top: 0 !important; }

    /* Petit encadré pour départ entre 10 et 30 min */
    .last-dep-small-frame {
        border: 1px solid #f1c40f;
        border-radius: 4px;
        padding: 1px 5px;
        color: #f1c40f;
        font-weight: bold;
    }
    
    /* Juste le texte pour départ > 30 min */
    .last-dep-text-only {
        color: #f1c40f;
        font-weight: bold;
    }

    .version-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* Nouveau dégradé plus moderne */
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.4em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-left: 0 !important; /* Le Flexbox gère l'espace */
    }
    
    .verified-badge {
        color: #3498db;
        font-size: 0.8em;
        margin-left: 5px;
    }
    /* CONFIGURATION TITRE (Taille & Alignement) */
    h1 {
        font-size: 3.5rem !important; /* Taille PC augmentée */
        display: flex !important;     /* Active l'alignement flexible */
        align-items: center !important;
        flex-wrap: wrap !important;   /* Permet au badge de passer à la ligne proprement */
        gap: 15px !important;         /* Espace entre le logo, le titre et le badge */
        line-height: 1.1 !important;
    }

    /* --- MEDIA QUERY MOBILE (MAX 480px) --- */
    @media (max-width: 480px) {
        
        /* 1. SUPPRESSION DE LA MARGE HAUTE (ESPACE BLANC) */
        .block-container {
            padding-top: 1rem !important; /* On réduit drastiquement l'espace (par défaut c'est ~6rem) */
        }

        /* Ajustements de taille de police globaux (Déjà présents) */
        .station-title, .station-title-pole { font-size: 20px; }
        h1 { font-size: 35px !important; gap: 10px !important; margin-top: 0 !important; }
        .version-badge { font-size: 0.45em !important; }

        /* ... (Le reste de ton code mobile pour les Bus/RER reste en dessous) ... */

        /* === CAS 1 : BUS / TRAM / MÉTRO (Affichage "Aéré" sur 2 lignes) === */
        .bus-row {
            flex-direction: column !important; /* Empile Destination et Heure */
            align-items: flex-start !important; /* Aligne tout à gauche */
            padding-top: 10px !important;
            padding-bottom: 10px !important;
        }
        
        .bus-dest {
            width: 100% !important;
            white-space: normal !important; /* Autorise le texte à passer à la ligne */
            margin-bottom: 6px !important;  /* Espace entre Nom et Heure */
            font-size: 16px !important;
            margin-right: 0 !important;
        }

        /* Le conteneur des heures pour les Bus passe en dessous */
        .bus-row > span:last-child {
            width: 100% !important;
            text-align: left !important; /* On aligne les heures à gauche pour la lecture */
            font-size: 0.9em !important;
            color: #ccc !important;
        }

        /* === CAS 2 : RER / TRAIN (On garde l'affichage "Compact" sur 1 ligne) === */
        /* On ne touche PAS à .rail-row ici pour qu'il garde le comportement par défaut (Row) */
        .rail-row {
            padding-top: 8px !important; 
            padding-bottom: 8px !important;
        }
        
        .rail-dest {
            max-width: 65% !important; /* Sécurité pour ne pas écraser l'heure */
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* === RESTAURATION DES SÉPARATEURS === */
        /* On s'assure qu'ils sont bien visibles */
        .time-sep { 
            display: inline-block !important; 
            margin: 0 5px !important;
            color: #666 !important;
            font-weight: lighter !important;
        }
    }
    
    /* Alignement vertical du bouton favori */
    div[data-testid="column"] {
        display: flex;
        align-items: center; 
    }
    div[data-testid="column"] button {
        border: none;
        background: transparent;
        font-size: 1.5rem;
        padding: 0;
    }
    div[data-testid="column"] button:hover {
        color: #f1c40f; 
        border: none;
        background: transparent;
    }
    /* --- AJOUT : BOX BUS REMPLACEMENT (Rouge & Pointillés) --- */
    .replacement-box {
        border: 2px dashed #e74c3c; 
        border-radius: 6px; 
        padding: 8px 10px; 
        margin-top: 8px; 
        margin-bottom: 8px;
        background-color: rgba(231, 76, 60, 0.1); 
    }
    .replacement-label { 
        display: block; 
        font-size: 0.75em; 
        text-transform: uppercase; 
        font-weight: bold; 
        color: #e74c3c; 
        margin-bottom: 4px; 
        letter-spacing: 1px; 
    }
    /* Annule les bordures internes */
    .replacement-box .rail-row, .replacement-box .bus-row { 
        border-top: none !important; 
        padding-top: 0 !important; 
        margin-top: 0 !important; 
    }
    /* --- CSS ICONES : VERSION BINAIRE FORCÉE --- */
    
    img.mode-icon {
        height: 1.5em !important;
        width: auto !important;
        margin-right: 10px !important;
        vertical-align: middle !important;
        transition: filter 0.3s ease;
    }

    /* ---------------------------------------------------------
       1. FORÇAGE MODE CLAIR (On veut du NOIR)
       --------------------------------------------------------- */
    /* Cas A : L'utilisateur force "Light" dans Streamlit */
    [data-theme="light"] img.mode-icon {
        filter: brightness(0) !important; 
    }
    
    /* Cas B : Le système est Light (et l'utilisateur n'a rien forcé) */
    @media (prefers-color-scheme: light) {
        img.mode-icon {
            filter: brightness(0) !important;
        }
    }

    /* ---------------------------------------------------------
       2. FORÇAGE MODE SOMBRE (On veut du BLANC)
       --------------------------------------------------------- */
    /* Cas A : L'utilisateur force "Dark" dans Streamlit */
    [data-theme="dark"] img.mode-icon {
        /* On écrase le noir pour faire : Noir -> Inversé -> BLANC PUR */
        filter: brightness(0) invert(1) !important; 
    }

    /* Cas B : Le système est Dark (et l'utilisateur n'a rien forcé) */
    @media (prefers-color-scheme: dark) {
        img.mode-icon {
            filter: brightness(0) invert(1) !important;
        }
    }
    /* --- BOUTON FAVORI LARGE ET PROPRE --- */
    .fav-btn-container { width: 100%; }
    .fav-btn-container button {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #f1c40f !important;
        font-size: 16px !important; /* Texte un peu plus fin */
        font-weight: 600 !important;
        height: 45px !important;
        border-radius: 8px !important;
        transition: background-color 0.2s, transform 0.1s !important;
    }
    .fav-btn-container button:hover {
        background-color: rgba(241, 196, 15, 0.15) !important;
        border-color: #f1c40f !important;
    }
    /* Force l'alignement vertical */
    div[data-testid="column"] { align-items: center; }

    /* On force l'alignement à droite */
    div[data-testid="column"]:has(.fav-btn-container) {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }
    /* --- 1. NETTOYAGE VISUEL --- */
    div[data-testid="InputInstructions"], [data-testid="stHeaderAction"], .stApp > header { 
        display: none !important; 
    }

    /* ============================================================ */
    /* SIDEBAR : VERSION ULTRA-COMPACTE (PC & MOBILE)              */
    /* ============================================================ */

    /* 1. LE CONTENEUR (La ligne complète) */
    /* On force l'alignement horizontal et on INTERDIT le passage à la ligne */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:not(:has([data-testid="stVerticalBlockBorderWrapper"])) {
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* C'est ça qui force la même ligne sur mobile */
        align-items: center !important;
        gap: 5px !important;
        width: 100% !important;
    }

    /* 2. COLONNE GAUCHE (Nom de la gare) - ÉLASTIQUE */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:not(:has([data-testid="stVerticalBlockBorderWrapper"])) > [data-testid="column"]:first-child {
        flex: 1 1 auto !important; /* Prend tout l'espace disponible */
        width: auto !important;
        min-width: 0px !important; /* INDISPENSABLE : permet au texte d'être coupé (...) sur mobile */
        overflow: hidden !important;
    }

    /* 3. COLONNE DROITE (Poubelle) - VERROUILLÉE */
    /* On fixe une taille rigide en pixels pour qu'il soit carré partout */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:not(:has([data-testid="stVerticalBlockBorderWrapper"])) > [data-testid="column"]:last-child {
        flex: 0 0 42px !important;    /* Ne grandit pas, ne rétrécit pas, fait 42px */
        width: 42px !important;       /* Largeur forcée */
        min-width: 42px !important;   /* Largeur min */
        max-width: 42px !important;   /* Largeur max (Empêche l'étirement PC) */
    }

    /* 4. DESIGN DU BOUTON GARE (Gauche) */
    button[key^="btn_fav_"] {
        width: 100% !important;
        height: 42px !important;      /* Hauteur standardisée */
        text-align: left !important;
        padding-left: 10px !important;
    }
    
    /* Gestion du texte trop long (Trois petits points...) */
    button[key^="btn_fav_"] p, button[key^="btn_fav_"] div {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
        width: 100% !important;
    }

    /* 5. DESIGN DU BOUTON POUBELLE (Droite) */
    button[key^="del_fav_"] {
        width: 100% !important;
        height: 42px !important;      /* Carré parfait (42x42 avec la colonne) */
        padding: 0 !important;
        margin: 0 !important;
        border: 1px solid rgba(231, 76, 60, 0.3) !important;
        background: rgba(231, 76, 60, 0.1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
#              LOGIQUE MÉTIER
# ==========================================

GEOGRAPHIE_RER = {
    "A": {
        "labels": ("⇦ OUEST (Cergy / Poissy / St-Germain)", "⇨ EST (Marne-la-Vallée / Boissy)"),
        "mots_1": ["CERGY", "POISSY", "GERMAIN", "RUEIL", "DEFENSE", "DÉFENSE", "NANTERRE", "VESINET", "MAISONS", "LAFFITTE", "PECQ", "ACHERES", "GRANDE ARCHE", "SARTROUVILLE"],
        "term_1": ["HAUT", "POISSY", "GERMAIN"],
        "mots_2": ["MARNE", "BOISSY", "TORCY", "NATION", "VINCENNES", "FONTENAY", "NOISY", "JOINVILLE", "VALLEE", "CHESSY", "DISNEY"],
        "term_2": ["CHESSY", "BOISSY"]
    },
    "B": {
        "labels": ("⇩ SUD (St-Rémy / Robinson)", "⇧ NORD (Roissy / Mitry)"),
        "mots_1": ["REMY", "RÉMY", "ROBINSON", "LAPLACE", "DENFERT", "CITE", "MASSY", "ORSAY", "BOURG", "CROIX", "GENTILLY", "ARCUEIL", "BAGNEUX"],
        "term_1": ["REMY", "RÉMY", "ROBINSON"],
        "mots_2": ["GAULLE", "MITRY", "NORD", "AULNAY", "BOURGET", "LA PLAINE", "CLAYE", "AÉROPORT"],
        "term_2": ["GAULLE", "MITRY"]
    },
    "C": {
        "labels": ("⇦ OUEST (Versailles / Pontoise)", "⇨ SUD/EST (Massy / Dourdan / Étampes)"),
        "mots_1": ["INVALIDES", "AUSTERLITZ", "VERSAILLES", "QUENTIN", "PONTOISE", "CHAMP", "EIFFEL", "CHAVILLE", "ERMONT", "JAVEL", "ALMA", "VELIZY", "BEAUCHAMP", "MONTIGNY", "ARGENTEUIL"],
        "term_1": ["VERSAILLES", "QUENTIN", "PONTOISE", "AUSTERLITZ"],
        "mots_2": ["MASSY", "DOURDAN", "ETAMPES", "ÉTAMPES", "MARTIN", "JUVISY", "BIBLIOTHEQUE", "ORLY", "RUNGIS", "BRETIGNY", "BRÉTIGNY", "CHOISY", "IVRY", "ATHIS", "SAVIGNY"],
        "term_2": ["DOURDAN", "ETAMPES", "ÉTAMPES", "MASSY", "BRÉTIGNY"]
    },
    "D": {
        "labels": ("⇩ SUD (Melun / Corbeil)", "⇧ NORD (Creil)"),
        "mots_1": ["MELUN", "CORBEIL", "MALESHERBES", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"],
        "term_1": ["MELUN", "CORBEIL", "MALESHERBES"],
        "mots_2": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS", "GARE DE LYON", "PARIS", "CHATELET", "NORD"],
        "term_2": ["CREIL", "ORRY", "GOUSSAINVILLE"]
    },
    "E": {
        "labels": ("⇦ OUEST (Nanterre)", "⇨ EST (Chelles / Tournan)"),
        "mots_1": ["HAUSSMANN", "LAZARE", "MAGENTA", "NANTERRE", "DEFENSE", "DÉFENSE", "ROSA"],
        "term_1": ["NANTERRE", "HAUSSMANN"],
        "mots_2": ["CHELLES", "TOURNAN", "VILLIERS", "GAGNY", "EMERAINVILLE", "ROISSY", "NOISY", "BONDY"],
        "term_2": ["CHELLES", "TOURNAN"]
    },
    # --- TRANSILIENS ---
    "H": {
        "labels": ("⇧ NORD (Pontoise / Persan / Creil)", "⇩ PARIS NORD"),
        "mots_1": ["PONTOISE", "PERSAN", "BEAUMONT", "LUZARCHES", "CREIL", "MONTSOULT", "VALMONDOIS", "SARROUS", "SAINT-LEU", "SARCELLES", "BRICE"],
        "term_1": ["PONTOISE", "PERSAN", "LUZARCHES", "CREIL"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "J": {
        "labels": ("⇦ OUEST (Mantes / Gisors / Ermont)", "⇨ PARIS ST-LAZARE"),
        "mots_1": ["MANTES", "JOLIE", "GISORS", "ERMONT", "VERNON", "PONTOISE", "CONFLANS", "BOISSY", "MEULAN", "MUREAUX", "CORMEILLES", "ARGENTEUIL", "ISSOU"],
        "term_1": ["MANTES", "GISORS", "ERMONT", "VERNON"],
        "mots_2": ["PARIS", "LAZARE"],
        "term_2": ["PARIS", "LAZARE"]
    },
    "K": {
        "labels": ("⇧ NORD (Crépy-en-Valois)", "⇩ PARIS NORD"),
        "mots_1": ["CREPY", "CRÉPY", "DAMMARTIN"],
        "term_1": ["CREPY", "CRÉPY"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "L": {
        "labels": ("⇦ OUEST (Versailles / St-Nom / Cergy)", "⇨ PARIS ST-LAZARE"),
        "mots_1": ["VERSAILLES", "NOM", "BRETÈCHE", "CERGY", "NANTERRE", "MAISONS", "CLOUD", "SARTROUVILLE"],
        "term_1": ["VERSAILLES", "NOM", "HAUT"],       
        "mots_2": ["PARIS", "LAZARE"],
        "term_2": ["PARIS", "LAZARE"]
    },
    "N": {
        "labels": ("⇦ OUEST (Rambouillet / Dreux / Mantes)", "⇨ PARIS MONTPARNASSE"),
        "mots_1": ["RAMBOUILLET", "DREUX", "MANTES", "JOLIE", "PLAISIR", "SEVRES", "SÈVRES"],
        "term_1": ["RAMBOUILLET", "DREUX", "MANTES"],
        "mots_2": ["PARIS", "MONTPARNASSE"],
        "term_2": ["PARIS", "MONTPARNASSE"]
    },
    "P": {
        "labels": ("⇨ EST (Meaux / Provins / Coulommiers)", "⇦ PARIS EST"),
        "mots_1": ["MEAUX", "CHATEAU", "CHÂTEAU", "THIERRY", "FERTE", "FERTÉ", "MILON", "PROVINS", "COULOMMIERS"],
        "term_1": ["MEAUX", "CHÂTEAU", "PROVINS", "COULOMMIERS", "FERTÉ"],
        "mots_2": ["PARIS", "EST"],
        "term_2": ["PARIS", "EST"]
    },
    "R": {
        "labels": ("⇩ SUD (Montereau / Montargis)", "⇧ PARIS GARE DE LYON"),
        "mots_1": ["MONTEREAU", "MONTARGIS", "MELUN"],
        "term_1": ["MONTEREAU", "MONTARGIS"],
        "mots_2": ["PARIS", "LYON", "BERCY"],
        "term_2": ["PARIS", "LYON"]
    },
    "U": {
        "labels": ("⇩ SUD (La Verrière)", "⇧ NORD (La Défense)"),
        "mots_1": ["VERRIERE", "VERRIÈRE", "TRAPPES"],
        "term_1": ["VERRIERE", "VERRIÈRE"],
        "mots_2": ["DEFENSE", "DÉFENSE"],
        "term_2": ["DEFENSE", "DÉFENSE"]
    },
    "V": {
        "labels": ("⇦ OUEST (Versailles-Chantiers)", "⇨ EST (Massy-Palaiseau)"),
        "mots_1": ["VERSAILLES", "CHANTIERS"],
        "term_1": ["VERSAILLES"],
        "mots_2": ["MASSY", "PALAISEAU"],
        "term_2": ["MASSY"]
    }
}

# ==========================================
#          FONCTIONS UTILITAIRES
# ==========================================

# 1. D'ABORD : La fonction qui lit le fichier (Indispensable qu'elle soit ici)
def get_img_as_base64(file_path):
    # Sécurité : si le fichier n'existe pas, on renvoie None
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None
# ==========================================
#          EASTER EGG (POP-UP)
# ==========================================
@st.dialog("🚨 ALERTE GÉNÉRALE 🚨")
def afficher_popup_feur(mot_declencheur):
    # 1. Les Ballons (S'affichent sur toute l'app)
    st.balloons()
    
    # 2. Le Titre dans la boite de dialogue
    if mot_declencheur == "quoi":
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 20px;'>FEUR ! 💇‍♂️</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 20px;'>ROUGE ! 🚤</h1>", unsafe_allow_html=True)
    
    # 3. La Vidéo (Centrée)
    # Tu peux remplacer l'URL par un fichier local "img/feur.mp4" si tu l'as
    st.video("autre/feur.mp4", autoplay=True)
    
    st.markdown("*Cliquez en dehors de la fenêtre pour fermer.*")

# ==========================================
#        GESTION DES LOGOS (RETOUR IMG)
# ==========================================
def generer_icones_html():
    mapping_files = {
        "RER":   "img/rer.svg",
        "TRAIN": "img/train.svg",
        "METRO": "img/metro.svg",
        "TRAM":  "img/tram.svg",
        "CABLE": "img/cable.svg",
        "BUS":   "img/bus.svg",
        "AUTRE": "img/autre.svg"
    }
    
    labels = {
        "RER": "RER", "TRAIN": "TRAIN", "METRO": "MÉTRO", 
        "TRAM": "TRAMWAY", "CABLE": "CÂBLE", "BUS": "BUS", "AUTRE": "AUTRE"
    }
    
    # Emoji de secours si le fichier n'est pas trouvé
    fallbacks = {
        "RER": "🚆", "TRAIN": "🚆", "METRO": "🚇", 
        "TRAM": "🚋", "CABLE": "🚠", "BUS": "🚌", "AUTRE": "🌙"
    }
    
    resultat = {}
    
    for mode, label in labels.items():
        filepath = mapping_files.get(mode)
        b64_data = None
        
        # On tente de lire le fichier
        if filepath:
            b64_data = get_img_as_base64(filepath)
            
        if b64_data:
            # RETOUR À LA BALISE IMG CLASSIQUE
            # C'est la seule méthode qui garantit l'affichage de l'image
            html = f'<img src="data:image/svg+xml;base64,{b64_data}" class="mode-icon">{label}'
            resultat[mode] = html
        else:
            emoji = fallbacks.get(mode, "❓")
            resultat[mode] = f"{emoji} {label}"
            
    return resultat

# 3. ENFIN : On lance la génération
ICONES_TITRE = generer_icones_html()

HIERARCHIE = {"RER": 1, "TRAIN": 2, "METRO": 3, "CABLE": 4, "TRAM": 5, "BUS": 6, "AUTRE": 99}

def demander_api(suffixe):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/{suffixe}", headers=headers)
        return r.json()
    except: return None

def trouver_gare_proche(lat, lon):
    """Trouve la gare la plus proche via Navitia"""
    try:
        # Navitia attend "lon;lat"
        data = demander_api(f"coord/{lon};{lat}/places?type[]=stop_area&distance=2000")
        if data and 'places' in data and len(data['places']) > 0:
            place = data['places'][0]
            if 'stop_area' in place:
                return {
                    'id': place['stop_area']['id'],
                    'name': place['name'],
                    'city': place.get('administrative_regions', [{}])[0].get('name', '')
                }
    except:
        return None
    return None
    
@st.cache_data(ttl=3600)
def demander_lignes_arret(stop_id):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/stop_areas/{stop_id}/lines", headers=headers)
        return r.json()
    except: return None

def normaliser_mode(mode_brut):
    if not mode_brut: return "AUTRE"
    m = mode_brut.upper()
    if "FUNI" in m or "CABLE" in m or "TÉLÉPHÉRIQUE" in m: return "CABLE"
    if "RER" in m or "RAPIDTRANSIT" in m: return "RER"
    if "TRAIN" in m or "RAIL" in m or "SNCF" in m or "EXPRESS" in m or "TER" in m: return "TRAIN"
    if "METRO" in m or "MÉTRO" in m: return "METRO"
    if "TRAM" in m: return "TRAM"
    if "BUS" in m: return "BUS"
    return "AUTRE"

def clean_code_line(code):
    return str(code).strip().upper()

def format_html_time(heure_str, data_freshness):
    paris_tz = pytz.timezone('Europe/Paris')
    obj_naive = datetime.strptime(heure_str, '%Y%m%dT%H%M%S')
    obj = paris_tz.localize(obj_naive)
    now = datetime.now(paris_tz)
    delta = int((obj - now).total_seconds() / 60)
    
    if data_freshness == 'base_schedule':
        return (2000, f"<span class='text-blue'>~{obj.strftime('%H:%M')}</span>")
    
    if delta > 120: return (3000, "<span class='service-end'>Service terminé</span>")
    if delta <= 0: return (0, "<span class='text-red'>À quai</span>")
    if delta == 1: return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5: return (delta, f"<span class='text-orange'>{delta} min</span>")
    return (delta, f"<span class='text-green'>{delta} min</span>")

def get_all_changelogs():
    log_dir = "changelogs"
    all_notes = []
    if not os.path.exists(log_dir): return ["*Aucune note de version trouvée.*"]
    files = [f for f in os.listdir(log_dir) if f.endswith(".md")]
    def version_key(filename):
        try:
            clean = filename.lower().replace('v', '').replace('.md', '')
            return [int(part) for part in clean.split('.') if part.isdigit()]
        except: return [0]
    files.sort(key=version_key, reverse=True)
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f: all_notes.append(f.read())
        except Exception as e: all_notes.append(f"Erreur de lecture de {filename}: {e}")
    return all_notes if all_notes else ["*Aucune note de version trouvée.*"]

# ==========================================
#              INTERFACE GLOBALE
# ==========================================
# --- RECUPERATION DE L'ICONE DU TITRE ---
img_app_b64 = get_img_as_base64("app_icon.png")
if img_app_b64:
    # On crée la balise image si le fichier existe
    icone_html = f'<img src="data:image/png;base64,{img_app_b64}" style="height: 1.5em; vertical-align: bottom; margin-right: 10px;">'
else:
    # Sinon on met l'émoji par défaut
    icone_html = "🚆"

# Titre avec Logo personnalisé + Badge v1.0
st.markdown(f"<h1>{icone_html} Grand Paname <span class='version-badge'>v1.1</span></h1>", unsafe_allow_html=True)

# Sous-titre
st.markdown("##### *Naviguez le Grand Paris, tout simplement.*", unsafe_allow_html=True)
# --- INITIALISATION DES FAVORIS (LocalStorage JS Pur - V4 Instantanée) ---

# 1. On initialise la session si elle n'existe pas
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'favs_loaded' not in st.session_state:
    st.session_state.favs_loaded = False

# 2. Lecture du navigateur (UNE SEULE FOIS au démarrage)
if not st.session_state.favs_loaded:
    # On demande les données au navigateur
    favs_from_browser = streamlit_js_eval(js_expressions="localStorage.getItem('gp_favs')", key="get_favs_init")
    
    if favs_from_browser:
        try:
            # Si on reçoit des données, on remplit la session et on verrouille
            st.session_state.favorites = json.loads(favs_from_browser)
            st.session_state.favs_loaded = True
            st.rerun() # On recharge pour afficher la sidebar remplie
        except:
            pass
    # Si le composant a fini de charger mais renvoie rien (premier lancement), on verrouille aussi
    # Note : streamlit_js_eval renvoie souvent None au tout premier tick, c'est normal.

def toggle_favorite(stop_id, stop_name):
    """Ajoute/Retire : Met à jour l'affichage IMMÉDIATEMENT et sauvegarde en fond."""
    clean_name = stop_name.split('(')[0].strip()
    exists = False
    
    # 1. MISE À JOUR DE LA SESSION
    for i, fav in enumerate(st.session_state.favorites):
        if fav['id'] == stop_id:
            st.session_state.favorites.pop(i)
            exists = True
            st.toast(f"❌ {clean_name} retiré", icon="🗑️")
            break
    if not exists:
        st.session_state.favorites.append({'id': stop_id, 'name': clean_name, 'full_name': stop_name})
        st.toast(f"⭐ {clean_name} ajouté !", icon="✅")
    
    # 2. SAUVEGARDE
    # CORRECTION CRITIQUE : On a retiré 'with st.sidebar' qui faisait planter le Fragment.
    # Le CSS ajouté plus haut se charge de rendre ce composant invisible.
    st.session_state.favs_loaded = True 
    json_data = json.dumps(st.session_state.favorites).replace("'", "\\'")
    
    streamlit_js_eval(js_expressions=f"localStorage.setItem('gp_favs', '{json_data}')", key=f"save_{time.time()}")
    
    time.sleep(0.1)
with st.sidebar:
    st.caption("v1.1 - Abondance 🧀")
    
    # --- SECTION FAVORIS ---
    st.header("⭐ Mes Favoris")
    
    # Fonction pour charger un favori (inchangée)
    def load_fav(fav_id, fav_name):
        st.session_state.selected_stop = fav_id
        st.session_state.selected_name = fav_name
        st.session_state.search_results = {}
        st.session_state.last_query = ""
        st.session_state.search_key += 1

    # --- LOGIQUE D'AFFICHAGE CORRIGÉE ---
    if not st.session_state.favorites:
        # CAS 1 : PAS DE FAVORIS
        st.info("Ajoutez des gares en cliquant sur l'étoile à côté de leur nom !")
        
    else:
        # CAS 2 : IL Y A DES FAVORIS (On affiche la liste ET le bouton supprimer)
        
        # --- A. LISTE DES FAVORIS ---
        for fav in st.session_state.favorites[:]:
            col_nav, col_del = st.columns([0.85, 0.15], gap="small", vertical_alignment="center")
            
            with col_nav:
                if st.button(f"📍 {fav['name']}", key=f"btn_fav_{fav['id']}", use_container_width=True):
                    load_fav(fav['id'], fav['full_name'])
                    st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_fav_{fav['id']}", help="Supprimer", use_container_width=True):
                    st.session_state.favorites = [f for f in st.session_state.favorites if f['id'] != fav['id']]
                    json_data = json.dumps(st.session_state.favorites).replace("'", "\\'")
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('gp_favs', '{json_data}')", 
                        key=f"del_sync_{time.time()}"
                    )
                    st.rerun()

        # --- B. ESPACE ---
        st.write("")
        st.write("") 
        
        # --- C. BOUTON TOUT EFFACER (Uniquement si favoris existants) ---
        if 'confirm_reset' not in st.session_state:
            st.session_state.confirm_reset = False

        if not st.session_state.confirm_reset:
            if st.button("💥 Tout effacer", use_container_width=True, type="primary", key="reset_all_favs_btn"):
                st.session_state.confirm_reset = True
                st.rerun()
        else:
            # LE PANNEAU DE CONFIRMATION
            with st.container(border=True):
                st.warning("Tout supprimer ?")
                
                # Bouton OUI (Rouge)
                if st.button("Oui, tout effacer", use_container_width=True, type="primary", key="confirm_yes"):
                    st.session_state.favorites = []
                    st.session_state.confirm_reset = False
                    streamlit_js_eval(js_expressions="localStorage.removeItem('gp_favs')")
                    st.rerun()
                
                # Bouton NON (Gris)
                if st.button("Non, annuler", use_container_width=True, key="confirm_no"):
                    st.session_state.confirm_reset = False
                    st.rerun()

    st.markdown("---")
    
   # --- SECTION INFOS ---
    st.header("🗄️ Informations")
    st.info("👋 **Bienvenue à bord !**\n\nGrand Paname passe en version 1.0 ! Profitez d'une information voyageur claire et rapide pour vos trajets du quotidien.")
    st.markdown("---")
    with st.expander("📜 Historique des versions"):
        notes_history = get_all_changelogs()
        for i, note in enumerate(notes_history):
            st.markdown(note)
            if i < len(notes_history) - 1: st.divider()
    st.markdown("---")
    st.caption("✨ Réalisé à l'aide de l'IA **Gemini**")
# --- GESTION DE LA RECHERCHE ---
if 'selected_stop' not in st.session_state:
    st.session_state.selected_stop = None
    st.session_state.selected_name = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}
if 'search_key' not in st.session_state:
    st.session_state.search_key = 0
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'search_error' not in st.session_state:
    st.session_state.search_error = None

# --- GESTION DE LA RECHERCHE & GÉOLOCALISATION ---
col_search, col_gps = st.columns([0.75, 0.25], gap="small", vertical_alignment="bottom")

with col_search:
    with st.form("search_form"):
        c_in, c_sub = st.columns([0.7, 0.3], vertical_alignment="bottom")
        with c_in:
            search_query = st.text_input(
                "🔍 Rechercher :", 
                placeholder="Ex: Noisiel...",
                value=st.session_state.last_query, 
                key=f"search_input_{st.session_state.search_key}",
                label_visibility="collapsed"
            )
        with c_sub:
            submitted = st.form_submit_button("Chercher", use_container_width=True)

with col_gps:
    # Bouton direct de la librairie
    loc = get_geolocation(component_key="gps_btn")

# --- LOGIQUE GÉOLOCALISATION ---
if loc and isinstance(loc, dict) and 'coords' in loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    
    # On vérifie si c'est une nouvelle demande pour éviter les boucles
    if 'last_gps_coords' not in st.session_state or st.session_state.last_gps_coords != (lat, lon):
        st.session_state.last_gps_coords = (lat, lon)
        
        with st.spinner("📍 Localisation..."):
            gare = trouver_gare_proche(lat, lon)
            
            if gare:
                st.session_state.selected_stop = gare['id']
                full_name = f"{gare['name']} ({gare['city']})" if gare['city'] else gare['name']
                st.session_state.selected_name = full_name
                st.toast(f"Trouvé : {gare['name']}", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Aucune gare trouvée à moins de 2km.")

if st.session_state.search_error:
    st.warning(st.session_state.search_error)

if submitted and search_query:
    # --- 1. FERMETURE DU CLAVIER MOBILE (Le retour !) ---
    # Cette commande JS enlève le focus du champ texte, ce qui ferme le clavier Android/iOS
    streamlit_js_eval(js_expressions="document.activeElement.blur()", key=f"blur_{time.time()}")

    # --- SUITE DU CODE EXISTANT ---
    st.session_state.last_query = search_query 
    st.session_state.search_error = None

    # --- 🥚 DEBUT EASTER EGG : QUOI-FEUR (MODE DIALOGUE) 🥚 ---
    trigger_word = re.sub(r'[^\w\s]', '', search_query.lower().strip())
    # ...
    
    if trigger_word in ["quoi", "feur", "coiffure"]:
        # On appelle la fonction décorée avec @st.dialog
        afficher_popup_feur(trigger_word)
        
        # On arrête le script ici pour ne pas lancer la recherche API derrière
        st.stop()
    # --- FIN EASTER EGG ---

    with st.spinner("Recherche des arrêts..."):
        # ... (La suite de ton code habituel) ...
        # ... (La suite de ton code habituel reste ici) ...
        data = demander_api(f"places?q={search_query}")
        opts = {}
        if data and 'places' in data:
            for p in data['places']:
                if 'stop_area' in p:
                    ville = p.get('administrative_regions', [{}])[0].get('name', '')
                    label = f"{p['name']} ({ville})" if ville else p['name']
                    opts[label] = p['stop_area']['id']
        if len(opts) > 0:
            st.session_state.search_results = opts
        else:
            st.session_state.search_results = {}
            st.session_state.search_error = "⚠️ Aucun résultat trouvé. Essayez un autre nom."
    st.session_state.search_key += 1
    st.rerun()

if st.session_state.search_results:
    opts = st.session_state.search_results
    choice = st.selectbox("Résultats trouvés :", list(opts.keys()))
    if choice:
        stop_id = opts[choice]
        if st.session_state.selected_stop != stop_id:
            st.session_state.selected_stop = stop_id
            st.session_state.selected_name = choice
            st.rerun()


# ==========================================
#           FRAGMENT LIVE (AUTO-REFRESH)
# ==========================================
# Ajoute l'argument 'container_header=None'
@st.fragment(run_every=15)
def afficher_live_content(stop_id, clean_name):
    # 1. CRÉATION DE LA BARRE D'ACTIONS (Interne au fragment pour éviter les bugs d'accumulation)
    # On donne plus de place au bouton (20%) pour qu'il soit plus large
    col_header, col_fav = st.columns([0.8, 0.2], gap="small", vertical_alignment="center")
    
    # A. Le Header (à gauche)
    header_placeholder = col_header.empty()
    
    # B. Le Bouton Favori (à droite)
    # On recalcule l'état favori ici car le fragment est isolé
    is_fav = any(f['id'] == stop_id for f in st.session_state.favorites)
    with col_fav:
        st.markdown('<div class="fav-btn-container">', unsafe_allow_html=True)
        # On ajoute un label au bouton pour qu'il soit plus large et explicite
        label_btn = "⭐ Suivi" if is_fav else "☆ Suivre"
        if st.button(label_btn, key=f"fav_btn_{stop_id}", use_container_width=True):
            toggle_favorite(stop_id, clean_name) # On passe clean_name, c'est suffisant
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # C. Préparation des conteneurs pour les résultats
    containers = {
        "Header": header_placeholder, # On pointe vers le placeholder créé juste au-dessus
        "RER": st.container(),
        "TRAIN": st.container(),
        "METRO": st.container(),
        "CABLE": st.container(),
        "TRAM": st.container(),
        "BUS": st.container(),
        "AUTRE": st.container()
    }
    
    # ... LE RESTE DU CODE RESTE EXACTEMENT LE MÊME ...
    
    def sort_key(k): 
        code = str(k[1]).strip().upper()
        if code.isalpha(): return (0, code)
        match = re.match(r"^([a-zA-Z]+)(\d+)", code)
        if match: return (1, match.group(1), int(match.group(2)))
        if code.isdigit(): return (2, int(code))
        return (3, code)

    def update_header(text, is_loading=False):
        loader_html = '<span class="custom-loader"></span>' if is_loading else ''
        html_content = f"""
        <div style='
            display: flex; align-items: center; color: #888; font-size: 0.8rem;
            height: 45px; line-height: 45px; overflow: hidden; font-weight: 500;
        '>
            {loader_html} <span style='margin-left: 8px;'>{text}</span>
        </div>
        """
        containers["Header"].markdown(html_content, unsafe_allow_html=True)

    update_header("Actualisation en cours...", is_loading=True)

    # ... [LE RESTE DU CODE (Lignes Théoriques, Temps Réel...) RESTE IDENTIQUE À AVANT] ...
    # Copie-colle le reste de ta fonction afficher_live_content ici (à partir de "# 1. LIGNES THEORIQUES")
    # ...

    # 1. LIGNES THEORIQUES
    data_lines = demander_lignes_arret(stop_id)
    all_lines_at_stop = {} 
    has_c1_cable = False # Flag pour détecter le Câble C1

    if data_lines and 'lines' in data_lines:
        for line in data_lines['lines']:
            raw_mode = "AUTRE"
            if 'physical_modes' in line and line['physical_modes']:
                raw_mode = line['physical_modes'][0].get('id', 'AUTRE')
            elif 'physical_mode' in line:
                raw_mode = line['physical_mode']
            
            mode = normaliser_mode(raw_mode)
            code = clean_code_line(line.get('code', '?')) 
            color = line.get('color', '666666')
            all_lines_at_stop[(mode, code)] = {'color': color}
            
            # DÉTECTION CÂBLE C1
            if mode == "CABLE" and code == "C1":
                has_c1_cable = True

    # 2. TEMPS REEL
    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=600")
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    last_departures_map = {} 

    if data_live and 'departures' in data_live:
        # PASSE 1 : CALCUL DU MAX
        for d in data_live['departures']:
            val_tri, _ = format_html_time(d['stop_date_time']['departure_date_time'], d.get('data_freshness', 'realtime'))
            if val_tri < 3000:
                info = d['display_informations']
                mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
                code = clean_code_line(info.get('code', '?')) 
                raw_dest = info.get('direction', '')
                # Nettoyage standard
                if mode != "BUS":
                    dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
                else:
                    match = re.search(r'(.*)\s*\(([^)]+)\)$', raw_dest)
                    if match:
                        name_part = match.group(1).strip()
                        city_part = match.group(2).strip()
                        if city_part.lower() in name_part.lower(): dest = name_part
                        elif '-' in city_part:
                            first_chunk = city_part.split('-')[0].strip()
                            if len(first_chunk) > 2 and first_chunk.lower() in name_part.lower(): dest = name_part
                            else: dest = raw_dest
                        else: dest = raw_dest
                    else: dest = raw_dest
                key = (mode, code, dest)
                current_max = last_departures_map.get(key, -999999)
                if val_tri > current_max: last_departures_map[key] = val_tri

        # PASSE 2 : REMPLISSAGE AVEC FUSION PRIORITAIRE
        for d in data_live['departures']:
            info = d['display_informations']
            
            # 1. DONNÉES BRUTES
            raw_mode = info.get('physical_mode', 'AUTRE')
            comm_mode = info.get('commercial_mode', '').upper()
            raw_code = str(info.get('code', '?')).strip().upper()
            raw_dest = info.get('direction', '')
            color = info.get('color', '666666')
            
            # Nettoyage du code (Ex: "BUS P" -> "P")
            clean_code = raw_code.replace("BUS", "").strip()
            mode = normaliser_mode(raw_mode)

            is_replacement = False
            match_found = None

            # 2. RECHERCHE DE CORRESPONDANCE THEORIQUE (Le point clé)
            # On regarde si une ligne ferrée portant ce code (ex: "P") existe DÉJÀ à cet arrêt.
            if mode == "BUS":
                for (theo_mode, theo_code) in all_lines_at_stop.keys():
                    # Si on trouve un Train/RER/Metro/Tram qui a le même code que notre bus
                    if theo_code == clean_code and theo_mode in ["RER", "TRAIN", "METRO", "TRAM"]:
                        match_found = (theo_mode, theo_code)
                        break

            # 3. DÉCISION DU STATUT
            if match_found:
                # CAS 1 : FUSION (Gare de l'Est)
                # Le bus s'appelle "P", et il y a un Train "P" ici -> C'est un remplacement !
                is_replacement = True
                mode = match_found[0] # On force le mode TRAIN
                code = match_found[1] # On force le code P
                color = all_lines_at_stop[match_found]['color'] # On vole la couleur (Orange)

            elif mode == "BUS":
                # CAS 2 : PAS DE FUSION (Pontault)
                # Le bus s'appelle "B", mais il n'y a pas de Train "B" ici.
                # On vérifie quand même les indices forts (Travaux/Admin) pour les gares complexes
                
                is_admin_train = ("RER" in comm_mode or "TRAIN" in comm_mode or "TRANSILIEN" in comm_mode)
                keywords = ["REMPLACEMENT", "SUBSTITUTION", "TRAVAUX", "BUS RELAIS", "BUS DE"]
                has_keywords = any(k in raw_dest.upper() for k in keywords)
                
                # Si indices forts, on crée une substitution "Orpheline" (sans ligne théorique)
                if is_admin_train or (clean_code in ["A","B","C","D","E","H","J","K","L","N","P","R","U"] and has_keywords):
                    is_replacement = True
                    code = clean_code
                    # On devine le mode
                    if code in ["A","B","C","D","E"]: mode = "RER"
                    elif code.startswith("T"): mode = "TRAM"
                    elif code.startswith("M"): mode = "METRO"
                    else: mode = "TRAIN"
                else:
                    # C'est juste un bus local -> On ne touche à rien
                    code = clean_code_line(info.get('code', '?'))

            else:
                # Ce n'est pas un bus, on garde tel quel
                code = clean_code_line(info.get('code', '?'))

            # --- SUITE STANDARD (Destination & Calculs) ---
            if mode != "BUS" or is_replacement:
                dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            else:
                match = re.search(r'(.*)\s*\(([^)]+)\)$', raw_dest)
                if match:
                    name_part = match.group(1).strip()
                    city_part = match.group(2).strip()
                    if city_part.lower() in name_part.lower(): dest = name_part
                    elif '-' in city_part:
                        first_chunk = city_part.split('-')[0].strip()
                        if len(first_chunk) > 2 and first_chunk.lower() in name_part.lower(): dest = name_part
                        else: dest = raw_dest
                    else: dest = raw_dest
            
            val_tri, html_time = format_html_time(d['stop_date_time']['departure_date_time'], d.get('data_freshness', 'realtime'))
            if val_tri < -5: continue 

            is_last = False
            is_noctilien = (mode == "BUS" and str(code).upper().startswith('N') and not is_replacement)
            if not is_noctilien and val_tri < 3000:
                key_check = (mode, code, dest)
                max_val = last_departures_map.get(key_check)
                if max_val is not None and val_tri == max_val:
                    try:
                        dep_str = d['stop_date_time']['departure_date_time']
                        dep_hour = int(dep_str.split('T')[1][:2])
                    except: dep_hour = 0
                    current_hour = datetime.now(pytz.timezone('Europe/Paris')).hour
                    is_evening_mode = (current_hour >= 21)
                    is_night_train = (dep_hour >= 22) or (dep_hour < 4)
                    if is_evening_mode or is_night_train:
                        is_last = True
            
            TRANSILIENS_OFFICIELS = ["H", "J", "K", "L", "N", "P", "R", "U", "V"]
            if is_last and mode == "TRAIN" and code not in TRANSILIENS_OFFICIELS and not is_replacement:
                is_last = False

            cle = (mode, code, color)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri, 'is_last': is_last, 'is_replacement': is_replacement})
    # 3. GHOST LINES
    MODES_NOBLES = ["RER", "TRAIN", "METRO", "CABLE", "TRAM"]
    for (mode_t, code_t), info_t in all_lines_at_stop.items():
        if mode_t in MODES_NOBLES:
            if code_t in ["TER", "R"]: continue
            exists_in_buckets = False
            if mode_t in buckets:
                for (b_mode, b_code, b_color) in buckets[mode_t]:
                    if b_code == code_t:
                        exists_in_buckets = True
                        break
            if not exists_in_buckets:
                cle_ghost = (mode_t, code_t, info_t['color'])
                if mode_t not in buckets: buckets[mode_t] = {}
                buckets[mode_t][cle_ghost] = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]
    
    # 4. FILTRAGE & NETTOYAGE
    for mode in list(buckets.keys()):
        keys_to_remove = []
        # On vérifie chaque ligne dans le mode
        for cle in buckets[mode]:
            code_clean = cle[1]; color_clean = cle[2]
            
            # Est-ce qu'il y a des départs affichables (< 50 min) ?
            has_active = any(d['tri'] < 3000 for d in buckets[mode][cle])
            
            if has_active: 
                displayed_lines_keys.add((mode, code_clean))
                # Si c'est une substitution, on marque aussi le BUS d'origine comme "traité" pour le footer
                if any(d.get('is_replacement') for d in buckets[mode][cle]):
                    displayed_lines_keys.add(("BUS", code_clean))
            else:
                # Si pas de départs actifs
                if mode == "BUS": 
                    # Les bus inactifs sont supprimés de l'affichage principal (-> footer)
                    keys_to_remove.append(cle)
                    footer_data[mode][code_clean] = color_clean
                else: 
                    # Les trains/RER inactifs restent affichés (avec "Service terminé")
                    displayed_lines_keys.add((mode, code_clean))
                    
        # On supprime les lignes inactives du dictionnaire
        for k in keys_to_remove: 
            del buckets[mode][k]
            
        # --- CORRECTIF CRITIQUE : Si le mode est devenu vide, on supprime la clé ---
        if not buckets[mode]:
            del buckets[mode]

    # 5. RENDU HTML
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    update_header(f"Dernière mise à jour : {heure_actuelle} • LIVE <span class='live-icon'>🟢</span>", is_loading=False)

    ordre_affichage = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    has_data = False

    for mode_actuel in ordre_affichage:
        # SÉCURITÉ ABSOLUE : Si le mode n'est plus dans les buckets, on passe au suivant
        if mode_actuel not in buckets: 
            continue
        
        lignes_du_mode = buckets[mode_actuel]
        has_data = True
        
        with containers[mode_actuel]:
            st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)
            
            # ... (Le reste de la boucle d'affichage reste identique) ...
            for cle in sorted(lignes_du_mode.keys(), key=sort_key):
                _, code, color = cle
                departs = lignes_du_mode[cle]
                proches = [d for d in departs if d['tri'] < 3000]
                if not proches:
                     proches = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]

                # CAS 1: RER/TRAIN (Logique géographique CORRIGÉE)
                if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                    geo = GEOGRAPHIE_RER[code]
                    stop_upper = clean_name.upper()
                    local_mots_1 = geo['mots_1'].copy(); local_mots_2 = geo['mots_2'].copy()
                    
                    # (Ta logique de filtres C et D reste identique ici...)
                    if code == "C":
                        if any(k in stop_upper for k in ["MAILLOT", "PEREIRE", "CLICHY", "ST-OUEN", "GENNEVILLIERS", "ERMONT", "PONTOISE", "FOCH", "MARTIN", "BOULAINVILLIERS", "KENNEDY", "JAVEL", "GARIGLIANO"]):
                            if "INVALIDES" in local_mots_1: local_mots_1.remove("INVALIDES")
                            if "INVALIDES" not in local_mots_2: local_mots_2.append("INVALIDES")
                    if code == "D":
                        zone_nord_d = ["CREIL", "ORRY", "COYE", "SURVILLIERS", "FOSSES", "LOUVRES", "GOUSSAINVILLE", "VILLIERS-LE-BEL", "GARGES", "SARCELLES", "PIERREFITTE", "STAINS", "SAINT-DENIS", "STADE DE FRANCE", "NORD"]
                        if any(k in stop_upper for k in zone_nord_d):
                            if "GARE DE LYON" in local_mots_2: local_mots_2.remove("GARE DE LYON")
                            if "GARE DE LYON" not in local_mots_1: local_mots_1.append("GARE DE LYON")

                    # Répartition des départs dans les groupes
                    p1 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_1)]
                    p2 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_2)]
                    # p3 récupère tout ce qui n'a pas matché (souvent les bus de substitution aux noms bizarres)
                    p3 = [d for d in proches if d not in p1 and d not in p2]
                    
                    # Nettoyage de p3 pour ne garder que les vrais trajets (pas les "Service terminé" générés par Ghost Lines)
                    real_p3 = [x for x in p3 if x['tri'] < 3000]

                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                    
                    # Fonction helper (inchangée)
                    def render_group(titre, items):
                        h = f"<div class='rer-direction'>{titre}</div>"
                        if not items: return h + """<div class="service-box">😴 Service terminé</div>"""
                        items.sort(key=lambda x: x['tri'])
                        for it in items[:4]:
                            val_tri = it['tri']
                            dest_txt = it['dest']
                            if it.get('is_replacement'):
                                h += f"""<div class='replacement-box'><span class='replacement-label'>🚍 Bus de substitution</span><div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div></div>"""
                            elif it.get('is_last'):
                                if val_tri < 10: h += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div></div>"""
                                else: h += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span class='last-dep-text-only'>{it['html']} 🏁</span></div>"""
                            else:
                                h += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div>"""
                        return h

                    # --- LOGIQUE D'AFFICHAGE CORRIGÉE ---
                    # On n'affiche "Service terminé" QUE si p1, p2 ET real_p3 sont vides
                    has_data_p1 = any(d['tri'] < 3000 for d in p1)
                    has_data_p2 = any(d['tri'] < 3000 for d in p2)
                    has_data_p3 = len(real_p3) > 0

                    if not has_data_p1 and not has_data_p2 and not has_data_p3:
                        card_html += """<div class="service-box">😴 Service terminé</div>"""
                    else:
                        # On affiche les blocs s'ils ne sont pas les terminus
                        if not any(k in stop_upper for k in geo['term_1']): 
                            card_html += render_group(geo['labels'][0], p1)
                        
                        if not any(k in stop_upper for k in geo['term_2']): 
                            card_html += render_group(geo['labels'][1], p2)
                        
                        # Si on a des rescapés dans p3 (souvent les bus !), on les affiche
                        if has_data_p3: 
                            card_html += render_group("AUTRES DIRECTIONS / BUS", real_p3)
                            
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)
                # CAS 2: RER/TRAIN SIMPLE
                elif mode_actuel in ["RER", "TRAIN"]:
                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:10px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                    if not proches or (len(proches)==1 and proches[0]['tri']==3000): card_html += f"""<div class="service-box">😴 Service terminé</div>"""
                    else:
                        proches.sort(key=lambda x: x['tri'])
                        for item in proches[:4]:
                            val_tri = item['tri']
                            dest_txt = item['dest']
                            if item.get('is_replacement'):
                                card_html += f"""
                                <div class='replacement-box'>
                                    <span class='replacement-label'>🚍 Bus de substitution</span>
                                    <div class='rail-row'>
                                        <span class='rail-dest'>{dest_txt}</span>
                                        <span>{item['html']}</span>
                                    </div>
                                </div>"""
                            elif item.get('is_last'):
                                if val_tri < 10:
                                    card_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{item['html']}</span></div></div>"""
                                elif val_tri <= 30:
                                    card_html += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span class='last-dep-small-frame'>{item['html']} 🏁</span></div>"""
                                else:
                                    card_html += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span class='last-dep-text-only'>{item['html']} 🏁</span></div>"""
                            else:
                                card_html += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{item['html']}</span></div>"""
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)

                # CAS 3: BUS/METRO/TRAM/CABLE (Traitement Standard Unifié)
                # CAS SPÉCIFIQUE : CÂBLE C1 (Filtrage Perturbations Strict)
                elif code == "C1":
                    rows_html = ""
                    destinations_vues = []
                    
                    # --- A. GESTION DES PERTURBATIONS ---
                    perturbation_msg = None 
                    
                    tz_paris = pytz.timezone('Europe/Paris')
                    now_hour = datetime.now(tz_paris).hour
                    
                    if not proches and (6 <= now_hour < 23):
                         perturbation_msg = "Aucun départ détecté - Vérifiez l'état de la ligne"

                    # Alerte
                    alert_html = ""
                    if perturbation_msg:
                        alert_html = f"<div style='background:rgba(231,76,60,0.15);border-left:4px solid #e74c3c;color:#ffadad;padding:10px;margin-bottom:12px;border-radius:4px;display:flex;align-items:start;gap:10px;'><span style='font-size:1.2em;'>⚠️</span><span style='font-size:0.9em;line-height:1.4;'>{perturbation_msg}</span></div>"

                    # --- B. AFFICHAGE DES DESTINATIONS ---
                    for d in proches:
                        dn = d['dest']
                        if dn not in destinations_vues:
                            destinations_vues.append(dn)
                            freq_text = "Départ toutes les ~30s"

                            # HTML compacté
                            rows_html += f"""<div class="bus-row" style="align-items:center;"><span class="bus-dest">➜ {dn}</span><span style="background-color:rgba(255,255,255,0.1);padding:4px 10px;border-radius:12px;font-size:0.85em;color:#a9cce3;white-space:nowrap;">⏱ {freq_text}</span></div>"""
                    
                    if not rows_html and not perturbation_msg:
                         rows_html = '<div class="service-box">😴 Service terminé</div>'

                    # --- C. RENDU DE LA CARTE ---
                    # Suppression de l'émoji et simplification de l'en-tête
                    st.markdown(f"""
<div class="bus-card" style="border-left-color: #{color}; position: relative;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span class="line-badge" style="background-color:#{color};">{code}</span>
</div>
{alert_html}
{rows_html}
</div>
""", unsafe_allow_html=True)
                # CAS 3: BUS/METRO/TRAM (Standard)
                else:
                    dest_data = {}
                    # 1. Regroupement par destination
                    for d in proches:
                        dn = d['dest']
                        if dn not in dest_data: dest_data[dn] = {'items': [], 'best_time': 9999}
                        # On garde les 3 prochains départs max par destination
                        if len(dest_data[dn]['items']) < 3:
                            dest_data[dn]['items'].append(d)
                            if d['tri'] < dest_data[dn]['best_time']: dest_data[dn]['best_time'] = d['tri']
                    
                    # 2. Tri des destinations
                    if mode_actuel in ["METRO", "TRAM", "CABLE"]: 
                        sorted_dests = sorted(dest_data.items(), key=lambda item: item[0])
                    else: 
                        sorted_dests = sorted(dest_data.items(), key=lambda item: item[1]['best_time'])
                    
                    is_noctilien = str(code).strip().upper().startswith('N')
                    rows_html = ""
                    
                    # 3. Génération des lignes
                    for dest_name, info in sorted_dests:
                        if "Service terminé" in dest_name: 
                            rows_html += f'<div class="service-box">😴 Service terminé</div>'
                        else:
                            html_list = []
                            contains_last = False; last_val_tri = 9999
                            is_group_replacement = False
                            
                            if info['items'] and info['items'][0].get('is_replacement'):
                                is_group_replacement = True
    
                            for idx, d_item in enumerate(info['items']):
                                val_tri = d_item['tri']
                                if idx > 0 and val_tri > 62 and not is_noctilien: continue
                                
                                txt = d_item['html']
                                if d_item.get('is_last'):
                                    contains_last = True
                                    last_val_tri = val_tri
                                    if val_tri < 10: txt = f"<span class='last-dep-text-only'>{txt} 🏁</span>"
                                    elif val_tri <= 30: txt = f"<span class='last-dep-small-frame'>{txt} 🏁</span>"
                                    else: txt = f"<span class='last-dep-text-only'>{txt} 🏁</span>"
                                html_list.append(txt)
                            
                            if not html_list and info['items']: html_list.append(info['items'][0]['html'])
                            times_str = "<span class='time-sep'>|</span>".join(html_list)
                            
                            row_content = f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'
    
                            if is_group_replacement:
                                rows_html += f"""<div class='replacement-box'><span class='replacement-label'>🚍 Bus de substitution</span>{row_content}</div>"""
                            elif contains_last and len(html_list) == 1 and last_val_tri < 10:
                                rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span>{row_content}</div>"""
                            else:
                                rows_html += row_content                    

                    st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>{rows_html}</div>""", unsafe_allow_html=True)
    # 6. FOOTER
    with containers["AUTRE"]:
        for (mode_theo, code_theo), info in all_lines_at_stop.items():
            if (mode_theo, code_theo) not in displayed_lines_keys:
                if mode_theo not in footer_data: footer_data[mode_theo] = {}
                footer_data[mode_theo][code_theo] = info['color']
        
        count_visible = sum(len(footer_data[m]) for m in footer_data if m != "AUTRE")

        if not has_data:
            if count_visible > 0: st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(52, 152, 219, 0.1); border-radius: 10px; margin-top: 20px; margin-bottom: 20px;'><h3 style='margin:0; color: #3498db;'>😴 Aucun départ immédiat</h3></div>""", unsafe_allow_html=True)
            else: st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(231, 76, 60, 0.1); border-radius: 10px; margin-top: 20px;'><h3 style='margin:0; color: #e74c3c;'>📭 Aucune information</h3></div>""", unsafe_allow_html=True)

        if count_visible > 0:
            st.markdown("<div style='margin-top: 10px; border-top: 1px solid #333; padding-top: 15px;'></div>", unsafe_allow_html=True)
            st.caption("Autres lignes desservant cet arrêt :")
            
            for mode in ordre_affichage:
                if mode == "AUTRE": continue
                if mode in footer_data and footer_data[mode]:
                    html_badges = ""
                    items = footer_data[mode]
                    
                    # --- MÉTHODE TRI INFAILLIBLE (SÉPARATION) ---
                    liste_lettres = []
                    liste_chiffres = []
                    
                    for code in items.keys():
                        c_str = str(code).strip()
                        if c_str.isdigit():
                            liste_chiffres.append(c_str)
                        else:
                            liste_lettres.append(c_str)
                    
                    # 1. On trie les lettres par ordre alphabétique (A, B, J, N137...)
                    liste_lettres.sort()
                    
                    # 2. On trie les chiffres par valeur numérique (1, 10, 100...)
                    liste_chiffres.sort(key=lambda x: int(x))
                    
                    # 3. ON COLLE : Lettres D'ABORD, Chiffres ENSUITE
                    sorted_codes = liste_lettres + liste_chiffres
                    # --------------------------------------------

                    for code in sorted_codes:
                        color = items[code]
                        html_badges += f'<span class="line-badge footer-badge" style="background-color:#{color};">{code}</span>'
                    
                    if html_badges:
                        st.markdown(f"""<div class="footer-container"><span class="footer-icon">{ICONES_TITRE[mode]}</span><div>{html_badges}</div></div>""", unsafe_allow_html=True)                        
# ========================================================
#                  AFFICHAGE LIVE (WRAPPER PRINCIPAL)
# ========================================================
def afficher_tableau_live(stop_id, stop_name):
    clean_name = stop_name.split('(')[0].strip()
    
    # 1. TITRE (PLEINE LARGEUR)
    st.markdown(f"<div class='station-title'>📍 {clean_name}</div>", unsafe_allow_html=True)
            
    # 2. APPEL DU FRAGMENT (Il gère maintenant le Header ET le Bouton)
    afficher_live_content(stop_id, clean_name)
# ========================================================
#           AFFICHAGE LIVE OU ACCUEIL (TUTO)
# ========================================================

# 1. Si une gare est sélectionnée -> On affiche le tableau de bord
if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)

# 2. Sinon -> Tuto de Bienvenue (Construction sécurisée & Couleurs dynamiques)
elif not st.session_state.search_results:
    # On construit le HTML morceau par morceau pour éviter les erreurs d'indentation
    html_content = "".join([
        '<div style="text-align: center; margin-top: 40px; margin-bottom: 40px; animation: float 3s ease-in-out infinite;">',
            '<span style="font-size: 50px;">👋</span>',
        '</div>',
        
        '<div style="text-align: center; margin-bottom: 30px;">',
            # Titre adaptatif
            '<h3 style="color: var(--text-color); margin-bottom: 10px;">Bienvenue sur Grand Paname</h3>',
            # Sous-titre adaptatif
            '<p style="font-size: 1.1em; opacity: 0.8; color: var(--text-color);">Votre compagnon de voyage pour l\'Île-de-France.</p>',
        '</div>',
        
        '<div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">',
            
            # CARTE 1
            # Background adaptatif (gris clair ou sombre) + Bordure neutre + Texte adaptatif
            '<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">',
                '<div style="font-size: 24px; margin-bottom: 10px;">🔍</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Recherchez</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Entrez le nom de votre station ci-dessus.</div>',
            '</div>',
            
            # CARTE 3
            '<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">',
                '<div style="font-size: 24px; margin-bottom: 10px;">⚡</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Temps Réel</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Vos prochains départs actualisés en temps réel.</div>',
            '</div>',

            # CARTE 2
            '<div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">',
                '<div style="font-size: 24px; margin-bottom: 10px;">⭐</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Favoris</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Cliquez sur l\'étoile pour sauvegarder votre arrêt.</div>',
            '</div>',
            
        '</div>'
    ])
    
    st.markdown(html_content, unsafe_allow_html=True)
