import streamlit as st
import requests
from datetime import datetime
import re
import time
import pytz # Nouvelle librairie indispensable

# ==========================================
#              CONFIGURATION
# ==========================================
# On cherche la clé dans les secrets sécurisés de Streamlit
try:
    API_KEY = st.secrets["IDFM_API_KEY"]
except FileNotFoundError:
    st.error("❌ Erreur : Le fichier .streamlit/secrets.toml est introuvable ou la clé est manquante.")
    st.stop()

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

# ==========================================
#              STYLE CSS
# ==========================================
st.markdown("""
<style>
    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1s linear infinite; font-weight: bold; }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); }
        100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }
    }
    .live-dot {
        display: inline-block; width: 10px; height: 10px;
        background-color: #e74c3c; border-radius: 50%;
        margin-right: 8px; animation: pulse 2s infinite;
    }

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
</style>
""", unsafe_allow_html=True)

# ==========================================
#              LOGIQUE MÉTIER
# ==========================================

GEOGRAPHIE_RER = {
    "A": {
        "label_1": "⇦ OUEST (Cergy / Poissy / St-Germain)",
        "mots_1": ["CERGY", "POISSY", "GERMAIN", "RUEIL", "DEFENSE", "DÉFENSE", "VESINET", "VÉSINET", "NANTERRE", "MAISONS", "LAFFITTE", "PECQ", "ACHERES", "GRANDE ARCHE"],
        "label_2": "⇨ EST (Marne-la-Vallée / Boissy / Torcy)",
        "mots_2": ["MARNE", "BOISSY", "TORCY", "NATION", "VINCENNES", "FONTENAY", "NOISY", "JOINVILLE", "VALLEE", "CHESSY", "VARENNE", "NOGENT", "DISNEY"]
    },
    "B": {
        "label_1": "⇧ NORD (Roissy / Mitry / Gare du Nord)",
        "mots_1": ["GAULLE", "MITRY", "NORD", "AULNAY", "BOURGET", "LA PLAINE", "CLAYE"],
        "label_2": "⇩ SUD (St-Rémy / Robinson / Laplace)",
        "mots_2": ["REMY", "RÉMY", "ROBINSON", "LAPLACE", "DENFERT", "CITE", "MASSY", "ORSAY", "BOURG", "CROIX", "GENTILLY", "ARCUEIL", "BAGNEUX"]
    },
    "C": {
        "label_1": "⇦ OUEST (Versailles / Pontoise)",
        "mots_1": ["VERSAILLES", "QUENTIN", "PONTOISE", "INVALIDES", "CHAMP", "EIFFEL", "CHAVILLE", "ERMONT", "JAVEL", "ALMA", "VELIZY", "BEAUCHAMP", "MONTIGNY", "ARGENTEUIL"],
        "label_2": "⇨ SUD/EST (Massy / Dourdan / Juvisy)",
        "mots_2": ["MASSY", "DOURDAN", "ETAMPES", "ÉTAMPES", "MARTIN", "JUVISY", "AUSTERLITZ", "BIBLIOTHEQUE", "ORLY", "RUNGIS", "BRETIGNY", "CHOISY", "IVRY", "ATHIS", "SAVIGNY"]
    },
    "D": {
        "label_1": "⇧ NORD (Creil / Stade de France)",
        "mots_1": ["CREIL", "GOUSSAINVILLE", "ORRY", "VILLIERS", "STADE", "DENIS", "LOUVRES", "SURVILLIERS"],
        "label_2": "⇩ SUD (Melun / Corbeil / Gare de Lyon)",
        "mots_2": ["MELUN", "CORBEIL", "MALESHERBES", "GARE DE LYON", "VILLENEUVE", "COMBS", "FERTE", "LIEUSAINT", "MOISSELLES", "JUVISY"]
    },
    "E": {
        "label_1": "⇦ OUEST (Haussmann / La Défense)",
        "mots_1": ["HAUSSMANN", "LAZARE", "MAGENTA", "NANTERRE", "DEFENSE", "DÉFENSE", "ROSA"],
        "label_2": "⇨ EST (Chelles / Tournan)",
        "mots_2": ["CHELLES", "TOURNAN", "VILLIERS", "GAGNY", "EMERAINVILLE", "ROISSY", "NOISY", "BONDY"]
    }
}

ICONES_TITRE = {
    "RER": "🚆 RER", "TRAIN": "🚆 TRAIN", "METRO": "🚇 MÉTRO", 
    "TRAM": "🚋 TRAMWAY", "BUS": "🚌 BUS", "AUTRE": "🌙 AUTRE"
}

HIERARCHIE = {"RER": 1, "TRAIN": 2, "METRO": 3, "TRAM": 4, "BUS": 5, "AUTRE": 99}

def demander_api(suffixe):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/{suffixe}", headers=headers)
        return r.json()
    except: return None

def normaliser_mode(mode_brut):
    if not mode_brut: return "AUTRE"
    m = mode_brut.upper()
    if "RER" in m: return "RER"
    if "TRAIN" in m or "RAIL" in m or "SNCF" in m or "EXPRESS" in m: return "TRAIN"
    if "METRO" in m or "MÉTRO" in m: return "METRO"
    if "TRAM" in m: return "TRAM"
    if "BUS" in m: return "BUS"
    return "AUTRE"

