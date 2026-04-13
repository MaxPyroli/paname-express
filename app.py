import streamlit as st
from datetime import datetime, timedelta
import re
import time
import pytz
import os
from PIL import Image
import base64
import json
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import streamlit.components.v1 as components

from pwa import rendre_installable
from constants import API_KEY, BASE_URL, HIERARCHIE, GEOGRAPHIE_RER
from utils import get_img_as_base64, generer_icones_html, normaliser_mode, clean_code_line, format_html_time, get_all_changelogs, analyser_importance_arret, synthetiser_alerte, afficher_bandeau_trafic
from api_idfm import demander_api, demander_lignes_arret, demander_arrets_proches, demander_coordonnees_arret, demander_info_trafic
from style import appliquer_style_global
from config import APP_NAME, APP_VERSION, APP_CODENAME, APP_SUBTITLE
from sidebar import initialiser_favoris, afficher_sidebar
from ui_composants import afficher_titre_app, afficher_tuto_bienvenue
from easter_eggs import afficher_popup_feur, afficher_cheval_express
from moteur_live import afficher_tableau_live
from assistant_ia import ouvrir_assistant

# Initialisation des variables de session
if 'search_key' not in st.session_state:
    st.session_state.search_key = 0

ICONES_TITRE = generer_icones_html()

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
# 3. ACTIVATION DU MODE APPLICATION MOBILE (PWA)
rendre_installable()

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
#              INTERFACE GLOBALE
# ==========================================
# --- RECUPERATION DE L'ICONE DU TITRE ---
img_app_b64 = get_img_as_base64("app_icon.png")
if img_app_b64:
    icone_html = f'<img src="data:image/png;base64,{img_app_b64}" style="height: 1em; vertical-align: -0.1em; margin-right: 8px;">'
else:
    icone_html = "<span style='font-size: 1em; vertical-align: middle; margin-right: 8px;'>🚆</span>"

# --- TITRE GÉANT ---
afficher_titre_app(APP_NAME, APP_VERSION, APP_SUBTITLE, icone_html)
initialiser_favoris()
afficher_sidebar()

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
        geo_clicked = st.form_submit_button("📍 Me localiser", use_container_width=True)

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
                        
                        # On garde le nom normal, sans forcer les majuscules
                        nom_affiche = nom
                        
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
                    
                    # On garde le nom normal, sans forcer les majuscules
                    nom_affiche = nom
                    
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

# ========================================================
#           AFFICHAGE LIVE OU ACCUEIL (TUTO)
# ========================================================

# 1. Si une gare est sélectionnée -> On affiche le tableau de bord
if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)

# 2. Sinon -> Tuto de Bienvenue (Construction sécurisée & Couleurs dynamiques)
elif not st.session_state.search_results:
    afficher_tuto_bienvenue()

# ========================================================
#           AFFICHAGE LIVE OU ACCUEIL (TUTO)
# ========================================================

# 1. Si une gare est sélectionnée -> On affiche le tableau de bord
if st.session_state.selected_stop:
    afficher_tableau_live(st.session_state.selected_stop, st.session_state.selected_name)

# 2. Sinon -> Tuto de Bienvenue
elif not st.session_state.search_results:
    afficher_tuto_bienvenue()

# ==========================================
# 🐾 LA BULLE FLOTTANTE DE PANA
# ==========================================
st.markdown(
    """
    <style>
    /* On cible spécifiquement le bouton "Primary" pour le transformer en bulle */
    button[kind="primary"] {
        position: fixed !important;
        bottom: 40px !important;
        right: 40px !important;
        width: 65px !important;
        height: 65px !important;
        border-radius: 50% !important; /* Le rend parfaitement rond */
        font-size: 28px !important;
        background-color: #ff9f43 !important; /* L'orange Pana */
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(255, 159, 67, 0.4) !important;
        z-index: 9999 !important; /* Passe au-dessus de TOUT */
        transition: all 0.3s ease !important;
    }
    
    button[kind="primary"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 20px rgba(255, 159, 67, 0.6) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Le bouton Pana (C'est désormais le SEUL bouton "primary" de l'app)
if st.button("🐾", type="primary", help="Discuter avec Pana"):
    ouvrir_assistant()
