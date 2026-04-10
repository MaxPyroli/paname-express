import streamlit as st
import urllib.parse
import re

# 1. LA NOUVELLE BIBLIOTHÈQUE GOOGLE (Option B)
from google import genai
from google.genai import types

# 2. L'IMPORT CORRIGÉ (Plus d'erreur ligne 9 !)
from api_idfm import demander_info_trafic, demander_api

# 3. NOUVELLE CONFIGURATION DU CLIENT GOOGLE
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Attention : Clé API introuvable dans st.secrets !")

# ==========================================
# 🧰 OUTIL 1 : INFO TRAFIC
# ==========================================
# ... (garde tes fonctions d'outils exactement comme elles étaient) ...
def outil_info_trafic_ia(nom_ligne: str) -> str:
    """Récupère l'état du trafic en temps réel pour une ligne de métro ou RER."""
    dico_lignes = {
        "1": "line:IDFM:C01371", "2": "line:IDFM:C01372", "3": "line:IDFM:C01373",
        "4": "line:IDFM:C01374", "5": "line:IDFM:C01375", "14": "line:IDFM:C01386",
        "RER A": "line:IDFM:C01742", "RER B": "line:IDFM:C01743" # (Ajoute les autres ici)
    }
    
    nom_propre = str(nom_ligne).upper().replace("LIGNE ", "").strip()
    line_id = dico_lignes.get(nom_propre)
    
    if not line_id:
        return f"Je ne connais pas l'ID de la ligne {nom_ligne}."

    try:
        alertes = demander_info_trafic(line_id, nom_propre)
    except Exception as e:
        return f"Erreur de réseau : {str(e)}"

    if not alertes or len(alertes) == 0:
        return f"Trafic normal sur la ligne {nom_propre}."
    
    rapport = f"Problèmes sur la ligne {nom_propre} :\n"
    for alerte in alertes:
        rapport += f"- {alerte.get('header', 'Alerte')} : {alerte.get('text', '')}\n"
    return rapport

# ==========================================
# 🧰 OUTIL 2 : PROCHAINS DÉPARTS (MODE DEBUG 🕵️‍♂️)
# ==========================================
def outil_prochains_departs_ia(nom_station: str) -> str:
    """Récupère les horaires simplifiés pour l'IA."""
    try:
        import urllib.parse
        nom_station_propre = urllib.parse.quote(nom_station)
        
        # 1. Recherche de la gare
        recherche_data = demander_api(f"places?q={nom_station_propre}")
        if not recherche_data or not recherche_data.get('places'):
            return f"Je ne trouve pas la gare '{nom_station}'."
            
        stop_id = recherche_data['places'][0]['id']
        nom_trouve = recherche_data['places'][0].get('name', nom_station)
        
        # 2. Récupération des départs
        data = demander_api(f"stop_areas/{stop_id}/departures?count=15")
        if not data or not data.get('departures'):
            return f"Aucun départ trouvé pour {nom_trouve}."

        directions_vues = set()
        rapport = f"Voici les prochains départs à {nom_trouve} :\n"
        
        for d in data['departures']:
            info = d['display_informations']
            ligne = info.get('code', '?')
            dest = info.get('direction', 'Inconnue').split('(')[0].strip()
            
            # On ne garde qu'un train par direction
            cle = (ligne, dest)
            if cle not in directions_vues:
                directions_vues.add(cle)
                
                # --- CALCUL DU TEMPS EN MINUTES (100% SÉCURISÉ PARIS) ---
                try:
                    from datetime import datetime
                    import pytz
                    
                    time_raw = d['stop_date_time']['departure_date_time'] # ex: 20260410T153000
                    dep_time = datetime.strptime(time_raw, '%Y%m%dT%H%M%S')
                    
                    # On force le fuseau horaire de Paris sur l'heure du train
                    paris_tz = pytz.timezone('Europe/Paris')
                    dep_time_paris = paris_tz.localize(dep_time)
                    
                    # On prend l'heure actuelle, strictement à Paris aussi
                    now_paris = datetime.now(paris_tz)
                    
                    # Différence en minutes
                    diff = int((dep_time_paris - now_paris).total_seconds() / 60)
                    
                    if diff <= 0:
                        heure_aff = "À quai 🏃‍♂️"
                    elif diff > 90: # Si c'est dans super longtemps
                        heure_aff = f"{diff // 60}h{diff % 60:02d}"
                    else:
                        heure_aff = f"{diff} min"
                except Exception as e:
                    heure_aff = "Bientôt"
                # ---------------------------------------------------------
                
            if len(directions_vues) >= 6: break # On s'arrête à 6 lignes max

        return rapport
        
    except Exception as e:
        # On print l'erreur réelle dans la console Streamlit pour débugger
        print(f"ERREUR CRITIQUE IA : {str(e)}")
        return "Désolé, petit bug technique avec les horaires. Réessaie !"
