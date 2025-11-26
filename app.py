import streamlit as st
import requests
from datetime import datetime
import re
import time
import pytz
import os  # <--- AJOUTER CET IMPORT ICI
from PIL import Image

# ==========================================
#              CONFIGURATION
# ==========================================
# On cherche la clé dans les secrets
try:
    API_KEY = st.secrets["IDFM_API_KEY"]
except FileNotFoundError:
    # Pour le développement local si pas de secrets.toml
    API_KEY = "TA_CLE_ICI_SI_BESOIN_EN_LOCAL"

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"

# --- CHARGEMENT DE L'ICÔNE ---
# Essaie de charger l'image 'app_icon.png' si elle existe, sinon met un émoji
try:
    icon_image = Image.open("app_icon.png") # Assure-toi que le fichier est là !
except FileNotFoundError:
    icon_image = "🚆" # Icône de secours

# CONFIGURATION DE LA PAGE (C'est la seule ligne qui compte vraiment)
st.set_page_config(
    page_title="Grand Paname Express",
    page_icon=icon_image, # On utilise l'image chargée
    layout="centered"
)

# ==========================================
#              STYLE CSS
# ... la suite du code ne change pas ...

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
    /* NOUVEAU : Tag pour les modes sans horaires en bas */
    .small-mode-tag {
        display: inline-block; background: #262730; color: #999;
        padding: 4px 10px; border-radius: 15px; font-size: 11px;
        margin-right: 6px; margin-bottom: 6px; border: 1px solid #444;
    }
    /* --------------------------- */

    /* Séparateur temps */
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

HIERARCHIE = {"RER": 1, "TRAIN": 2, "METRO": 3, "TRAM": 4, "BUS": 5, "AUTRE": 99}

def demander_api(suffixe):
    # (Pas de changement ici, je le mets juste pour le repère)
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/{suffixe}", headers=headers)
        return r.json()
    except: return None

# ----- INSÉRER JUSTE APRÈS LA FONCTION demander_api EXISTANTE -----
def demander_lignes_arret(stop_id):
    """Récupère toutes les lignes desservant un arrêt."""
    headers = {'apiKey': API_KEY.strip()}
    try:
        # On demande les lignes spécifiques à cet arrêt
        r = requests.get(f"{BASE_URL}/stop_areas/{stop_id}/lines", headers=headers)
        return r.json()
    except: return None
# ------------------------------------------------------------------

def normaliser_mode(mode_brut):
    if not mode_brut: return "AUTRE"
    m = mode_brut.upper()
    # Ajout de la détection CABLE
    if "FUNI" in m or "CABLE" in m or "TÉLÉPHÉRIQUE" in m: return "CABLE"
    if "RER" in m: return "RER"
    if "TRAIN" in m or "RAIL" in m or "SNCF" in m or "EXPRESS" in m: return "TRAIN"
    if "METRO" in m or "MÉTRO" in m: return "METRO"
    if "TRAM" in m: return "TRAM"
    if "BUS" in m: return "BUS"
    return "AUTRE"

# ----- REMPLACER LA FONCTION format_html_time -----
def format_html_time(heure_str, data_freshness):
    paris_tz = pytz.timezone('Europe/Paris')
    obj_naive = datetime.strptime(heure_str, '%Y%m%dT%H%M%S')
    obj = paris_tz.localize(obj_naive)
    now = datetime.now(paris_tz)
    delta = int((obj - now).total_seconds() / 60)
    
    if data_freshness == 'base_schedule':
        return (2000, f"<span class='text-blue'>~{obj.strftime('%H:%M')}</span>")
    
    # MODIFICATION ICI : Texte plus court et couleur grise
    if delta > 120:
         return (3000, "<span style='color:#999; font-size:0.9em'>Service terminé</span>")

    if delta <= 0:
        return (0, "<span class='text-red'>À quai</span>")
    if delta == 1:
        return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5:
        return (delta, f"<span class='text-orange'>{delta} min</span>")
    
    return (delta, f"<span class='text-green'>{delta} min</span>")
# --------------------------------------------------
    
    # MODIFICATION ICI : Seuil passé à 120 minutes (2 heures) au lieu de 240
    if delta > 120:
         return (3000, "<span class='text-blue' style='font-size:0.9em'>Service terminé / Lointain</span>")

    if delta <= 0:
        return (0, "<span class='text-red'>À quai</span>")
    if delta == 1:
        return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5:
        return (delta, f"<span class='text-orange'>{delta} min</span>")
    
    return (delta, f"<span class='text-green'>{delta} min</span>")
