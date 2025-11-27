import streamlit as st
import requests
from datetime import datetime
import re
import time
import pytz
import os
from PIL import Image

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
    
    /* --- CSS POUR LE FOOTER --- */
    .footer-container {
        display: flex; align-items: center; margin-bottom: 8px;
    }
    .footer-icon {
        margin-right: 10px; font-size: 14px; color: #ccc;
    }
    .footer-badge {
        font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important;
    }
    /* -------------------------- */

    .time-sep { color: #555; margin: 0 8px; font-weight: lighter; }
    
    .section-header {
        margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px;
        border-bottom: 2px solid #444; font-size: 20px; font-weight: bold; color: #eee;
        letter-spacing: 1px;
    }
    
    .station-title {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .rer-direction {
        margin-top: 15px; margin-bottom: 8px; 
        font-size: 13px; font-weight: bold; color: #3498db; 
        text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 1px solid #333; padding-bottom: 2px;
    }
    
    .bus-card {
        background-color: #1a1a1a; padding: 12px; margin-bottom: 10px;
        border-radius: 8px; border-left: 5px solid #666;
    }
    .bus-row {
        display: flex; justify-content: space-between; margin-top: 6px;
        padding-top: 4px; border-top: 1px solid #333;
    }
    .bus-dest { color: #ccc; font-size: 15px; }
    
    .rail-card { margin-bottom: 20px; background-color: #0E1117; }
    .rail-dest { font-weight: 500; font-size: 15px; color: #e0e0e0; }
    .rail-row { display: flex; justify-content: space-between; padding: 4px 0; }
    .rail-sep { border-top: 1px solid #222; margin: 4px 0; }

    /* Style pour "Service terminé" */
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
        "label_2": "⇨ EST (Boissy / Marne-la-Vallée / Torcy)",
        "mots_2": ["MARNE", "BOISSY", "TORCY", "NATION", "VINCENNES", "FONTENAY", "NOISY", "JOINVILLE", "VALLEE", "CHESSY", "VARENNE", "NOGENT", "DISNEY"]
    },
    "B": {
        "label_1": "⇧ NORD (Roissy / Mitry)",
        "mots_1": ["GAULLE", "MITRY", "NORD", "AULNAY", "BOURGET", "LA PLAINE", "CLAYE"],
        "label_2": "⇩ SUD (St-Rémy / Robinson)",
        "mots_2": ["REMY", "RÉMY", "ROBINSON", "LAPLACE", "DENFERT", "CITE", "MASSY", "ORSAY", "BOURG", "CROIX", "GENTILLY", "ARCUEIL", "BAGNEUX"]
    },
    "C": {
        "label_1": "⇦ OUEST (Versailles / Pontoise)",
        "mots_1": ["VERSAILLES", "QUENTIN", "PONTOISE", "INVALIDES", "CHAMP", "EIFFEL", "CHAVILLE", "ERMONT", "JAVEL", "ALMA", "VELIZY", "BEAUCHAMP", "MONTIGNY", "ARGENTEUIL"],
        "label_2": "⇨ SUD/EST (Massy / Dourdan / Étampes)",
        "mots_2": ["MASSY", "DOURDAN", "ETAMPES", "ÉTAMPES", "MARTIN", "JUVISY", "AUSTERLITZ", "BIBLIOTHEQUE", "ORLY", "RUNGIS", "BRETIGNY", "CHOISY", "IVRY", "ATHIS", "SAVIGNY"]
    },
    "D": {
        "label_1": "⇧ NORD (Creil)",
        "mots_1": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS"],
        "label_2": "⇩ SUD (Melun / Corbeil)",
        "mots_2": ["MELUN", "CORBEIL", "MALESHERBES", "GARE DE LYON", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"]
    },
    "E": {
        "label_1": "⇦ OUEST (Nanterre)",
        "mots_1": ["HAUSSMANN", "LAZARE", "MAGENTA", "NANTERRE", "DEFENSE", "DÉFENSE", "ROSA"],
        "label_2": "⇨ EST (Chelles / Tournan)",
        "mots_2": ["CHELLES", "TOURNAN", "VILLIERS", "GAGNY", "EMERAINVILLE", "ROISSY", "NOISY", "BONDY"]
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
    # Modification ici : ajout de "TER" pour les regrouper avec les trains
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
    
    # --- LOGIQUE DE TRI INTELLIGENT (v0.10 > v0.9) ---
    def version_key(filename):
        # Transforme "v0.9.1.md" en [0, 9, 1] pour comparer les nombres et pas le texte
        try:
            clean = filename.lower().replace('v', '').replace('.md', '')
            return [int(part) for part in clean.split('.') if part.isdigit()]
        except:
            return [0]
            
    files.sort(key=version_key, reverse=True)
    # -------------------------------------------------

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
st.caption("v0.9.1 - Milk")

with st.sidebar:
    st.header("🗄️ Informations")
    st.markdown("---")
    with st.expander("📜 Historique des versions"):
        notes_history = get_all_changelogs()
        for i, note in enumerate(notes_history):
            st.markdown(note)
            if i < len(notes_history) - 1: st.divider()

# --- RECHERCHE ---
if 'selected_stop' not in st.session_state:
    st.session_state.selected_stop = None
    st.session_state.selected_name = None

search_query = st.text_input("🔍 Rechercher une gare (tapez puis sélectionnez) :", placeholder="Ex: Noisiel, Châtelet, Funiculaire...")

if search_query:
    if not st.session_state.selected_name or search_query.lower() not in st.session_state.selected_name.lower():
        with st.spinner("Recherche des arrêts..."):
            data = demander_api(f"places?q={search_query}")
        
        if data and 'places' in data:
            opts = {}
            for p in data['places']:
                if 'stop_area' in p:
                    ville = p.get('administrative_regions', [{}])[0].get('name', '')
                    label = f"{p['name']} ({ville})" if ville else p['name']
                    opts[label] = p['stop_area']['id']
            
            choice = st.selectbox("Résultats trouvés :", list(opts.keys()))
            
            if choice and st.session_state.selected_name != choice:
                st.session_state.selected_stop = opts[choice]
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
            mode = normaliser_mode(line.get('physical_mode', 'AUTRE'))
            code = clean_code_line(line.get('code', '?')) 
            color = line.get('color', '666666')
            all_lines_at_stop[(mode, code)] = {'color': color}

    # 2. Récupération temps réel
    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=100")
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "TRAM": {}, "CABLE": {}, "BUS": {}, "AUTRE": {}}
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
            
            # Filtre : on garde les prochains départs
            proches = [d for d in departs if d['tri'] < 3000]
            if not proches:
                 proches = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000}]

            # -----------------------------------------------------------
            # CAS 1 : RER/TRAIN AVEC GÉOGRAPHIE DÉFINIE (A, B, C, D, E)
            # -> Affichage groupé par branches (Nord, Sud, etc.)
            # -----------------------------------------------------------
            if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                st.markdown(f"""
                <div class="rail-card">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                geo = GEOGRAPHIE_RER[code]
                real_proches = [d for d in departs if d['tri'] < 3000]
                
                p1 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_1'])]
                p2 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_2'])]
                p3 = [d for d in real_proches if d not in p1 and d not in p2]
                
                def render_rer_group(titre, liste_proches):
                    st.markdown(f"<div class='rer-direction'>{titre}</div>", unsafe_allow_html=True)
                    if not liste_proches:
                        st.markdown(f"""<div class='rail-row'><span class='service-end'>Service terminé</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                    else:
                        liste_proches.sort(key=lambda x: x['tri'])
                        for item in liste_proches[:4]:
                            st.markdown(f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)

                if not p1 and not p2:
                     st.markdown("""<div class='rail-row' style='text-align:center; margin: 15px 0;'><span class='service-end'>Service terminé pour les directions principales</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                else:
                    render_rer_group(geo['label_1'], p1)
                    render_rer_group(geo['label_2'], p2)

                if p3: render_rer_group("AUTRES DIRECTIONS", p3)

                st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------
            # CAS 2 : TRAINS/RER SANS GÉOGRAPHIE (Ligne H, J, K, TER...)
            # -> Affichage liste simple style RER (ta demande)
            # -----------------------------------------------------------
            elif mode_actuel in ["RER", "TRAIN"]:
                st.markdown(f"""
                <div class="rail-card">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                real_proches = [d for d in departs if d['tri'] < 3000]
                
                if not real_proches:
                     st.markdown(f"""<div class='rail-row'><span class='service-end'>Service terminé</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                else:
                    # On affiche simplement la liste des prochains trains, triés par heure
                    real_proches.sort(key=lambda x: x['tri'])
                    for item in real_proches:
                        st.markdown(f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------
            # CAS 3 : TOUS LES AUTRES MODES (Bus, Métro, Tram, Câble...)
            # -> Affichage compact groupé par destination
            # -----------------------------------------------------------
            else:
                dest_map = {}
                for d in proches:
                    if d['dest'] not in dest_map: dest_map[d['dest']] = []
                    if len(dest_map[d['dest']]) < 3: dest_map[d['dest']].append(d['html'])
                
                sorted_dests = sorted(dest_map.items(), key=lambda i: i[1][0]) 
                
                rows_html = ""
                for dest_name, times in sorted_dests:
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

            # --- AFFICHAGE RER/TRAIN ---
            elif mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                st.markdown(f"""
                <div class="rail-card">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                geo = GEOGRAPHIE_RER[code]
                real_proches = [d for d in departs if d['tri'] < 3000]
                
                p1 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_1'])]
                p2 = [d for d in real_proches if any(k in d['dest'].upper() for k in geo['mots_2'])]
                p3 = [d for d in real_proches if d not in p1 and d not in p2]
                
                def render_rer_group(titre, liste_proches):
                    st.markdown(f"<div class='rer-direction'>{titre}</div>", unsafe_allow_html=True)
                    if not liste_proches:
                        st.markdown(f"""<div class='rail-row'><span class='service-end'>Service terminé</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                    else:
                        liste_proches.sort(key=lambda x: x['tri'])
                        for item in liste_proches[:4]:
                            st.markdown(f"""<div class='rail-row'><span class='rail-dest'>{item['dest']}</span><span>{item['html']}</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)

                if not p1 and not p2:
                     st.markdown("""<div class='rail-row' style='text-align:center; margin: 15px 0;'><span class='service-end'>Service terminé pour les directions principales</span></div><div class='rail-sep'></div>""", unsafe_allow_html=True)
                else:
                    render_rer_group(geo['label_1'], p1)
                    render_rer_group(geo['label_2'], p2)

                if p3: render_rer_group("AUTRES DIRECTIONS", p3)

                st.markdown("</div>", unsafe_allow_html=True)

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
            if mode == "AUTRE": continue # SUPPRESSION DES AUTRES DU FOOTER

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