# ==========================================
# 🧠 LE CERVEAU DE PANA (Personnalité & Config)
# ==========================================
personnalite = """
Tu t'appelles Pana, le petit assistant virtuel tout mignon de l'application Grand Paname. 🦊✨
Tu as une personnalité adorable, très chaleureuse, pétillante et toujours prête à aider.

RÈGLES DE RÉPONSE :
1. Accueille toujours l'utilisateur avec un petit mot mignon et joyeux.
2. Affiche EXACTEMENT la liste fournie par l'outil. Ne modifie pas les chiffres.
3. Fais une liste à puces propre avec les emojis.
4. Finis par une petite phrase adorable et bienveillante pour souhaiter un bon voyage.
5. Reste concis : on veut de la mignonnerie, mais pas de gros pavés de texte.
"""

# 👇 C'EST ICI QUE TU CHANGES LA TEMPÉRATURE 👇
# Plus c'est proche de 0.0 = Robot très strict (bon pour les horaires purs)
# Plus c'est proche de 1.0 = Très bavard et créatif (risque d'inventer)
# 0.4 est le compromis idéal pour Pana !
config_ia = types.GenerateContentConfig(
    system_instruction=personnalite,
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    temperature=0.4  
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE & LE BADGE
# ==========================================
@st.dialog("🤖 Pana") 
def ouvrir_assistant():
    
    # 1. LE STYLE CSS (Largeur de la modale + Design du Badge Orange)
    st.markdown(
        """
        <style>
            div[data-testid="stDialog"] div[role="dialog"] { max-width: 580px !important; }
            .stChatMessage { border-radius: 15px; }
            
            /* Le design de ton badge Bêta orange ! */
            .badge-beta {
                background-color: #ff9f43; /* Un bel orange moderne */
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                font-weight: 800;
                letter-spacing: 0.5px;
                margin-left: 8px;
                box-shadow: 0 2px 4px rgba(255, 159, 67, 0.3);
                vertical-align: middle;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. LE SOUS-TITRE AVEC LE BADGE
    st.markdown(
        "<p style='color: #888; font-size: 0.9em; margin-top: -10px; margin-bottom: 20px;'>"
        "Coucou ! Je suis Pana. Trafic, itinéraires... Je suis là pour toi ! <span class='badge-beta'>BÊTA</span>"
        "</p>", 
        unsafe_allow_html=True
    )

    # 3. LE DÉMARRAGE DU CERVEAU (Il trouvera config_ia car il est défini plus haut !)
    if "chat_session_v4" not in st.session_state:
        st.session_state.chat_session_v4 = client.chats.create(
            model="gemini-3.1-flash-lite-preview", 
            config=config_ia
        )
        
        st.session_state.messages_ia_v4 = [
            {"role": "assistant", "content": "Coucou ! 👋 Moi c'est Pana, ton petit assistant de poche. Tu vas où de beau aujourd'hui ? 🐾"}
        ]

    chat_container = st.container(height=500)
    
    with chat_container:
        for message in st.session_state.messages_ia_v4:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Prochains départs à Noisy Champs ?"):
        st.session_state.messages_ia_v4.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🦊 *Pana cherche dans ses fiches...*")
                
                try:
                    response = st.session_state.chat_session_v4.send_message(prompt)
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    st.session_state.messages_ia_v4.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    erreur_brute = str(e)
                    if "429" in erreur_brute or "Quota" in erreur_brute:
                        message_placeholder.warning("**Oups !** 🥵 Le réseau est saturé. Laisse-moi souffler une petite minute. 🐾")
                    else:
                        message_placeholder.error(f"Erreur technique : {erreur_brute}")
