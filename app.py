import streamlit as st
from datetime import datetime, timedelta
import re
import time
import pytz
import os
from PIL import Image
import base64
import json
from streamlit_js_eval import streamlit_js_eval, get_geolocation # <--- La librairie JS robuste
import streamlit.components.v1 as components  # <--- AJOUT INDISPENSABLE
from constants import API_KEY, BASE_URL, HIERARCHIE, GEOGRAPHIE_RER
from utils import get_img_as_base64, generer_icones_html, normaliser_mode, clean_code_line, format_html_time, get_all_changelogs, analyser_importance_arret, synthetiser_alerte, afficher_bandeau_trafic
from api_idfm import demander_api, demander_lignes_arret, demander_arrets_proches, demander_coordonnees_arret, demander_info_trafic
from style import appliquer_style_global
from config import APP_NAME, APP_VERSION, APP_CODENAME, APP_SUBTITLE
# Initialisation des variables de session
if 'search_key' not in st.session_state:
    st.session_state.search_key = 0


# ==========================================
#              CONFIGURATION
# ==========================================

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

# 2. APPLICATION DU STYLE
appliquer_style_global()

# ==========================================
# 🪄 MAGIE : AUTO-FERMETURE DE LA SIDEBAR
# ==========================================
if st.session_state.get('fermer_sidebar', False):
    # On ferme juste la sidebar proprement, sans toucher au scroll !
    streamlit_js_eval(
        js_expressions="window.parent.document.querySelector('[data-testid=\"stSidebar\"] button').click()", 
        key=f"close_sb_{time.time()}"
    )
    st.session_state.fermer_sidebar = False
# ==========================================
#          FONCTIONS UTILITAIRES
# ==========================================
# 1. D'ABORD : La fonction qui lit le fichier (Indispensable qu'elle soit ici)
def get_svg_inline(file_path):
    # Lit le fichier SVG comme du texte pour l'injecter directement
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        
        # Nettoyage : On retire l'entête XML si elle existe pour éviter les bugs d'affichage
        svg_content = re.sub(r'<\?xml.*?\?>', '', svg_content)
        
        # Astuce magique : On force le SVG à utiliser la couleur du texte courant
        # On ajoute une classe pour pouvoir gérer sa taille en CSS
        if '<svg' in svg_content:
            svg_content = svg_content.replace('<svg', '<svg class="mode-icon-inline" fill="currentColor"', 1)
            
        return svg_content
    except Exception as e: 
        return None
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
#              INTERFACE GLOBALE
# ==========================================
# --- RECUPERATION DE L'ICONE DU TITRE ---
img_app_b64 = get_img_as_base64("app_icon.png")
if img_app_b64:
    icone_html = f'<img src="data:image/png;base64,{img_app_b64}" style="height: 1em; vertical-align: -0.1em; margin-right: 8px;">'
else:
    icone_html = "<span style='font-size: 1em; vertical-align: middle; margin-right: 8px;'>🚆</span>"

# --- TITRE GÉANT (Version Finale : Ajustée et sans indentation) ---
st.markdown(f"""
<style>
.titre-geant-custom {{
font-size: clamp(2rem, 9vw, 4rem) !important;
font-weight: 900 !important;
margin: 0 !important;
padding: 0 !important;
line-height: 1.1 !important;
letter-spacing: -1.5px !important;
display: flex !important;
align-items: center !important;
white-space: nowrap !important;
}}
.badge-geant-custom {{
font-size: clamp(0.9rem, 4vw, 1.1rem) !important;
padding: 4px 12px !important;
display: inline-block !important;
}}
.sous-titre-geant-custom {{
color: #aaa !important;
font-style: italic !important;
font-size: clamp(1rem, 4vw, 1.15rem) !important;
}}
</style>

<div style="margin-top: 10px; margin-bottom: 25px; text-align: left;">
<div class="titre-geant-custom">
{icone_html}<span>{APP_NAME}</span>
</div>
<div style="margin-top: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 12px;">
<span class='version-badge badge-geant-custom'>{APP_VERSION}</span>
<span class="sous-titre-geant-custom">{APP_SUBTITLE}</span>
</div>
</div>
""", unsafe_allow_html=True)
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
    st.caption(f"{APP_VERSION} - {APP_CODENAME}")
    
    # 🏠 NOUVEAU : BOUTON ACCUEIL 
    if st.button("🏠 Retour à l'accueil", use_container_width=True, type="secondary"):
        st.session_state.selected_stop = None
        st.session_state.selected_name = None
        st.session_state.search_results = {}
        st.query_params.clear() # 🔗 On efface l'URL !
        st.rerun()
        
    # --- SECTION FAVORIS ---
    st.header("⭐ Mes Favoris")
    
    # Fonction pour charger un favori (inchangée)
    def load_fav(fav_id, fav_name):
        st.session_state.selected_stop = fav_id
        st.session_state.selected_name = fav_name
        st.session_state.search_results = {}
        st.session_state.last_query = ""
        st.session_state.search_key += 1
        
        # 🔗 NOUVEAU : On écrit l'ID de la gare dans l'URL !
        st.query_params["gare"] = fav_id
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
                    
                    # 🪄 NOUVEAU : On dit à l'application de fermer la sidebar au prochain rechargement
                    st.session_state.fermer_sidebar = True 
                    
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
    st.sidebar.success(
        "🎉 **Bienvenue sur Grand Paname V2.0 !**\n\n"
        "Profitez de la nouvelle interface, des alertes trafic intelligentes "
        "et d'une navigation encore plus fluide. Bon voyage ! 🚀"
    )
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