# --------------------------------------------------
# ----- NOUVELLE FONCTION POUR LIRE L'HISTORIQUE -----
def get_all_changelogs():
    """Lit tous les fichiers .md dans le dossier 'changelogs' et les trie."""
    log_dir = "changelogs"
    all_notes = []
    
    # Vérifie si le dossier existe
    if not os.path.exists(log_dir):
        return ["*Aucune note de version trouvée.*"]
        
    # Liste les fichiers .md
    files = [f for f in os.listdir(log_dir) if f.endswith(".md")]
    
    # Trie inversé pour avoir les versions les plus récentes en premier
    # (Suppose que les fichiers sont nommés v0.8.6.md, v0.8.5.md etc.)
    files.sort(reverse=True)
    
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_notes.append(f.read())
        except Exception as e:
             all_notes.append(f"Erreur de lecture de {filename}: {e}")
             
    return all_notes if all_notes else ["*Aucune note de version trouvée.*"]
# ----------------------------------------------------
# ==========================================
#              INTERFACE GLOBALE
# ==========================================

st.title("🚆 Grand Paname Express")
st.caption("v0.9 - Milk")

with st.sidebar:
    st.header("🗄️ Informations")
    st.markdown("---")
    with st.expander("📜 Historique des versions"):
        notes_history = get_all_changelogs()
        for i, note in enumerate(notes_history):
            st.markdown(note)
            if i < len(notes_history) - 1:
                 st.divider()
# ----------------------------------------------------

# --- GESTION DE LA RECHERCHE ---
# ... la suite du code ...
if 'selected_stop' not in st.session_state:
    st.session_state.selected_stop = None
    st.session_state.selected_name = None

# ----- REMPLACER TOUT LE BLOC DE RECHERCHE PAR CECI -----

# ----- REMPLACER LA LIGNE st.text_input -----
search_query = st.text_input("🔍 Rechercher une gare (tapez puis sélectionnez) :", placeholder="Ex: Noisiel, Châtelet, Funiculaire...")
# --------------------------------------------

if search_query:
    with st.spinner("Recherche des arrêts..."):
        data = demander_api(f"places?q={search_query}")

    if data and 'places' in data:
        opts = {}
        for p in data['places']:
            if 'stop_area' in p:
                ville = p.get('administrative_regions', [{}])[0].get('name', '')
                label = f"{p['name']} ({ville})" if ville else p['name']
                opts[label] = p['stop_area']['id']

        # Le menu déroulant. Si l'utilisateur change la sélection, le script se relance.
        choice = st.selectbox("Résultats trouvés :", list(opts.keys()))

        # V3.3 : Validation immédiate (plus de bouton)
        # Si un choix est fait ET qu'il est différent de celui déjà affiché, on met à jour immédiatement.
        if choice and st.session_state.selected_name != choice:
            st.session_state.selected_stop = opts[choice]
            st.session_state.selected_name = choice
            st.rerun() # Force le rechargement pour afficher le tableau tout de suite
# -------------------------------------------------------

# ========================================================
#        FRAGMENT DYNAMIQUE
# ========================================================