def format_html_time(heure_str, data_freshness):
    # --- CORRECTION FUSEAU HORAIRE ---
    paris_tz = pytz.timezone('Europe/Paris')
    
    # L'API renvoie l'heure sans info de zone, mais c'est l'heure locale de Paris
    # On force donc l'interprétation en "Paris Time"
    obj_naive = datetime.strptime(heure_str, '%Y%m%dT%H%M%S')
    obj = paris_tz.localize(obj_naive)
    
    # On récupère l'heure actuelle à Paris aussi
    now = datetime.now(paris_tz)
    
    delta = int((obj - now).total_seconds() / 60)
    # ---------------------------------
    
    if data_freshness == 'base_schedule':
        return (2000, f"<span class='text-blue'>~{obj.strftime('%H:%M')}</span>")
    
    if delta <= 0:
        return (0, "<span class='text-red'>À quai</span>")
    if delta == 1:
        return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5:
        return (delta, f"<span class='text-orange'>{delta} min</span>")
    
    return (delta, f"<span class='text-green'>{delta} min</span>")

# ==========================================
#              INTERFACE GLOBALE
# ==========================================

st.title("🚆 Grand Paname")
st.caption("v3.2 - Timezone Fixed")

if 'selected_stop' not in st.session_state:
    st.session_state.selected_stop = None
    st.session_state.selected_name = None

search_query = st.text_input("🔍 Rechercher une gare :", placeholder="Tapez le nom ici...")

if search_query:
    with st.spinner("Recherche..."):
        data = demander_api(f"places?q={search_query}")
    
    if data and 'places' in data:
        opts = {}
        for p in data['places']:
            if 'stop_area' in p:
                ville = p.get('administrative_regions', [{}])[0].get('name', '')
                label = f"{p['name']} ({ville})" if ville else p['name']
                opts[label] = p['stop_area']['id']
        
        choice = st.selectbox("Choisir l'arrêt :", list(opts.keys()))
        
        if st.button("Voir les horaires 🚀", type="primary", use_container_width=True):
            st.session_state.selected_stop = opts[choice]
            st.session_state.selected_name = choice
            st.rerun()

# ========================================================
#        FRAGMENT DYNAMIQUE
# ========================================================
@st.fragment(run_every=15)
def afficher_tableau_live(stop_id, stop_name):
    
    clean_name = stop_name.split('(')[0].strip()
    st.markdown(f"<div class='station-title'>📍 {clean_name}</div>", unsafe_allow_html=True)
    
    # Heure Parisienne pour l'affichage "Dernière mise à jour"
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    st.caption(f"Dernière mise à jour : {heure_actuelle} 🔴 LIVE")

    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=100")
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    
    if data_live and 'departures' in data_live:
        for d in data_live['departures']:
            info = d['display_informations']
            mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
            code = info.get('code', '?')
            color = info.get('color', '666666')
            
            raw_dest = info.get('direction', '')
            if mode == "BUS": dest = raw_dest.split('(')[0]
            else: dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            
            freshness = d.get('data_freshness', 'realtime')
            val_tri, html_time = format_html_time(d['stop_date_time']['departure_date_time'], freshness)
            
            if val_tri < -5: continue 

            cle = (mode, code, color)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri})

    ordre_affichage = ["RER", "TRAIN", "METRO", "TRAM", "BUS", "AUTRE"]
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

            # --- BUS ---
            if mode_actuel == "BUS":
                dest_map = {}
                for d in departs:
                    if d['dest'] not in dest_map: dest_map[d['dest']] = []
                    if len(dest_map[d['dest']]) < 2: dest_map[d['dest']].append(d['html'])
                
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

            # --- RER ---
            elif mode_actuel == "RER" and code in GEOGRAPHIE_RER:
                st.markdown(f"""
                <div class="rail-card">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                geo = GEOGRAPHIE_RER[code]
                p1, p2, p3 = [], [], []
                for d in departs:
                    u = d['dest'].upper()
                    if any(k in u for k in geo['mots_1']): p1.append(d)
                    elif any(k in u for k in geo['mots_2']): p2.append(d)
                    else: p3.append(d)
                
                def render_rer_group(titre, liste):
                    if not liste: return
                    liste.sort(key=lambda x: x['tri'])
                    st.markdown(f"<div class='rer-direction'>{titre}</div>", unsafe_allow_html=True)
                    for item in liste[:4]:
                        st.markdown(f"""
                        <div class='rail-row'>
                            <span class='rail-dest'>{item['dest']}</span>
                            <span>{item['html']}</span>
                        </div>
                        <div class='rail-sep'></div>
                        """, unsafe_allow_html=True)

                render_rer_group(geo['label_1'], p1)
                render_rer_group(geo['label_2'], p2)
                render_rer_group("AUTRES DIRECTIONS", p3)
                st.markdown("</div>", unsafe_allow_html=True)

            # --- STANDARD ---
            else:
                st.markdown(f"""
                <div class="rail-card">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <span class="line-badge" style="background-color:#{color};">{code}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                dest_map = {}
                for d in departs:
                    if d['dest'] not in dest_map: dest_map[d['dest']] = []
                    if len(dest_map[d['dest']]) < 3: dest_map[d['dest']].append(d['html'])
                
                sorted_dests = sorted(dest_map.items(), key=lambda i: i[1][0])
                
                for dest_name, times in sorted_dests:
                    times_str = "<span class='time-sep'>|</span>".join(times)
                    st.markdown(f"""
                    <div class='rail-row'>
                        <span class='rail-dest'>{dest_name}</span>
                        <div style='text-align:right;'>{times_str}</div>
                    </div>
                    <div class='rail-sep'></div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    if not has_data:
        st.info("Aucun passage trouvé ou erreur API.")

if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)