# 🔗 NOUVEAU : LECTURE DE L'URL AU DÉMARRAGE 🔗
if "gare" in st.query_params and st.session_state.selected_stop is None:
    stop_id_url = st.query_params["gare"]
    
    with st.spinner("Chargement de la gare partagée..."):
        # On demande à l'API comment s'appelle cette gare mystère
        data_gare = demander_api(f"stop_areas/{stop_id_url}")
        
        if data_gare and 'stop_areas' in data_gare and len(data_gare['stop_areas']) > 0:
            sa = data_gare['stop_areas'][0]
            nom = sa['name']
            ville = sa.get('administrative_regions', [{}])[0].get('name', '')
            
            # On recrée un joli nom avec la ville
            nom_complet = f"{nom.upper()} ({ville})" if ville else nom.upper()
            
            # On force la sélection
            st.session_state.selected_stop = stop_id_url
            st.session_state.selected_name = nom_complet
            # On n'a pas besoin de rerun, Streamlit va naturellement afficher la gare en descendant le code !
# --- GESTION DE LA RECHERCHE & GÉOLOCALISATION ---
if 'geoloc_active' not in st.session_state:
    st.session_state.geoloc_active = False

# 1. LA BARRE DE RECHERCHE ET LE BOUTON GÉOLOC (Version Claire & Lisible)
with st.form("search_form"):
    search_query = st.text_input(
        "🔍 Rechercher un arrêt :", 
        placeholder="Ex: Noisiel, Saint-Lazare...",
        value=st.session_state.last_query, 
        key=f"search_input_{st.session_state.search_key}"
    )
    
    # On utilise des colonnes pour aligner les boutons.
    # [0.65, 0.35] donne plus de place au bouton de localisation pour son texte.
    col_submit, col_geo = st.columns([0.65, 0.35], gap="small")
    with col_submit:
        # Bouton standard
        submitted = st.form_submit_button("Rechercher", use_container_width=True)
    with col_geo:
        # 📍 Me localiser : L'ajout de texte rend le bouton BEAUCOUP plus lisible.
        # type="primary" le colore pour le mettre en valeur.
        geo_clicked = st.form_submit_button("📍 Me localiser", type="primary", use_container_width=True)

# Si le bouton "Me localiser" est cliqué, on active le mode géoloc
if geo_clicked:
    st.session_state.geoloc_active = True

