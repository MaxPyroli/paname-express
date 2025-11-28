import streamlit as st
import requests
from datetime import datetime
import re
import time
import pytz
import os
from PIL import Image
import base64

# ... tes imports existants ...

# FONCTION POUR CHARGER LA POLICE LOCALE
def charger_police_locale(file_path, font_name):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        css = f"""
            <style>
            @font-face {{
                font-family: '{font_name}';
                src: url('data:font/otf;base64,{b64}') format('opentype');
                /* Si c'est du .ttf, remplacer 'opentype' par 'truetype' et 'otf' par 'ttf' */
            }}
            
            /* Appliquer la police à toute l'app */
            html, body, [class*="css"] {{
                font-family: '{font_name}', sans-serif !important;
            }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        # Si le fichier n'est pas là, on ne fait rien (police par défaut)
        pass

# ... suite du code ...

# APPEL DE LA FONCTION (A mettre juste après st.set_page_config)
st.set_page_config(...) # Ta config actuelle

charger_police_locale("GrandParis-Regular.otf", "Grand Paris") # Nom de ton fichier ici

# ==========================================
#              CONFIGURATION
# ==========================================
try:
    API_KEY = st.secrets["IDFM_API_KEY"]
except FileNotFoundError:
    API_KEY = "TA_CLE_ICI_SI_BESOIN_EN_LOCAL"

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

try:
    icon_image = Image.open("app_icon.png")
except FileNotFoundError:
    icon_image = "🚆"

st.set_page_config(
    page_title="Grand Paname Express",
    page_icon=icon_image,
    layout="centered"
)

# ==========================================
#              STYLE CSS
# ==========================================
st.markdown("""
<style>
    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1s linear infinite; font-weight: bold; }
    
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
        /* CORRECTION MODE CLAIR : Utilisation de var(--text-color) et bordure semi-transparente */
        border-bottom: 2px solid rgba(128, 128, 128, 0.5); 
        font-size: 20px; font-weight: bold; 
        color: var(--text-color);
        letter-spacing: 1px;
    }
    
    .station-title {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Titre interne (ex: OUEST NANTERRE) */
    .rer-direction {
        margin-top: 12px; 
        font-size: 13px; font-weight: bold; color: #3498db; 
        text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 1px solid #444; 
        padding-bottom: 4px;
        margin-bottom: 0px; /* Collé au prochain élément */
    }
    
    .bus-card, .rail-card {
        background-color: #1a1a1a; 
        padding: 12px; 
        margin-bottom: 15px;
        border-radius: 8px; 
        border-left: 5px solid #666;
        color: #ddd; 
    }

    .bus-row, .rail-row {
        display: flex; justify-content: space-between; 
        padding-top: 8px; padding-bottom: 2px;
        border-top: 1px solid #333; /* Ligne de séparation par défaut */
    }
    
    /* CORRECTION DOUBLES LIGNES : Si une ligne de train suit direct un titre, pas de ligne en haut ! */
    .rer-direction + .rail-row {
        border-top: none;
        padding-top: 8px;
    }
    
    .bus-dest, .rail-dest { color: #ccc; font-size: 15px; font-weight: 500; }
    
    .service-box { 
        text-align: left; padding: 10px 12px; color: #888; font-style: italic; font-size: 0.95em;
        background: rgba(255, 255, 255, 0.05); border-radius: 6px;
        margin-top: 5px; margin-bottom: 5px; border-left: 3px solid #444;
    }
    .service-end { color: #999; font-style: italic; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
#              LOGIQUE MÉTIER
# ==========================================

GEOGRAPHIE_RER = {
    "A": {
        "label_1": "⇦ OUEST (Cergy / Poissy / St-Germain)",
        "mots_1": ["CERGY", "POISSY", "GERMAIN", "RUEIL", "DEFENSE", "DÉFENSE", "VESINET", "VÉSINET", "NANTERRE", "MAISONS", "LAFFITTE", "PECQ", "ACHERES", "GRANDE ARCHE"],
        "term_1": ["CERGY", "POISSY", "GERMAIN"],
        
        "label_2": "⇨ EST (Boissy / Marne-la-Vallée / Torcy)",
        "mots_2": ["MARNE", "BOISSY", "TORCY", "NATION", "VINCENNES", "FONTENAY", "NOISY", "JOINVILLE", "VALLEE", "CHESSY", "VARENNE", "NOGENT", "DISNEY"],
        "term_2": ["CHESSY", "BOISSY"]
    },
    "B": {
        "label_1": "⇧ NORD (Roissy / Mitry)",
        "mots_1": ["GAULLE", "MITRY", "NORD", "AULNAY", "BOURGET", "LA PLAINE", "CLAYE"],
        "term_1": ["GAULLE", "MITRY"],
        
        "label_2": "⇩ SUD (St-Rémy / Robinson)",
        "mots_2": ["REMY", "RÉMY", "ROBINSON", "LAPLACE", "DENFERT", "CITE", "MASSY", "ORSAY", "BOURG", "CROIX", "GENTILLY", "ARCUEIL", "BAGNEUX"],
        "term_2": ["REMY", "RÉMY", "ROBINSON"]
    },
    "C": {
        "label_1": "⇦ OUEST (Versailles / Pontoise)",
        "mots_1": ["VERSAILLES", "QUENTIN", "PONTOISE", "INVALIDES", "CHAMP", "EIFFEL", "CHAVILLE", "ERMONT", "JAVEL", "ALMA", "VELIZY", "BEAUCHAMP", "MONTIGNY", "ARGENTEUIL"],
        "term_1": ["VERSAILLES", "QUENTIN", "PONTOISE"],
        
        "label_2": "⇨ SUD/EST (Massy / Dourdan / Étampes)",
        "mots_2": ["MASSY", "DOURDAN", "ETAMPES", "ÉTAMPES", "MARTIN", "JUVISY", "AUSTERLITZ", "BIBLIOTHEQUE", "ORLY", "RUNGIS", "BRETIGNY", "BRÉTIGNY", "CHOISY", "IVRY", "ATHIS", "SAVIGNY"],
        "term_2": ["DOURDAN", "ETAMPES", "ÉTAMPES", "MASSY", "BRÉTIGNY"]
    },
    "D": {
        "label_1": "⇧ NORD (Creil)",
        "mots_1": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS"],
        "term_1": ["CREIL", "ORRY"],
        
        "label_2": "⇩ SUD (Melun / Corbeil)",
        "mots_2": ["MELUN", "CORBEIL", "MALESHERBES", "GARE DE LYON", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"],
        "term_2": ["MELUN", "CORBEIL", "MALESHERBES"]
    },
    "E": {
        "label_1": "⇦ OUEST (Nanterre)",
        "mots_1": ["HAUSSMANN", "LAZARE", "MAGENTA", "NANTERRE", "DEFENSE", "DÉFENSE", "ROSA"],
        "term_1": ["NANTERRE", "HAUSSMANN"],
        
        "label_2": "⇨ EST (Chelles / Tournan)",
        "mots_2": ["CHELLES", "TOURNAN", "VILLIERS", "GAGNY", "EMERAINVILLE", "ROISSY", "NOISY", "BONDY"],
        "term_2": ["CHELLES", "TOURNAN"]
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
    if "RER" in m: return "RER"
    # AJOUT DES TER ICI
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
    
    if delta > 120:
         return (3000, "<span class='service-end'>Service terminé</span>")

    if delta <= 0:
        return (0, "<span class='text-red'>À quai</span>")
    if delta == 1:
        return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5:
        return (delta, f"<span class='text-orange'>{delta} min</span>")
    
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
        except:
            return [0]
            
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

st.title("🚆 Grand Paname")
st.caption("v0.10.1 - Milk")

with st.sidebar:
    st.header("v0.10.1 - Milk") 
    st.header("🗄️ Informations")
    st.markdown("---")
    with st.expander("📜 Historique des versions"):
        notes_history = get_all_changelogs()
        for i, note in enumerate(notes_history):
            st.markdown(note)
            if i < len(notes_history) - 1: st.divider()

# --- GESTION DE LA RECHERCHE ---
if 'selected_stop' not in st.session_state:
    st.session_state.selected_stop = None
    st.session_state.selected_name = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

# Variables pour l'astuce du clavier mobile (Key Hack)
if 'search_key' not in st.session_state:
    st.session_state.search_key = 0
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

with st.form("search_form"):
    # On utilise une clé dynamique (search_key) pour le widget.
    # Quand on change cette clé après la recherche, Streamlit recrée le champ
    # texte à neuf, ce qui lui fait perdre le "focus" et ferme le clavier !
    search_query = st.text_input(
        "🔍 Rechercher une station :", 
        placeholder="Ex: Noisiel, Saint-Lazare...",
        value=st.session_state.last_query, 
        key=f"search_input_{st.session_state.search_key}"
    )
    submitted = st.form_submit_button("Rechercher")

if submitted and search_query:
    st.session_state.last_query = search_query 
    
    with st.spinner("Recherche des arrêts..."):
        data = demander_api(f"places?q={search_query}")
        
        if data and 'places' in data:
            opts = {}
            for p in data['places']:
                if 'stop_area' in p:
                    ville = p.get('administrative_regions', [{}])[0].get('name', '')
                    label = f"{p['name']} ({ville})" if ville else p['name']
                    opts[label] = p['stop_area']['id']
            st.session_state.search_results = opts
        else:
            st.warning("Aucun résultat trouvé.")
            st.session_state.search_results = {}
    
    # ASTUCE CLAVIER MOBILE : Changement de clé + Rerun
    st.session_state.search_key += 1
    st.rerun()

# Affichage du menu déroulant s'il y a des résultats en mémoire
if st.session_state.search_results:
    opts = st.session_state.search_results
    choice = st.selectbox("Résultats trouvés :", list(opts.keys()))
    
    if choice:
        stop_id = opts[choice]
        # Mise à jour si changement
        if st.session_state.selected_stop != stop_id:
            st.session_state.selected_stop = stop_id
            st.session_state.selected_name = choice
            st.rerun()

# ========================================================
#                  AFFICHAGE LIVE
# ========================================================
@st.fragment(run_every=15)
def afficher_tableau_live(stop_id, stop_name):
    
    clean_name = stop_name.split('(')[0].strip()
    st.markdown(f"<div class='station-title'>📍 {clean_name}</div>", unsafe_allow_html=True)
    
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    st.caption(f"Dernière mise à jour : {heure_actuelle} 🔴 LIVE")

    # 1. Récupération des lignes théoriques
    data_lines = demander_lignes_arret(stop_id)
    all_lines_at_stop = {} 
    if data_lines and 'lines' in data_lines:
        for line in data_lines['lines']:
            # Correction robuste du mode
            raw_mode = "AUTRE"
            if 'physical_modes' in line and line['physical_modes']:
                raw_mode = line['physical_modes'][0].get('id', 'AUTRE')
            elif 'physical_mode' in line:
                raw_mode = line['physical_mode']
            
            mode = normaliser_mode(raw_mode)
            code = clean_code_line(line.get('code', '?')) 
            color = line.get('color', '666666')
            all_lines_at_stop[(mode, code)] = {'color': color}

    # 2. Récupération temps réel (Count 600)
    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=600")
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}

    if data_live and 'departures' in data_live:
        for d in data_live['departures']:
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

            cle = (mode, code, color)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri})

    # 2.1 RECUPERATION DES LIGNES MANQUANTES ("GHOST LINES")
    MODES_NOBLES = ["RER", "TRAIN", "METRO", "CABLE", "TRAM"]
    
    for (mode_t, code_t), info_t in all_lines_at_stop.items():
        if mode_t in MODES_NOBLES:
            exists_in_buckets = False
            if mode_t in buckets:
                for (b_mode, b_code, b_color) in buckets[mode_t]:
                    if b_code == code_t:
                        exists_in_buckets = True
                        break
            
            if not exists_in_buckets:
                cle_ghost = (mode_t, code_t, info_t['color'])
                if mode_t not in buckets: buckets[mode_t] = {}
                buckets[mode_t][cle_ghost] = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000}]
    
    # 2.5 FILTRAGE
    for mode in list(buckets.keys()):
        keys_to_remove = []
        for cle in buckets[mode]:
            code_clean = cle[1]
            color_clean = cle[2]
            departs = buckets[mode][cle]
            has_active = any(d['tri'] < 3000 for d in departs)
            
            if has_active:
                displayed_lines_keys.add((mode, code_clean))
            else:
                if mode == "BUS":
                    keys_to_remove.append(cle)
                    footer_data[mode][code_clean] = color_clean
                else:
                    displayed_lines_keys.add((mode, code_clean))
        
        for k in keys_to_remove:
            del buckets[mode][k]

    # 3. Affichage Tableau
    ordre_affichage = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    has_data = False

    for mode_actuel in ordre_affichage:
        lignes_du_mode = buckets[mode_actuel]
        if not lignes_du_mode: continue
            
        has_data = True
        st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)

        def sort_key(k): 
            try: return (0, int(k[1])) 
            except: return (1, k[1])
        
        for cle in sorted(lignes_du_mode.keys(), key=sort_key):
            _, code, color = cle
            departs = lignes_du_mode[cle]
            
            proches = [d for d in departs if d['tri'] < 3000]
            if not proches:
                 proches = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000}]

            # ===========================================================
            # CAS 1 : RER/TRAIN AVEC GÉOGRAPHIE
            # ===========================================================
            if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                # CONSTRUCTION HTML UNIQUE POUR ÉVITER LES BUGS D'AFFICHAGE
                card_html = f"""
                <div class="rail-card" style="border-left-color: #{color};">
                    <div style="display:flex; align-items:center; margin-bottom:5px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """
                
                geo = GEOGRAPHIE_RER[code]
                stop_upper = clean_name.upper()
                is_term_1 = any(t in stop_upper for t in geo.get('term_1', []))
                is_term_2 = any(t in stop_upper for t in geo.get('term_2', []))
                
                real_proches = [d for d in departs if d['tri'] < 3000]
                
                p1 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_1'])]
                p2 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_2'])]
                p3 = [d for d in real_proches if d not in p1 and d not in p2]
                
                def build_rer_group(titre, liste_proches):
                    html_output = f"<div class='rer-direction'>{titre}</div>"
                    if not liste_proches:
                        html_output += f"""<div class="service-box">😴 Service terminé</div>"""
                    else:
                        liste_proches.sort(key=lambda x: x['tri'])
                        for item in liste_proches[:4]:
                            # Pas de séparateur ici, le CSS s'en charge (border-top)
                            html_output += f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div>"""
                    return html_output

                if not p1 and not p2:
                     card_html += """<div class="service-box">😴 Service terminé pour les directions principales</div>"""
                else:
                    if not is_term_1: card_html += build_rer_group(geo['label_1'], p1)
                    if not is_term_2: card_html += build_rer_group(geo['label_2'], p2)

                if p3: card_html += build_rer_group("AUTRES DIRECTIONS", p3)

                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # ===========================================================
            # CAS 2 : TRAINS/RER SANS GÉOGRAPHIE
            # ===========================================================
            elif mode_actuel in ["RER", "TRAIN"]:
                card_html = f"""
                <div class="rail-card" style="border-left-color: #{color};">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """
                
                real_proches = [d for d in departs if d['tri'] < 3000]
                
                if not real_proches:
                     card_html += f"""<div class="service-box">😴 Service terminé</div>"""
                else:
                    real_proches.sort(key=lambda x: x['tri'])
                    for item in real_proches[:4]:
                        card_html += f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div>"""
                
                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # ===========================================================
            # CAS 3 : TOUS LES AUTRES MODES
            # ===========================================================
            else:
                dest_data = {}
                for d in proches:
                    dn = d['dest']
                    if dn not in dest_data: 
                        dest_data[dn] = {'html': [], 'best_time': 9999}
                    
                    if len(dest_data[dn]['html']) < 3:
                        dest_data[dn]['html'].append(d['html'])
                        if d['tri'] < dest_data[dn]['best_time']:
                            dest_data[dn]['best_time'] = d['tri']
                
                sorted_dests = sorted(dest_data.items(), key=lambda item: item[1]['best_time'])
                
                rows_html = ""
                for dest_name, info in sorted_dests:
                    times = info['html']
                    if "Service terminé" in dest_name:
                        rows_html += f'<div class="service-box">😴 Service terminé</div>'
                    else:
                        times_str = "<span class='time-sep'>|</span>".join(times)
                        rows_html += f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'
                
                st.markdown(f"""
                <div class="bus-card" style="border-left-color: #{color};">
                    <div style="display:flex; align-items:center;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                    {rows_html}
                </div>
                """, unsafe_allow_html=True)

    # 4. Footer Intelligent (Final Clean)
    for (mode_theo, code_theo), info in all_lines_at_stop.items():
        if (mode_theo, code_theo) not in displayed_lines_keys:
            if mode_theo not in footer_data: footer_data[mode_theo] = {}
            footer_data[mode_theo][code_theo] = info['color']

    count_visible = 0
    for m in footer_data:
        if m != "AUTRE":
            count_visible += len(footer_data[m])

    if count_visible > 0:
        st.markdown("<div style='margin-top: 30px; border-top: 1px solid #333; padding-top: 15px;'></div>", unsafe_allow_html=True)
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
                    st.markdown(f"""
                    <div class="footer-container">
                        <span class="footer-icon">{ICONES_TITRE[mode]}</span>
                        <div>{html_badges}</div>
                    </div>
                    """, unsafe_allow_html=True)

    if not has_data and count_visible == 0:
        st.info("Aucune information trouvée pour cet arrêt.")

if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)
