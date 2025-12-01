import streamlit as st
import requests
from datetime import datetime
import re
import time
import pytz
import os
from PIL import Image
import base64

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

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Grand Paname (v1.0 ALPHA)",
    page_icon=icon_image,
    layout="centered"
)

# 2. FONCTION POLICE
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
            @font-face {{
                font-family: '{font_name}';
                src: url('data:font/{ext};base64,{b64}') format('{format_str}');
            }}
            html, body {{ font-family: '{font_name}', sans-serif; }}
            h1, h2, h3, h4, h5, h6, p, a, li, button, input, label, textarea {{
                font-family: '{font_name}', sans-serif !important;
            }}
            .stMarkdown, .stButton, .stTextInput, .stSelectbox {{
                font-family: '{font_name}', sans-serif !important;
            }}
            .streamlit-expanderHeader {{
                font-family: '{font_name}', sans-serif !important;
            }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        pass

charger_police_locale("GrandParis.otf", "Grand Paris")

# ==========================================
#              STYLE CSS (Ninja Update v2)
# ==========================================
st.markdown("""
<style>
    /* --- CSS NINJA : FORCER L'OPACITÉ --- */
    
    /* Cible le fragment et force l'opacité à 100% tout le temps */
    div[data-testid="stFragment"] {
        opacity: 1 !important;
        transform: none !important;
        transition: none !important;
        filter: none !important;
    }
    
    /* Cible les conteneurs internes pour empêcher le clignotement */
    div.element-container {
        opacity: 1 !important;
        filter: none !important;
    }
    
    /* Cache l'icône de chargement (le spinner) par défaut de Streamlit */
    div[data-testid="stSpinner"] {
        display: none !important;
    }
    
    /* Cache la barre de progression "Running" en haut */
    .stApp > header {
        visibility: hidden !important;
    }
    
    /* ----------------------------------------- */

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
    }
    
    .footer-container { display: flex; align-items: center; margin-bottom: 8px; }
    .footer-icon { margin-right: 10px; font-size: 14px; color: var(--text-color); opacity: 0.7; }
    .footer-badge { font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important; }

    .time-sep { color: #888; margin: 0 8px; font-weight: lighter; }
    
    .section-header {
        margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5); 
        font-size: 20px; font-weight: bold; color: var(--text-color); letter-spacing: 1px;
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
    
    .bus-card, .rail-card {
        background-color: #1a1a1a; padding: 12px; margin-bottom: 15px; border-radius: 8px; border-left: 5px solid #666; color: #ddd; 
    }

    .bus-row, .rail-row {
        display: flex; justify-content: space-between; padding-top: 8px; padding-bottom: 2px; border-top: 1px solid #333; 
    }
    
    .rer-direction + .rail-row { border-top: none; padding-top: 8px; }
    
    .bus-dest, .rail-dest { color: #ccc; font-size: 15px; font-weight: 500; }
    
    .service-box { 
        text-align: left; padding: 10px 12px; color: #888; font-style: italic; font-size: 0.95em;
        background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-top: 5px; margin-bottom: 5px; border-left: 3px solid #444;
    }
    .service-end { color: #999; font-style: italic; font-size: 0.9em; }

    .last-dep-box {
        border: 2px solid #f1c40f; border-radius: 6px; padding: 8px 10px; margin-top: 8px; margin-bottom: 8px;
        background-color: rgba(241, 196, 15, 0.1); animation: yellow-pulse 2s infinite;
    }
    .last-dep-label { display: block; font-size: 0.75em; text-transform: uppercase; font-weight: bold; color: #f1c40f; margin-bottom: 4px; letter-spacing: 1px; }
    .last-dep-box .rail-row, .last-dep-box .bus-row { border-top: none !important; padding-top: 0 !important; margin-top: 0 !important; }

    /* LE STYLE DU BADGE ALPHA */
    .version-badge {
        background: linear-gradient(45deg, #FF4B4B, #F76B1C);
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.5em; 
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        vertical-align: middle;
        margin-left: 10px;
        letter-spacing: 1px;
    }
    
    .verified-badge {
        color: #3498db;
        font-size: 0.8em;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
#              LOGIQUE MÉTIER
# ==========================================

GEOGRAPHIE_RER = {
    "A": {
        "labels": ("⇦ OUEST (Cergy / Poissy / St-Germain)", "⇨ EST (Marne-la-Vallée / Boissy)"),
        "mots_1": ["CERGY", "POISSY", "GERMAIN", "RUEIL", "DEFENSE", "DÉFENSE", "NANTERRE", "VESINET", "MAISONS", "LAFFITTE", "PECQ", "ACHERES", "GRANDE ARCHE"],
        "term_1": ["CERGY", "POISSY", "GERMAIN"],
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
        "mots_1": ["MELUN", "CORBEIL", "MALESHERBES", "GARE DE LYON", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"],
        "term_1": ["MELUN", "CORBEIL", "MALESHERBES"],
        "mots_2": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS"],
        "term_2": ["CREIL", "ORRY"]
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
        # J'ai ajouté "SARCELLES" et "BRICE" ici
        "mots_1": ["PONTOISE", "PERSAN", "BEAUMONT", "LUZARCHES", "CREIL", "MONTSOULT", "VALMONDOIS", "SARROUS", "SAINT-LEU", "SARCELLES", "BRICE"],
        "term_1": ["PONTOISE", "PERSAN", "LUZARCHES", "CREIL"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "J": {
        "labels": ("⇦ OUEST (Mantes / Gisors / Ermont)", "⇨ PARIS ST-LAZARE"),
        # J'ai ajouté "MUREAUX" et "CORMEILLES" (souvent un terminus aussi)
        "mots_1": ["MANTES", "JOLIE", "GISORS", "ERMONT", "VERNON", "PONTOISE", "CONFLANS", "BOISSY", "MEULAN", "MUREAUX", "CORMEILLES"],
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
        "mots_1": ["VERSAILLES", "NOM", "BRETÈCHE", "CERGY", "NANTERRE", "MAISONS", "CLOUD"],
        "term_1": ["VERSAILLES", "NOM", "CERGY"],
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

ICONES_TITRE = {
    "RER": "🚆 RER", "TRAIN": "🚆 TRAIN", "METRO": "🚇 MÉTRO", 
    "TRAM": "🚋 TRAMWAY", "CABLE": "🚠 CÂBLE", "BUS": "🚌 BUS", "AUTRE": "🌙 AUTRE"
}

HIERARCHIE = {"RER": 1, "TRAIN": 2, "METRO": 3, "CABLE": 4, "TRAM": 5, "BUS": 6, "AUTRE": 99}

def demander_api(suffixe):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/{suffixe}", headers=headers)
        return r.json()
    except: return None

# =============================================================
#  IMPORTANT : CETTE FONCTION ÉTAIT MANQUANTE ET CAUSAIT L'ERREUR
# =============================================================
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

st.markdown("<h1>🚆 Grand Paname <span class='version-badge'>v1.0 Alpha</span></h1>", unsafe_allow_html=True)
st.markdown("##### *L'application de référence pour vos départs en Île-de-France* <span class='verified-badge'>✔ Officiel</span>", unsafe_allow_html=True)
# --- INITIALISATION DES FAVORIS ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

def toggle_favorite(stop_id, stop_name):
    """Ajoute ou retire un arrêt des favoris."""
    # On nettoie le nom pour l'affichage (enlève la ville entre parenthèses)
    clean_name = stop_name.split('(')[0].strip()
    
    # Vérifie si l'ID est déjà dans la liste
    exists = False
    for i, fav in enumerate(st.session_state.favorites):
        if fav['id'] == stop_id:
            st.session_state.favorites.pop(i) # On retire
            exists = True
            st.toast(f"❌ {clean_name} retiré des favoris", icon="🗑️")
            break
    
    if not exists:
        st.session_state.favorites.append({'id': stop_id, 'name': clean_name, 'full_name': stop_name})
        st.toast(f"⭐ {clean_name} ajouté aux favoris !", icon="✅")

with st.sidebar:
    st.caption("v1.0.0 - Abondance 🧀")
    
    # --- SECTION FAVORIS ---
    st.header("⭐ Mes Favoris")
    if not st.session_state.favorites:
        st.info("Ajoutez des gares en cliquant sur l'étoile à côté de leur nom !")
    else:
        # On affiche les favoris sous forme de boutons
        for fav in st.session_state.favorites:
            if st.button(f"📍 {fav['name']}", key=f"btn_fav_{fav['id']}", use_container_width=True):
                st.session_state.selected_stop = fav['id']
                st.session_state.selected_name = fav['full_name']
                st.session_state.search_key += 1 # Petite astuce pour forcer le refresh UI
                st.rerun()
    
    st.markdown("---")
    
    # --- SECTION INFOS ---
    st.header("🗄️ Informations")
    st.warning("🚧 **Zone de travaux !**\n\nBienvenue sur la version 1.0. Nous reconstruisons les fondations pour plus de rapidité. Si vous croisez un bug, soyez sympa ! 🥺")
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

with st.form("search_form"):
    search_query = st.text_input(
        "🔍 Rechercher une station :", 
        placeholder="Ex: Noisiel, Saint-Lazare...",
        value=st.session_state.last_query, 
        key=f"search_input_{st.session_state.search_key}"
    )
    submitted = st.form_submit_button("Rechercher")

if st.session_state.search_error:
    st.warning(st.session_state.search_error)

if submitted and search_query:
    st.session_state.last_query = search_query 
    st.session_state.search_error = None
    with st.spinner("Recherche des arrêts..."):
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

# ========================================================
#                  AFFICHAGE LIVE (OPTIMISÉ + FIX TER)
# ========================================================
@st.fragment(run_every=15)
def afficher_tableau_live(stop_id, stop_name):
    
    clean_name = stop_name.split('(')[0].strip()
    
    # --- GESTION DU BOUTON FAVORI ---
    # On vérifie si la gare actuelle est déjà favorite
    is_fav = any(f['id'] == stop_id for f in st.session_state.favorites)
    
    # Mise en page : Colonne Titre (Large) + Colonne Bouton (Petite)
    col_title, col_fav = st.columns([0.85, 0.15])
    
    with col_title:
        st.markdown(f"<div class='station-title'>📍 {clean_name}</div>", unsafe_allow_html=True)
        
    with col_fav:
        # On centre le bouton verticalement avec un peu de marge vide
        st.write("") 
        if st.button("⭐" if is_fav else "☆", key=f"toggle_{stop_id}", help="Ajouter/Retirer des favoris"):
            toggle_favorite(stop_id, stop_name)
            st.rerun()
    
    # On prépare des conteneurs vides
    containers = {
        "Header": st.empty(),
        "RER": st.container(),
        "TRAIN": st.container(),
        "METRO": st.container(),
        "CABLE": st.container(),
        "TRAM": st.container(),
        "BUS": st.container(),
        "AUTRE": st.container()
    }
    
    # --- FIX STABILITÉ HTML ---
    def update_header(text, is_loading=False):
        loader_html = '<span class="custom-loader"></span>' if is_loading else ''
        html_content = f"""
        <div style='
            display: flex; align-items: center; color: #888; font-size: 0.8rem; font-style: italic; margin-bottom: 10px;
            height: 30px; line-height: 30px; overflow: hidden;
        '>
            {loader_html} <span style='margin-left: 8px;'>{text}</span>
        </div>
        """
        containers["Header"].markdown(html_content, unsafe_allow_html=True)

    # 1. ÉTAT CHARGEMENT
    update_header("Actualisation rapide...", is_loading=True)

    # 2. LIGNES THEORIQUES
    data_lines = demander_lignes_arret(stop_id)
    all_lines_at_stop = {} 

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

    # 3. TEMPS REEL
    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=600")
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    last_departures_map = {} 

    if data_live and 'departures' in data_live:
        # --- NETTOYAGE INTELLIGENT DES NOMS (V2) ---
                raw_dest = info.get('direction', '')
                if mode != "BUS":
                    dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
                else:
                    match = re.search(r'(.*)\s*\(([^)]+)\)$', raw_dest)
                    if match:
                        name_part = match.group(1).strip()
                        city_part = match.group(2).strip()
                        
                        # 1. Vérification exacte (Ex: Noisiel inclus dans Gare de Noisiel)
                        if city_part.lower() in name_part.lower():
                            dest = name_part
                        # 2. Vérification partielle pour villes composées (Ex: Sucy-en-Brie -> Sucy)
                        elif '-' in city_part:
                            # On prend juste le premier mot avant le tiret (ex: "Sucy")
                            first_chunk = city_part.split('-')[0].strip()
                            # Sécurité : on ne filtre que si le morceau fait plus de 2 lettres (évite les faux positifs)
                            if len(first_chunk) > 2 and first_chunk.lower() in name_part.lower():
                                dest = name_part
                            else:
                                dest = raw_dest
                        else:
                            dest = raw_dest
                    else:
                        dest = raw_dest
                # -------------------------------------------
                
                key = (mode, code, dest)
                if val_tri > last_departures_map.get(key, -999999): last_departures_map[key] = val_tri

        # Passe 2 : Buckets
        for d in data_live['departures']:
            info = d['display_informations']
            mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
            code = clean_code_line(info.get('code', '?')) 
            color = info.get('color', '666666')
            
            # --- NETTOYAGE INTELLIGENT DES NOMS (V2 - Copie conforme) ---
            raw_dest = info.get('direction', '')
            if mode != "BUS":
                dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            else:
                match = re.search(r'(.*)\s*\(([^)]+)\)$', raw_dest)
                if match:
                    name_part = match.group(1).strip()
                    city_part = match.group(2).strip()
                    
                    if city_part.lower() in name_part.lower():
                        dest = name_part
                    elif '-' in city_part:
                        first_chunk = city_part.split('-')[0].strip()
                        if len(first_chunk) > 2 and first_chunk.lower() in name_part.lower():
                            dest = name_part
                        else:
                            dest = raw_dest
                    else:
                        dest = raw_dest
                else:
                    dest = raw_dest
            # -------------------------------------------------------------
            # -------------------------------------------------------------
            
            val_tri, html_time = format_html_time(d['stop_date_time']['departure_date_time'], d.get('data_freshness', 'realtime'))
            
            if val_tri < -5: continue 
            # ... (la suite reste inchangée) ... 

            # ... (code précédent: val_tri, html_time, etc.)

            is_last = False
            if val_tri < 3000:
                # Clé pour identifier la ligne et la direction
                key_check = (mode, code, dest)
                max_val = last_departures_map.get(key_check)
                
                # Si ce train correspond au temps le plus lointain trouvé
                if max_val and val_tri == max_val:
                    
                    # --- NOUVELLE LOGIQUE INTELLIGENTE ---
                    # 1. On récupère l'heure réelle de départ du train (HH)
                    try:
                        dep_str = d['stop_date_time']['departure_date_time']
                        # Format Navitia : YYYYMMDDTHHMMSS -> On prend le HH après le T
                        dep_hour = int(dep_str.split('T')[1][:2])
                    except:
                        dep_hour = 0

                    # 2. On récupère l'heure actuelle
                    current_hour = datetime.now(pytz.timezone('Europe/Paris')).hour
                    
                    # 3. CRITÈRES STRICTS :
                    # - Soit on est déjà en "Mode Soirée" (après 21h)
                    # - Soit le train part dans la "Zone Nuit" (22h - 04h du matin)
                    is_evening_mode = (current_hour >= 21)
                    is_night_train = (dep_hour >= 22) or (dep_hour < 4)
                    
                    if is_evening_mode or is_night_train:
                        is_last = True
            
            # --- FIX TER (Toujours utile) ---
            # Si c'est un TRAIN mais pas un Transilien officiel, on force is_last à False par sécurité
            TRANSILIENS_OFFICIELS = ["H", "J", "K", "L", "N", "P", "R", "U", "V"]
            if is_last and mode == "TRAIN" and code not in TRANSILIENS_OFFICIELS:
                is_last = False
            # -----------------------------------------------------------

            cle = (mode, code, color)
            # ... (suite du code)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri, 'is_last': is_last})

    # 4. GHOST LINES
    MODES_NOBLES = ["RER", "TRAIN", "METRO", "CABLE", "TRAM"]
    for (mode_t, code_t), info_t in all_lines_at_stop.items():
        if mode_t in MODES_NOBLES:
            if code_t in ["TER", "R"]: continue
            exists = False
            if mode_t in buckets:
                for (b_mode, b_code, b_color) in buckets[mode_t]:
                    if b_code == code_t: exists = True; break
            if not exists:
                cle_ghost = (mode_t, code_t, info_t['color'])
                if mode_t not in buckets: buckets[mode_t] = {}
                buckets[mode_t][cle_ghost] = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]
    
    # 5. FILTRAGE
    for mode in list(buckets.keys()):
        keys_to_remove = []
        for cle in buckets[mode]:
            code_clean = cle[1]; color_clean = cle[2]
            has_active = any(d['tri'] < 3000 for d in buckets[mode][cle])
            if has_active: displayed_lines_keys.add((mode, code_clean))
            else:
                if mode == "BUS": keys_to_remove.append(cle); footer_data[mode][code_clean] = color_clean
                else: displayed_lines_keys.add((mode, code_clean))
        for k in keys_to_remove: del buckets[mode][k]

    # 6. AFFICHAGE FINAL
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    update_header(f"Dernière mise à jour : {heure_actuelle} 🔴 LIVE", is_loading=False)

    ordre_affichage = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    has_data = False

    for mode_actuel in ordre_affichage:
        lignes_du_mode = buckets[mode_actuel]
        if not lignes_du_mode: continue
        
        has_data = True
        
        with containers[mode_actuel]:
            st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)

            def sort_key(k): 
                try: return (0, int(k[1])) 
                except: return (1, k[1])
            
            for cle in sorted(lignes_du_mode.keys(), key=sort_key):
                _, code, color = cle
                departs = lignes_du_mode[cle]
                proches = [d for d in departs if d['tri'] < 3000]
                if not proches: proches = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]

                if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                    geo = GEOGRAPHIE_RER[code]
                    stop_upper = clean_name.upper()
                    local_mots_1 = geo['mots_1'].copy(); local_mots_2 = geo['mots_2'].copy()
                    if code == "C":
                        if any(k in stop_upper for k in ["MAILLOT", "PEREIRE", "CLICHY", "ST-OUEN", "GENNEVILLIERS", "ERMONT", "PONTOISE", "FOCH", "MARTIN", "BOULAINVILLIERS", "KENNEDY", "JAVEL", "GARIGLIANO"]):
                            if "INVALIDES" in local_mots_1: local_mots_1.remove("INVALIDES")
                            if "INVALIDES" not in local_mots_2: local_mots_2.append("INVALIDES")

                    p1 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_1)]
                    p2 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_2)]
                    p3 = [d for d in proches if d not in p1 and d not in p2]
                    
                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                    
                    def render_group(titre, items):
                        h = f"<div class='rer-direction'>{titre}</div>"
                        items.sort(key=lambda x: x['tri'])
                        for it in items[:4]:
                            if it.get('is_last'): h += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div></div>"""
                            else: h += f"""<div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div>"""
                        return h

                    if not p1 and not p2: card_html += """<div class="service-box">😴 Service terminé</div>"""
                    else:
                        if not any(k in stop_upper for k in geo['term_1']): card_html += render_group(geo['labels'][0], p1)
                        if not any(k in stop_upper for k in geo['term_2']): card_html += render_group(geo['labels'][1], p2)
                    if p3 and any(d['tri'] < 3000 for d in p3): card_html += render_group("AUTRES DIRECTIONS", p3)
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)

                elif mode_actuel in ["RER", "TRAIN"]:
                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:10px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                    if not proches or (len(proches)==1 and proches[0]['tri']==3000): card_html += f"""<div class="service-box">😴 Service terminé</div>"""
                    else:
                        proches.sort(key=lambda x: x['tri'])
                        for item in proches[:4]:
                            if item.get('is_last'): card_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div></div>"""
                            else: card_html += f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div>"""
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)

                else:
                    dest_data = {}
                    for d in proches:
                        dn = d['dest']
                        if dn not in dest_data: dest_data[dn] = {'items': [], 'best_time': 9999}
                        if len(dest_data[dn]['items']) < 3:
                            dest_data[dn]['items'].append(d)
                            if d['tri'] < dest_data[dn]['best_time']: dest_data[dn]['best_time'] = d['tri']
                    
                    if mode_actuel in ["METRO", "TRAM", "CABLE"]: sorted_dests = sorted(dest_data.items(), key=lambda item: item[0])
                    else: sorted_dests = sorted(dest_data.items(), key=lambda item: item[1]['best_time'])
                    
                    is_noctilien = str(code).strip().upper().startswith('N')
                    rows_html = ""
                    
                    if code == "C1":
                        target_date = datetime(2025, 12, 13, 11, 0, 0, tzinfo=pytz.timezone('Europe/Paris'))
                        now = datetime.now(pytz.timezone('Europe/Paris'))
                        if target_date > now:
                            delta = target_date - now
                            days = delta.days; hours = delta.seconds // 3600; mins = (delta.seconds % 3600) // 60
                            rows_html += f'<div class="bus-row"><span class="bus-dest">➜ Ouverture Public</span><span style="font-weight:bold; color:#56CCF2;">{days}j {hours}h {mins}min</span></div>'
                        else: rows_html += f'<div class="bus-row"><span class="bus-dest">➜ En service</span><span class="text-green">Ouvert !</span></div>'
                    else:
                        for dest_name, info in sorted_dests:
                            if "Service terminé" in dest_name: rows_html += f'<div class="service-box">😴 Service terminé</div>'
                            else:
                                html_list = []
                                contains_last = False; last_val_tri = 9999
                                for idx, d_item in enumerate(info['items']):
                                    val_tri = d_item['tri']
                                    if idx > 0 and val_tri > 62 and not is_noctilien: continue
                                    txt = d_item['html']
                                    if d_item.get('is_last'):
                                        contains_last = True; last_val_tri = val_tri
                                        if val_tri < 60: txt = f"<span style='border: 1px solid #f1c40f; border-radius: 4px; padding: 0 4px; color: #f1c40f;'>{txt} 🏁</span>"
                                        else: txt += " <span style='opacity:0.7; font-size:0.9em'>🏁</span>"
                                    html_list.append(txt)
                                if not html_list and info['items']: html_list.append(info['items'][0]['html'])
                                times_str = "<span class='time-sep'>|</span>".join(html_list)
                                if contains_last and len(html_list) == 1 and last_val_tri < 10:
                                     rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='bus-row'><span class='bus-dest'>➜ {dest_name}</span><span>{times_str}</span></div></div>"""
                                else: rows_html += f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'
                    
                    if code == "C1":
                         target_date = datetime(2025, 12, 13, 11, 0, 0, tzinfo=pytz.timezone('Europe/Paris'))
                         now = datetime.now(pytz.timezone('Europe/Paris'))
                         if target_date > now:
                             delta = target_date - now
                             st.markdown("""<style>@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } } .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }</style>""", unsafe_allow_html=True)
                             st.markdown(f"""<div style="background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(47, 128, 237, 0.3); border: 1px solid rgba(255,255,255,0.2);"><div style="font-size: 1.1em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><span class='cable-icon'>🚠</span> Câble C1 • A l'approche...</div><div style="font-size: 2.5em; font-weight: 900; line-height: 1.1;">J-{delta.days}</div><div style="font-size: 0.9em; opacity: 0.9; font-style: italic; margin-top: 5px;">Inauguration le 13 décembre 2025 à 11h</div></div>""", unsafe_allow_html=True)

                    st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>{rows_html}</div>""", unsafe_allow_html=True)

    # 7. FOOTER
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
                    sorted_codes = sorted(items.keys(), key=lambda x: (0, int(x)) if x.isdigit() else (1, x))
                    for code in sorted_codes:
                        color = items[code]
                        html_badges += f'<span class="line-badge footer-badge" style="background-color:#{color};">{code}</span>'
                    if html_badges:
                        st.markdown(f"""<div class="footer-container"><span class="footer-icon">{ICONES_TITRE[mode]}</span><div>{html_badges}</div></div>""", unsafe_allow_html=True)
if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)
