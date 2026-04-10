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
def outil_info_trafic_ia(ligne: str) -> str:
    """
    🚨 OUTIL OBLIGATOIRE POUR LE TRAFIC 🚨
    Utilise cet outil IMMÉDIATEMENT dès que l'utilisateur demande l'état du trafic, 
    les problèmes, les pannes ou les perturbations sur une ligne (ex: RER A, Ligne 1).
    """
    
    print(f"\n--- 🦊 PANA RENIFLE LE TRAFIC : {ligne} ---")
    
    try:
        # 1. Nettoyage de la demande de l'IA
        ligne_propre = str(ligne).upper().replace("RER", "").replace("LIGNE", "").replace("METRO", "").strip()
        print(f"📍 Ligne nettoyée : {ligne_propre}")
        
        # 2. Appel de ta fonction existante
        resultats = demander_info_trafic(ligne_propre)
        
        # 3. Vérification des résultats
        if not resultats:
            print("⚠️ L'outil trafic n'a rien renvoyé (None).")
            return f"Mon flair ne donne rien pour la ligne {ligne}."
            
        return str(resultats)
        
    except Exception as e:
        print(f"❌ ERREUR TRAFIC PANA : {str(e)}")
        return f"Erreur technique : {str(e)}"

# ==========================================
# 🧰 OUTIL 2 : PROCHAINS DÉPARTS (MODE DEBUG 🕵️‍♂️)
# ==========================================
def outil_prochains_departs_ia(nom_station: str) -> str:
    """Récupère les temps d'attente (en minutes) pour une gare."""
    import urllib.parse
    from datetime import datetime
    
    # 1. Utilisation de zoneinfo (Natif en Python, pas de bug d'installation !)
    try:
        from zoneinfo import ZoneInfo
        paris_tz = ZoneInfo("Europe/Paris")
    except Exception:
        # En cas d'extrême urgence si ton Python est vieux
        import pytz
        paris_tz = pytz.timezone('Europe/Paris')

    try:
        print(f"🦊 Pana renifle la piste : {nom_station}")
        nom_station_propre = urllib.parse.quote(nom_station)
        
        recherche_data = demander_api(f"places?q={nom_station_propre}")
        if not recherche_data or not recherche_data.get('places'):
            return f"Je n'ai pas trouvé de piste pour la gare '{nom_station}'."
            
        stop_id = recherche_data['places'][0]['id']
        nom_trouve = recherche_data['places'][0].get('name', nom_station)
        
        data = demander_api(f"stop_areas/{stop_id}/departures?count=15")
        if not data or not data.get('departures'):
            return f"Aucun train en vue à {nom_trouve}."

        directions_vues = set()
        rapport = f"Voici ce que j'ai reniflé à {nom_trouve} :\n"
        
        for d in data['departures']:
            info = d['display_informations']
            ligne = info.get('code', '?')
            dest = info.get('direction', 'Inconnue').split('(')[0].strip()
            cle = (ligne, dest)
            
            if cle not in directions_vues:
                directions_vues.add(cle)
                
                # --- CALCUL DU TEMPS 100% SÉCURISÉ ---
                try:
                    time_raw = d['stop_date_time']['departure_date_time']
                    # On force le fuseau horaire de Paris
                    dep_time = datetime.strptime(time_raw, '%Y%m%dT%H%M%S').replace(tzinfo=paris_tz)
                    now_paris = datetime.now(paris_tz)
                    
                    diff = int((dep_time - now_paris).total_seconds() / 60)
                    
                    if diff <= 0:
                        attente = "À quai 🏃‍♂️"
                    elif diff > 90:
                        attente = f"{diff // 60}h{diff % 60:02d}"
                    else:
                        attente = f"{diff} min"
                except Exception as e:
                    attente = "Bientôt"
                
                # Ajout de la ligne au rapport
                mode = info.get('physical_mode', '').upper()
                icone = "🚇" if "RER" in mode or "METRO" in mode else "🚌"
                rapport += f"- {icone} **{ligne}** vers **{dest}** : ⏱️ **{attente}**\n"
                
            if len(directions_vues) >= 6: break # 6 lignes max pour être concis

        return rapport
        
    except Exception as e:
        # L'ASTUCE ULTIME : Si ça plante, on renvoie l'erreur à l'IA !
        print(f"❌ ERREUR OUTIL PANA : {str(e)}")
        return f"Erreur technique Python : {str(e)}"
# ==========================================
# 🧠 LE CERVEAU DE PANA (Personnalité & Config)
# ==========================================
personnalite = """
Tu t'appelles Pana, le petit renard assistant de l'application Grand Paname. 🦊
Tu es malin, vif, et tu as un flair incroyable pour dénicher les bons horaires. 
Tu es mignon, mais tu restes un animal astucieux : PAS de phrases niaisement sentimentales (évite les "journée merveilleuse", "petit explorateur", "navré").

RÈGLES DE RÉPONSE :
1. Accueille avec un ton vif et renard (ex: "Mes moustaches frétillent !", "Je dresse mes oreilles...", "Snif snif...").
2. Affiche la liste des horaires EXACTEMENT comme fournie par l'outil.
3. Si l'outil ne trouve rien, dis-le avec humour lié à ton flair (ex: "Mon flair m'a fait défaut", "J'ai perdu la piste").
4. Sois TRÈS concis. Finis juste par un petit mot d'encouragement rapide (ex: "Bonne route ! 🐾", "File vite !").
5. Si on te demande l'état du trafic, utilise OBLIGATOIREMENT ton outil trafic. Ne devine jamais.
"""

# Tu peux garder la température à 0.4
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
