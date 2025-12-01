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

# 1. CONFIGURATION
st.set_page_config(
    page_title="Grand Paname (v1.0 Bêta)",
    page_icon=icon_image,
    layout="centered"
)

# 2. FONCTION POLICE
def charger_police_locale(file_path, font_name):
    if not os.path.exists(file_path): return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.split('.')[-1].lower()
        format_str = "opentype" if ext == "otf" else "truetype"
        css = f"""
            <style>
            @font-face {{ font-family: '{font_name}'; src: url('data:font/{ext};base64,{b64}') format('{format_str}'); }}
            html, body {{ font-family: '{font_name}', sans-serif; }}
            h1, h2, h3, h4, h5, h6, p, a, li, button, input, label, textarea {{ font-family: '{font_name}', sans-serif !important; }}
            .stMarkdown, .stButton, .stTextInput, .stSelectbox {{ font-family: '{font_name}', sans-serif !important; }}
            .streamlit-expanderHeader {{ font-family: '{font_name}', sans-serif !important; }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except: pass

charger_police_locale("GrandParis.otf", "Grand Paris")

# ==========================================
#              STYLE CSS
# ==========================================
st.markdown("""
<style>
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
    
    /* STYLE STANDARD (Gare Simple) */
    .station-title {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* NOUVEAU STYLE : SUPER PÔLE (Premium) */
    .station-title-pole {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        /* Dégradé Violet/Or + Bordure Dorée */
        background: linear-gradient(135deg, #662D8C 0%, #ED1E79 100%);
        padding: 12px; border-radius: 10px; 
        box-shadow: 0 4px 20px rgba(237, 30, 121, 0.4);
        border: 2px solid #FDB931;
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
    
    .version-badge {
        background: linear-gradient(45deg, #FF4B4B, #F76B1C); color: white; padding: 4px 10px; border-radius: 15px;
        font-size: 0.6em; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2); vertical-align: middle; margin-left: 10px;
    }
    
    .origin-badge {
        font-size: 0.85em; font-weight: normal; color: #aaa; margin-left: 10px; font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
#           CONFIGURATION DES PÔLES
# ==========================================
POLES_CONFIGURATION = {
    # --- CHÂTELET / LES HALLES ---
    "stop_area:IDFM:474151": "CHATELET",
    "stop_area:IDFM:71264":  "CHATELET",
    "stop_area:IDFM:73794":  "CHATELET",
    
    # --- SAINT-LAZARE / OPÉRA / AUBER / HAUSSMANN ---
    # Gare Saint-Lazare (M3, 12, 13, 14, J, L)
    "stop_area:IDFM:71370":  "ST_LAZARE", 
    # Haussmann St-Lazare (RER E)
    "stop_area:IDFM:73688":  "ST_LAZARE", 
    # Auber (RER A)
    "stop_area:IDFM:478926": "ST_LAZARE", 
    # Saint-Augustin (M9)
    "stop_area:IDFM:73690":  "ST_LAZARE", 
    
    # --- OPÉRA & HAVRE-CAUMARTIN (Tes IDs + Standards) ---
    # Tes IDs identifiés :
    "stop_area:IDFM:71337":  "ST_LAZARE", # Opéra (ou Havre selon dataset)
    "stop_area:IDFM:482368": "ST_LAZARE", # Havre-Caumartin
    # Standards de sécurité (au cas où les tiens sont des StopPoints) :
    "stop_area:IDFM:73650":  "ST_LAZARE", # Opéra Standard
    "stop_area:IDFM:73645":  "ST_LAZARE", # Havre-Caumartin Standard

    # --- GARE DU NORD / MAGENTA ---
    "stop_area:IDFM:71410":  "GARE_NORD", 
    "stop_area:IDFM:478733": "GARE_NORD", 
    "stop_area:IDFM:71434":  "GARE_NORD", 
}

POLES_DATA = {
    "CHATELET": {
        "name": "✨ SUPER-PÔLE : CHÂTELET / LES HALLES",
        "ids": ["stop_area:IDFM:474151", "stop_area:IDFM:71264", "stop_area:IDFM:73794"]
    },
    "ST_LAZARE": {
        "name": "✨ SUPER-PÔLE : SAINT-LAZARE / OPÉRA",
        # On met TOUS les IDs potentiels. L'API ignorera ceux qui sont vides.
        "ids": [
            "stop_area:IDFM:71370", # St-Lazare
            "stop_area:IDFM:73688", # Haussmann
            "stop_area:IDFM:478926", # Auber
            "stop_area:IDFM:73690", # St-Augustin
            
            # OPÉRA (M3, M7, M8)
            "stop_area:IDFM:71337", # Ton ID
            "stop_area:IDFM:73650", # Backup Standard
            
            # HAVRE-CAUMARTIN (M3, M9)
            "stop_area:IDFM:482368", # Ton ID
            "stop_area:IDFM:73645"   # Backup Standard
        ]
    },
    "GARE_NORD": {
        "name": "✨ SUPER-PÔLE : GARE DU NORD / MAGENTA",
        "ids": ["stop_area:IDFM:71410", "stop_area:IDFM:478733", "stop_area:IDFM:71434"]
    }
}

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
        "mots_1": ["PONTOISE", "PERSAN", "BEAUMONT", "LUZARCHES", "CREIL", "MONTSOULT", "VALMONDOIS", "SARROUS", "SAINT-LEU"],
        "term_1": ["PONTOISE", "PERSAN", "LUZARCHES", "CREIL"],
        "mots_2": ["PARIS", "NORD"],
        "term_2": ["PARIS", "NORD"]
    },
    "J": {
        "labels": ("⇦ OUEST (Mantes / Gisors / Ermont)", "⇨ PARIS ST-LAZARE"),
        "mots_1": ["MANTES", "JOLIE", "GISORS", "ERMONT", "VERNON", "PONTOISE", "CONFLANS", "BOISSY", "MEULAN"],
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

st.markdown("<h1>🚆 Grand Paname <span class='version-badge'>v1.0 Bêta</span></h1>", unsafe_allow_html=True)

with st.sidebar:
    st.caption("v1.0.0 - Bêta 3 • 🚧 Dev")
    
    # --- MODE DÉVELOPPEUR ---
    st.markdown("---")
    st.subheader("🛠️ Mode Développeur")
    with st.expander("🔎 Trouver un ID de gare"):
        dev_search = st.text_input("Nom de la gare à analyser :", key="dev_search")
        if dev_search:
            dev_data = demander_api(f"places?q={dev_search}")
            if dev_data and 'places' in dev_data:
                for p in dev_data['places']:
                    if 'stop_area' in p:
                        st.text(f"{p['name']} :")
                        st.code(p['stop_area']['id'])
    st.markdown("---")
    # ------------------------

    st.header("🗄️ Informations")
    st.info("**🚀 Bienvenue dans la Bêta 1.0 !**\n\nCeci est une version majeure. Nous testons les Super-Pôles (agrégation de gares).")
    st.markdown("---")
    with st.expander("📜 Historique des versions"):
        notes_history = get_all_changelogs()
        for i, note in enumerate(notes_history):
            st.markdown(note)
            if i < len(notes_history) - 1: st.divider()
    st.markdown("---")
    st.caption("✨ Réalisé à l'aide de l'IA **Gemini**")

# --- GESTION DE LA RECHERCHE ET SESSION ---
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

if 'selected_pole_name' not in st.session_state:
    st.session_state.selected_pole_name = None
if 'selected_pole_ids' not in st.session_state:
    st.session_state.selected_pole_ids = None

with st.form("search_form"):
    search_query = st.text_input(
        "🔍 Rechercher une station :", 
        placeholder="Ex: Noisiel, Châtelet...",
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
        
        opts = {}
        
        # 1. RECHERCHE DANS LES SUPER-PÔLES (Intercepteur)
        query_normalized = search_query.lower()
        for pole_name in POLES_CONFIGURATION:
            pole_target = POLES_CONFIGURATION[pole_name]
            pole_display_name = POLES_DATA[pole_target]['name']
            
            for p_key, p_info in POLES_DATA.items():
                clean_p_name = p_info['name'].replace("✨ SUPER-PÔLE : ", "").lower()
                if query_normalized in clean_p_name or clean_p_name in query_normalized:
                    opts[p_info['name']] = "POLE:" + p_key

        # 2. RECHERCHE CLASSIQUE API
        data = demander_api(f"places?q={search_query}")
        if data and 'places' in data:
            for p in data['places']:
                if 'stop_area' in p:
                    ville = p.get('administrative_regions', [{}])[0].get('name', '')
                    label = f"{p['name']} ({ville})" if ville else p['name']
                    s_id = p['stop_area']['id']
                    if s_id in POLES_CONFIGURATION:
                        pole_key = POLES_CONFIGURATION[s_id]
                        pole_label = POLES_DATA[pole_key]['name']
                        opts[pole_label] = "POLE:" + pole_key
                    else:
                        opts[label] = s_id
        
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
        value = opts[choice]
        
        # CAS 1 : C'EST UN SUPER-PÔLE
        if value.startswith("POLE:"):
            pole_key = value.split("POLE:")[1]
            if st.session_state.selected_pole_name != pole_key:
                st.session_state.selected_pole_name = pole_key
                st.session_state.selected_pole_ids = POLES_DATA[pole_key]['ids']
                st.session_state.selected_stop = None
                st.session_state.selected_name = None
                st.rerun()

        # CAS 2 : C'EST UNE GARE SIMPLE
        else:
            stop_id = value
            if st.session_state.selected_stop != stop_id:
                st.session_state.selected_stop = stop_id
                st.session_state.selected_name = choice
                st.session_state.selected_pole_name = None
                st.session_state.selected_pole_ids = None
                st.rerun()

# ========================================================
#                  AFFICHAGE LIVE (Gare Simple ou Pôle)
# ========================================================
@st.fragment(run_every=15)
def afficher_tableau_live(stop_ids, display_name):
    
    clean_name = display_name.split('(')[0].strip().replace("✨ SUPER-PÔLE : ", "")
    title_class = "station-title-pole" if len(stop_ids) > 1 else "station-title"
    st.markdown(f"<div class='{title_class}'>📍 {clean_name}</div>", unsafe_allow_html=True)
    
    status_area = st.empty()
    status_area.markdown("""<div style='display: flex; align-items: center; color: #888; font-size: 0.8rem; font-style: italic; margin-bottom: 10px;'><span class="custom-loader"></span> Actualisation...</div>""", unsafe_allow_html=True)

    # 1. LIGNES THEORIQUES
    all_lines_at_stop = {} 
    has_c1_cable = False
    is_pole_mode = len(stop_ids) > 1 

    for s_id in stop_ids:
        data_lines = demander_lignes_arret(s_id)
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
                if mode == "CABLE" and code == "C1": has_c1_cable = True

    # 2. TEMPS REEL
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    last_departures_map = {} 

    all_departures = []
    for s_id in stop_ids:
        data_live = demander_api(f"stop_areas/{s_id}/departures?count=600")
        if data_live and 'departures' in data_live:
            for d in data_live['departures']:
                try:
                    stop_name_raw = d['stop_point']['stop_area']['name']
                    stop_name_clean = stop_name_raw.split('(')[0].strip()
                    d['origin_name'] = stop_name_clean
                except: d['origin_name'] = ""
                all_departures.append(d)
    
    if all_departures:
        # Passe 1 : Max
        for d in all_departures:
            info = d['display_informations']
            mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
            code = clean_code_line(info.get('code', '?')) 
            raw_dest = info.get('direction', '')
            if mode == "BUS": dest = raw_dest
            else: dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            freshness = d.get('data_freshness', 'realtime')
            val_tri, _ = format_html_time(d['stop_date_time']['departure_date_time'], freshness)
            if val_tri < 3000:
                key = (mode, code, dest)
                current_max = last_departures_map.get(key, -999999)
                if val_tri > current_max: last_departures_map[key] = val_tri

        # Passe 2 : Buckets
        for d in all_departures:
            info = d['display_informations']
            mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
            code = clean_code_line(info.get('code', '?')) 
            color = info.get('color', '666666')
            raw_dest = info.get('direction', '')
            if mode == "BUS": dest = raw_dest
            else: dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            freshness = d.get('data_freshness', 'realtime')
            val_tri, html_time = format_html_time(d['stop_date_time']['departure_date_time'], freshness)
            if val_tri < -5: continue 

            is_last = False
            if val_tri < 3000:
                key = (mode, code, dest)
                max_val = last_departures_map.get(key)
                if max_val and val_tri == max_val:
                    if mode in ["RER", "TRAIN"]: is_last = True
                    elif val_tri > 60 or datetime.now(pytz.timezone('Europe/Paris')).hour >= 21: is_last = True

            # MODIF IMPORTANTE : On utilise TOUJOURS l'origine si on est en mode Pôle
            origin_key = d['origin_name'] if is_pole_mode else "MAIN"
            
            cle = (mode, code, color, origin_key)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                is_duplicate = False
                for existing in buckets[mode][cle]:
                    if existing['dest'] == dest and existing['tri'] == val_tri:
                        is_duplicate = True; break
                if not is_duplicate:
                    buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri, 'is_last': is_last, 'origin': origin_key})

    # 2.1 GHOST LINES
    MODES_NOBLES = ["RER", "TRAIN", "METRO", "CABLE", "TRAM"]
    for (mode_t, code_t), info_t in all_lines_at_stop.items():
        if mode_t in MODES_NOBLES:
            if code_t in ["TER", "R"]: continue
            exists_in_buckets = False
            if mode_t in buckets:
                for cle_bucket in buckets[mode_t]:
                    if cle_bucket[1] == code_t: exists_in_buckets = True; break
            if not exists_in_buckets:
                cle_ghost = (mode_t, code_t, info_t['color'], "MAIN")
                if mode_t not in buckets: buckets[mode_t] = {}
                if cle_ghost not in buckets[mode_t]:
                    buckets[mode_t][cle_ghost] = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]
    
    # 2.5 FILTRAGE
    for mode in list(buckets.keys()):
        keys_to_remove = []
        for cle in buckets[mode]:
            code_clean = cle[1]; color_clean = cle[2]
            departs = buckets[mode][cle]
            has_active = any(d['tri'] < 3000 for d in departs)
            if has_active: displayed_lines_keys.add((mode, code_clean))
            else:
                if mode == "BUS": keys_to_remove.append(cle); footer_data[mode][code_clean] = color_clean
                else: displayed_lines_keys.add((mode, code_clean))
        for k in keys_to_remove: del buckets[mode][k]

    # UPDATE STATUT
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    status_area.caption(f"Dernière mise à jour : {heure_actuelle} 🔴 LIVE")

    # 3. AFFICHAGE
    ordre_affichage = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    has_data = len(all_departures) > 0

    for mode_actuel in ordre_affichage:
        lignes_du_mode = buckets[mode_actuel]
        if not lignes_du_mode: continue
        
        has_data = True
        st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)

        def sort_key(k): 
            try: code_val = (0, int(k[1])) 
            except: code_val = (1, k[1])
            return (code_val, k[3])
        
        for cle in sorted(lignes_du_mode.keys(), key=sort_key):
            mode, code, color, origin = cle
            departs = lignes_du_mode[cle]
            proches = [d for d in departs if d['tri'] < 3000]
            if not proches: proches = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]

            # Badge Gare (MODIF : Autorisé pour TOUS les modes en Super-Pôle)
            station_badge = ""
            if is_pole_mode and origin != "MAIN":
                station_badge = f"<span class='origin-badge'>{origin}</span>"

            # === CAS 1 : RER ET TRAINS AVEC GÉOGRAPHIE ===
            if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span>{station_badge}</div>"""
                
                geo = GEOGRAPHIE_RER[code]
                stop_upper = clean_name.upper()
                
                local_mots_1 = geo['mots_1'].copy()
                local_mots_2 = geo['mots_2'].copy()
                
                if code == "C":
                    zone_nord_ouest = ["MAILLOT", "PEREIRE", "CLICHY", "ST-OUEN", "GENNEVILLIERS", "ERMONT", "PONTOISE", "FOCH", "MARTIN", "BOULAINVILLIERS", "KENNEDY", "JAVEL", "GARIGLIANO"]
                    if any(k in stop_upper for k in zone_nord_ouest):
                        if "INVALIDES" in local_mots_1: local_mots_1.remove("INVALIDES")
                        if "INVALIDES" not in local_mots_2: local_mots_2.append("INVALIDES")

                p1 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_1)]
                p2 = [d for d in proches if any(k in d['dest'].upper() for k in local_mots_2)]
                p3 = [d for d in proches if d not in p1 and d not in p2]
                
                is_term_1 = any(k in stop_upper for k in geo['term_1'])
                is_term_2 = any(k in stop_upper for k in geo['term_2'])
                
                def render_group(titre, items):
                    h = f"<div class='rer-direction'>{titre}</div>"
                    items.sort(key=lambda x: x['tri'])
                    for it in items[:4]:
                        if it.get('is_last'):
                            h += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div></div>"""
                        else:
                            h += f"""<div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div>"""
                    return h

                directions_vides = (not p1 and not p2)
                if directions_vides: card_html += """<div class="service-box">😴 Service terminé</div>"""
                else:
                    if not is_term_1: card_html += render_group(geo['labels'][0], p1)
                    if not is_term_2: card_html += render_group(geo['labels'][1], p2)

                has_real_trains_in_p3 = any(d['tri'] < 3000 for d in p3)
                if p3:
                    if directions_vides and not has_real_trains_in_p3: pass 
                    else: card_html += render_group("AUTRES DIRECTIONS", p3)

                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # === CAS 2 : TRAINS/RER SANS GÉOGRAPHIE (BACKUP) ===
            elif mode_actuel in ["RER", "TRAIN"]:
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:10px;"><span class="line-badge" style="background-color:#{color};">{code}</span>{station_badge}</div>"""
                if not proches or (len(proches)==1 and proches[0]['tri']==3000):
                     card_html += f"""<div class="service-box">😴 Service terminé</div>"""
                else:
                    proches.sort(key=lambda x: x['tri'])
                    for item in proches[:4]:
                        if item.get('is_last'):
                            card_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div></div>"""
                        else:
                            card_html += f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div>"""
                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # === CAS 3 : TOUS LES AUTRES MODES ===
            else:
                dest_data = {}
                for d in proches:
                    dn = d['dest']
                    if dn not in dest_data: dest_data[dn] = {'items': [], 'best_time': 9999}
                    if len(dest_data[dn]['items']) < 3:
                        dest_data[dn]['items'].append(d)
                        if d['tri'] < dest_data[dn]['best_time']: dest_data[dn]['best_time'] = d['tri']
                
                if mode_actuel in ["METRO", "TRAM", "CABLE"]:
                    sorted_dests = sorted(dest_data.items(), key=lambda item: item[0])
                else:
                    sorted_dests = sorted(dest_data.items(), key=lambda item: item[1]['best_time'])
                
                is_noctilien = str(code).strip().upper().startswith('N')

                rows_html = ""
                for dest_name, info in sorted_dests:
                    if "Service terminé" in dest_name:
                        rows_html += f'<div class="service-box">😴 Service terminé</div>'
                    else:
                        html_list = []
                        contains_last = False
                        last_val_tri = 9999
                        for idx, d_item in enumerate(info['items']):
                            val_tri = d_item['tri']
                            if idx > 0 and val_tri > 62 and not is_noctilien: continue
                            txt = d_item['html']
                            if d_item.get('is_last'):
                                contains_last = True
                                last_val_tri = val_tri
                                if val_tri < 60:
                                    if val_tri < 30: txt = f"<span style='border: 1px solid #f1c40f; border-radius: 4px; padding: 0 4px; color: #f1c40f;'>{txt} 🏁</span>"
                                    else: txt += " <span style='opacity:0.7; font-size:0.9em'>🏁</span>"
                            html_list.append(txt)
                        if not html_list and info['items']: html_list.append(info['items'][0]['html'])
                        times_str = "<span class='time-sep'>|</span>".join(html_list)
                        
                        if contains_last and len(html_list) == 1 and last_val_tri < 10:
                             rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ (Imminent)</span><div class='bus-row'><span class='bus-dest'>➜ {dest_name}</span><span>{times_str}</span></div></div>"""
                        else:
                            rows_html += f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'
                
                if code == "C1":
                    target_date = datetime(2025, 12, 13, 11, 0, 0, tzinfo=pytz.timezone('Europe/Paris'))
                    now = datetime.now(pytz.timezone('Europe/Paris'))
                    if target_date > now:
                        delta = target_date - now
                        st.markdown("""<style>@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } } .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }</style>""", unsafe_allow_html=True)
                        st.markdown(f"""<div style="background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(47, 128, 237, 0.3); border: 1px solid rgba(255,255,255,0.2);"><div style="font-size: 1.1em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><span class='cable-icon'>🚠</span> Câble C1 • A l'approche...</div><div style="font-size: 2.5em; font-weight: 900; line-height: 1.1;">J-{delta.days}</div><div style="font-size: 0.9em; opacity: 0.9; font-style: italic; margin-top: 5px;">Inauguration le 13 décembre 2025 à 11h</div></div>""", unsafe_allow_html=True)

                st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span>{station_badge}</div>{rows_html}</div>""", unsafe_allow_html=True)

    # 4. FOOTER & MESSAGES
    for (mode_theo, code_theo), info in all_lines_at_stop.items():
        if (mode_theo, code_theo) not in displayed_lines_keys:
            if mode_theo not in footer_data: footer_data[mode_theo] = {}
            footer_data[mode_theo][code_theo] = info['color']
    count_visible = sum(len(footer_data[m]) for m in footer_data if m != "AUTRE")

    if not has_data:
        if count_visible > 0:
            st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(52, 152, 219, 0.1); border-radius: 10px; margin-top: 20px; margin-bottom: 20px;'><h3 style='margin:0; color: #3498db;'>😴 Aucun départ immédiat</h3><p style='margin-top:5px; color: #888;'>Les lignes ci-dessous desservent cet arrêt mais n'ont pas de départ prévu dans les prochaines minutes.</p></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(231, 76, 60, 0.1); border-radius: 10px; margin-top: 20px;'><h3 style='margin:0; color: #e74c3c;'>📭 Aucune information</h3><p style='margin-top:5px; color: #888;'>Aucune donnée temps réel ou théorique trouvée pour cet arrêt.</p></div>""", unsafe_allow_html=True)

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

if st.session_state.selected_pole_ids:
    afficher_tableau_live(st.session_state.selected_pole_ids, POLES_DATA[st.session_state.selected_pole_name]['name'])
elif st.session_state.selected_stop:
    afficher_tableau_live([st.session_state.selected_stop], st.session_state.selected_name)