# ----- REMPLACER TOUT LE FRAGMENT (CORRECTIF v1.1.6) -----
@st.fragment(run_every=15)
def afficher_tableau_live(stop_id, stop_name):
    # Nettoyage du nom de la gare
    clean_name = re.sub(r'\s*\(.*?\)$', '', stop_name)
    st.markdown(f"## 📍 {clean_name}")
    
    paris_tz = pytz.timezone('Europe/Paris')
    heure_actuelle = datetime.now(paris_tz).strftime('%H:%M:%S')
    # Utilisation d'un petit conteneur pour aligner le point live et le texte
    st.markdown(f"""
        <div style="display: flex; align-items: center; color: #888; font-size: 0.9em; margin-bottom: 20px;">
            <div class="live-indicator-container">
                <div class="live-indicator"></div>
            </div>
            Dernière M.A.J : {heure_actuelle}
        </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # 1. RÉCUPÉRATION DES DONNÉES THÉORIQUES (Lignes censées passer ici)
    # ============================================================
    data_lines = demander_lignes_arret(stop_id)
    all_lines_at_stop = {} # Clé: (mode, code), Valeur: info {color, name}
    modes_theoriques_presents = set()

    if data_lines and 'lines' in data_lines:
        for line in data_lines['lines']:
            mode = normaliser_mode(line.get('physical_mode', 'AUTRE'))
            code = line.get('code', '?')
            color = line.get('color', '666666')
            name = line.get('name', '')
            all_lines_at_stop[(mode, code)] = {'color': color, 'name': name}
            modes_theoriques_presents.add(mode)

    # ============================================================
    # 2. RÉCUPÉRATION ET TRAITEMENT DES DONNÉES TEMPS RÉEL
    # ============================================================
    data_live = demander_api(f"stop_areas/{stop_id}/departures?count=100")
    
    # Buckets pour grouper les départs temps réel par mode, puis par ligne
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "TRAM": {}, "CABLE": {}, "BUS": {}, "AUTRE": {}}
    
    if data_live and 'departures' in data_live:
        for d in data_live['departures']:
            info = d['display_informations']
            mode = normaliser_mode(info.get('physical_mode', 'AUTRE'))
            code = info.get('code', '?')
            color = info.get('color', '666666')
            
            # Nettoyage de la destination
            raw_dest = info.get('direction', '')
            # Pour les BUS, on garde la ville si elle est entre parenthèses à la fin
            if mode == "BUS":
                 dest = raw_dest
            # Pour les ferrés, on enlève tout ce qui est entre parenthèses à la fin
            else:
                 dest = re.sub(r'\s*\([^)]+\)$', '', raw_dest)
            
            # Calcul du temps d'attente
            freshness = d.get('data_freshness', 'realtime')
            val_tri, html_time = format_html_time(d['stop_date_time']['departure_date_time'], freshness)
            
            # On ignore les trains déjà passés depuis longtemps
            if val_tri < -2: continue 

            # Remplissage des buckets
            cle = (mode, code, color)
            if mode in buckets:
                if cle not in buckets[mode]: buckets[mode][cle] = []
                buckets[mode][cle].append({'dest': dest, 'html': html_time, 'tri': val_tri})


    # ============================================================
    # 3. AFFICHAGE PRINCIPAL (Logique corrigée v1.1.6)
    # ============================================================
    ordre_affichage = ["RER", "TRAIN", "METRO", "TRAM", "CABLE", "BUS", "AUTRE"]
    has_displayed_anything = False

    for mode_actuel in ordre_affichage:
        # On n'affiche le mode que s'il existe en théorie OU s'il y a des données temps réel dessus
        if mode_actuel not in modes_theoriques_presents and not buckets[mode_actuel]:
            continue
            
        # --- AFFICHER LE TITRE DU MODE UNE SEULE FOIS ---
        st.markdown(f"### {ICONES_TITRE[mode_actuel]}")
        st.markdown("---")
        has_displayed_anything = True

        lignes_temps_reel = buckets[mode_actuel]
        codes_temps_reel_vus = set() # Pour identifier les lignes manquantes plus tard

        # --- A) D'ABORD, LES LIGNES AVEC DONNÉES TEMPS RÉEL ---
        if lignes_temps_reel:
            # Fonction de tri pour les numéros de ligne (ex: 1, 2, 10 avant B, C)
            def sort_key_lines(k): 
                try: return (0, int(k[1])) # Tente de convertir le code en nombre
                except: return (1, k[1])    # Sinon tri alphabétique
            
            for cle in sorted(lignes_temps_reel.keys(), key=sort_key_lines):
                _, code, color = cle
                departs = lignes_temps_reel[cle]
                codes_temps_reel_vus.add(code) # On note que cette ligne est affichée

                # On ne garde que les départs "proches" (< 2h) pour l'affichage principal
                proches = [d for d in departs if d['tri'] < 3000]

                # --- MODES URBAINS (BUS, MÉTRO, TRAM...) ---
                if mode_actuel in ["BUS", "METRO", "TRAM", "CABLE", "AUTRE"]:
                    
                    # Si pas de départs proches, on met une ligne "Info indisponible"
                    final_departs = proches if proches else [{'dest': 'Info indisponible / Fin de service', 'html': '<span class="time-no-service">--</span>', 'tri': 3000}]

                    # Regroupement par destination
                    dest_map = {}
                    for d in final_departs:
                        if d['dest'] not in dest_map: dest_map[d['dest']] = []
                        # Max 2 horaires par destination
                        if len(dest_map[d['dest']]) < 2: dest_map[d['dest']].append(d['html'])
                    
                    # Tri alphabétique des destinations
                    sorted_dests = sorted(dest_map.items(), key=lambda i: i[0]) 
                    
                    rows_html = ""
                    for i, (dest_name, times) in enumerate(sorted_dests):
                        times_str = " ".join(times)
                        # Ajout d'une classe 'last-row' à la dernière ligne pour le CSS
                        row_class = "bus-row last-row" if i == len(sorted_dests) - 1 else "bus-row"
                        
                        # Si c'est la ligne "Info indisponible", on grise la destination
                        dest_style_class = "bus-dest bus-dest-no-service" if dest_name.startswith("Info indisponible") else "bus-dest"

                        rows_html += f"""
                        <div class="{row_class}">
                            <span class="{dest_style_class}">→ {dest_name}</span>
                            <span class="bus-time-group">{times_str}</span>
                        </div>
                        """
                    
                    # Affichage du bloc complet pour la ligne
                    st.markdown(f"""
                    <div class="bus-container" style="border-left-color: #{color};">
                        <div class="bus-line-info">
                            <span class="line-badge" style="background-color:#{color};">{code}</span>
                        </div>
                        <div class="bus-rows-container">
                            {rows_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # --- MODES FERROVIAIRES LOURDS (RER, TRAIN) ---
                elif mode_actuel in ["RER", "TRAIN"]:
                    # Configuration géographique (si dispo)
                    geo = GEOGRAPHIE_RER.get(code, {})
                    mots_1 = geo.get('mots_1', [])
                    mots_2 = geo.get('mots_2', [])
                    label_1 = geo.get('label_1', "↔️ DIRECTIONS PRINCIPALES")
                    label_2 = geo.get('label_2', "↔️ AUTRES DIRECTIONS")

                    # Répartition des trains dans les groupes
                    p1 = [d for d in proches if any(k in d['dest'].upper() for k in mots_1)]
                    # Si p1 est rempli, ce qui reste va dans p2. Sinon, tout va dans p1 par défaut.
                    remaining = [d for d in proches if d not in p1]
                    p2 = [d for d in remaining if any(k in d['dest'].upper() for k in mots_2)] if mots_1 else remaining
                    # p3 récupère les miettes s'il y a une config géo complète
                    p3 = [d for d in remaining if d not in p2] if mots_1 and mots_2 else []

                    # Fonction interne pour afficher un groupe de RER
                    def render_rer_group(titre, liste_proches):
                        st.markdown(f"<div class='rer-direction-title'>{titre}</div>", unsafe_allow_html=True)
                        if not liste_proches:
                            st.markdown(f"""
                            <div class="rer-row-container">
                                <div class='rer-row'>
                                    <span class='rer-dest rer-dest-no-service'>Info indisponible / Fin de service</span>
                                    <span class='time-no-service'>--</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            liste_proches.sort(key=lambda x: x['tri'])
                            html_rows = ""
                            # Max 4 trains par direction
                            for item in liste_proches[:4]:
                                html_rows += f"""
                                <div class='rer-row'>
                                    <span class='rer-dest'>{item['dest']}</span>
                                    <span>{item['html']}</span>
                                </div>
                                """
                            st.markdown(f"""<div class="rer-row-container">{html_rows}</div>""", unsafe_allow_html=True)

                    # Affichage du conteneur principal RER
                    st.markdown(f"""
                    <div class="rer-container" style="border-left-color: #{color};">
                        <div class="rer-line-badge-container">
                            <span class="line-badge" style="background-color:#{color};">{code}</span>
                        </div>
                        <div class="rer-content">
                    """, unsafe_allow_html=True)
                    
                    # Logique d'affichage des groupes
                    if not proches:
                        # Cas où aucun train n'est proche
                         st.markdown("""
                            <div class='rer-row' style='color:#888; font-style:italic; padding: 10px 0;'>
                                Info indisponible ou fin de service pour cette ligne.
                            </div>
                            """, unsafe_allow_html=True)
                    elif not mots_1:
                        # Pas de config géo : tout dans le premier groupe
                        render_rer_group(label_1, p1)
                    else:
                        # Config géo présente : on affiche les groupes
                        render_rer_group(label_1, p1)
                        if mots_2 or p2: render_rer_group(label_2, p2)
                        if p3: render_rer_group("AUTRES", p3)

                    st.markdown("</div></div>", unsafe_allow_html=True)

        # --- B) ENSUITE, LES LIGNES THÉORIQUES MANQUANTES ---
        # On cherche les lignes théoriques de ce mode qui n'ont pas été affichées en temps réel
        lignes_manquantes = []
        for (m_t, c_t), info_t in all_lines_at_stop.items():
            if m_t == mode_actuel and c_t not in codes_temps_reel_vus:
                lignes_manquantes.append({'code': c_t, 'color': info_t['color']})
        
        # Si on en trouve, on les affiche comme des blocs "Info indisponible"
        if lignes_manquantes:
            # Tri pour l'affichage
            lignes_manquantes.sort(key=lambda x: (0, int(x['code'])) if x['code'].isdigit() else (1, x['code']))
            
            for ligne in lignes_manquantes:
                 # On utilise le style des BUS/METRO pour la cohérence
                 st.markdown(f"""
                    <div class="bus-container" style="border-left-color: #{ligne['color']};">
                        <div class="bus-line-info">
                            <span class="line-badge" style="background-color:#{ligne['color']};">{ligne['code']}</span>
                            <span class="bus-dest bus-dest-no-service">→ Info indisponible / Fin de service</span>
                        </div>
                        <div class="bus-time"><span class="time-no-service">--</span></div>
                    </div>
                    """, unsafe_allow_html=True)

    # Message si absolument aucune donnée n'a été affichée
    if not has_displayed_anything:
        st.info("Aucune information d'arrêt disponible pour le moment.")
# ------------------------------------------------------------

if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)





