# 2. LOGIQUE DE GÉOLOCALISATION (Si le bouton 📍 a été cliqué)
if st.session_state.geoloc_active:
    st.info("📡 Recherche de votre position...")
    # La magie opère ici : ça demande l'autorisation au navigateur
    loc = get_geolocation() 
    
    if loc:
        # 🛡️ LE BOUCLIER ANTI-CRASH (Vérification de l'autorisation)
        if 'coords' in loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            with st.spinner("Recherche des arrêts à proximité..."):
                data_proches = demander_arrets_proches(lat, lon, rayon=1500)
            
            resultats_bruts = []
            if data_proches and 'places_nearby' in data_proches:
                for p in data_proches['places_nearby']:
                    if 'stop_area' in p:
                        sa = p['stop_area']
                        nom = sa['name']
                        ville = sa.get('administrative_regions', [{}])[0].get('name', '')
                        
                        # 🔢 LA CORRECTION EST ICI : On force en "int" (nombre entier)
                        distance = int(p.get('distance', 0))
                        
                        # ✨ L'analyse magique (On ignore le tag avec "_")
                        rang, _ = analyser_importance_arret(sa)
                        
                        # Si c'est un mode lourd (RER, Train, Métro, rang <= 3), on met en MAJUSCULES
                        nom_affiche = nom.upper() if rang <= 3 else nom
                        
                        label = f"{nom_affiche} ({ville}) - à {distance}m" if ville else f"{nom_affiche} - à {distance}m"
                        
                        resultats_bruts.append({
                            'label': label,
                            'id': sa['id'],
                            'rang': rang,
                            'distance': distance
                        })
            
            if resultats_bruts:
                # 1. Tri kilométrique strict
                resultats_bruts.sort(key=lambda x: x['distance'])
                
                # 2. Séparation en deux mondes
                gares_lourdes = [r for r in resultats_bruts if r['rang'] <= 3] # RER, Train, Métro
                arrets_legers = [r for r in resultats_bruts if r['rang'] > 3]  # Bus, Tram
                
                # 3. On garde les 10 plus proches de CHAQUE catégorie
                gares_lourdes = gares_lourdes[:10]
                arrets_legers = arrets_legers[:10]
                
               # 4. On crée le menu déroulant SANS les titres (mais on garde l'ordre intelligent)
                opts = {}
                
                # On met d'abord les gares lourdes (s'il y en a)
                for r in gares_lourdes:
                    opts[f"🚇 {r['label']}"] = r['id']
                        
                # Puis on met les arrêts de bus à la suite
                for r in arrets_legers:
                    opts[f"🚌 {r['label']}"] = r['id']
                
                st.session_state.search_results = opts
                st.session_state.geoloc_active = False 
                st.rerun()
            else:
                st.warning("⚠️ Aucune gare trouvée dans un rayon de 1,5km.")
                st.session_state.geoloc_active = False
        else:
            # 🛑 Le navigateur a bloqué ou refusé la position !
            st.warning("⚠️ Accès à la position refusé. Veuillez l'autoriser dans les paramètres de votre navigateur.")
            st.session_state.geoloc_active = False

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
        data = demander_api(f"places?q={search_query}")
        resultats_bruts = []
        
        if data and 'places' in data:
            for p in data['places']:
                if 'stop_area' in p:
                    sa = p['stop_area']
                    nom = sa['name']
                    ville = sa.get('administrative_regions', [{}])[0].get('name', '')
                    # 🔢 LA CORRECTION EST ICI : On force en "int" (nombre entier)
                    distance = int(p.get('distance', 0))
                    
                    # ✨ L'analyse magique
                    rang, _ = analyser_importance_arret(sa)
                    
                    nom_affiche = nom.upper() if rang <= 3 else nom
                    
                    label = f"{nom_affiche} ({ville})" if ville else f"{nom_affiche}"
                    
                    resultats_bruts.append({
                        'label': label,
                        'id': sa['id'],
                        'rang': rang
                    })
        
        if resultats_bruts:
            # ✨ On laisse l'API Navitia faire son tri textuel naturel (pertinence > hiérarchie)
            opts = {r['label']: r['id'] for r in resultats_bruts}
            st.session_state.search_results = opts
        else:
            st.session_state.search_results = {}
            st.session_state.search_error = "⚠️ Aucun résultat trouvé. Essayez un autre nom."
    st.session_state.search_key += 1
    st.rerun()

# 4. AFFICHAGE DES RÉSULTATS (Valable pour recherche ET géoloc)
if st.session_state.search_results:
    opts = st.session_state.search_results
    choice = st.selectbox("Résultats trouvés :", list(opts.keys()))
    
    # 🛑 NOUVEAU : On vérifie que le choix n'est pas un titre de catégorie (qui vaut None)
    if choice and opts.get(choice) is not None:
        stop_id = opts[choice]
        if st.session_state.selected_stop != stop_id:
            st.session_state.selected_stop = stop_id
            
            # On nettoie l'émoji pour le beau titre de la page
            nom_propre = choice.replace("🚇 ", "").replace("🚌 ", "")
            st.session_state.selected_name = nom_propre
            
            # 🔗 On écrit l'ID de la gare dans l'URL
            st.query_params["gare"] = stop_id
            
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
            all_lines_at_stop[(mode, code)] = {'color': color, 'id': line.get('id')}
            
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
                
                # --- INFO TRAFIC ---
                line_id = all_lines_at_stop.get((mode_actuel, code), {}).get('id')
                bandeau_html = afficher_bandeau_trafic(line_id, code) if line_id else ""
                # -------------------

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

                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span>{bandeau_html}</div>"""
                    
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
                    card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:10px;"><span class="line-badge" style="background-color:#{color};">{code}</span>{bandeau_html}</div>"""
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

                    st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span>{bandeau_html}</div>{rows_html}</div>""", unsafe_allow_html=True)
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
    st.markdown(f"<div class='station-title'>{clean_name}</div>", unsafe_allow_html=True)
            
    # --- 🗺️ NOUVEAU : LE BANDEAU CARTE (ÉLÉGANT) ---
    coords_df = demander_coordonnees_arret(stop_id)
    if coords_df is not None:
        # On remet le magnifique st.map natif
        st.map(coords_df, height=150, zoom=14, use_container_width=True)
    # -------------------------------------
    
    # 3. APPEL DU FRAGMENT (Il gère maintenant le Header ET le Bouton)
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
            '<p style="font-size: 1.1em; opacity: 0.8; color: var(--text-color);">Votre compagnon de voyage en Île-de-France.</p>',
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
