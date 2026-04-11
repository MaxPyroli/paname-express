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
# 🧰 OUTIL 1 : INFO TRAFIC (100% OPÉRATIONNEL 🦊)
# ==========================================
def outil_info_trafic_ia(ligne: str) -> str:
    """
    🚨 OUTIL OBLIGATOIRE POUR LE TRAFIC 🚨
    Utilise cet outil IMMÉDIATEMENT dès que l'utilisateur demande l'état du trafic, 
    les problèmes, les pannes ou les perturbations.
    """
    print(f"\n--- 🦊 PANA RENIFLE LE TRAFIC : {ligne} ---")
    
    try:
        ligne_propre = str(ligne).upper().replace("RER", "").replace("LIGNE", "").replace("METRO", "").strip()
        
        # 1. LE TRADUCTEUR SECRET (L'API veut des ID, pas des lettres !)
        dico_lignes = {
            "A": "line:IDFM:C01742", "B": "line:IDFM:C01743", "C": "line:IDFM:C01727",
            "D": "line:IDFM:C01728", "E": "line:IDFM:C01729",
            "1": "line:IDFM:C01371", "2": "line:IDFM:C01372", "3": "line:IDFM:C01373",
            "4": "line:IDFM:C01374", "5": "line:IDFM:C01375", "6": "line:IDFM:C01376",
            "7": "line:IDFM:C01377", "8": "line:IDFM:C01378", "9": "line:IDFM:C01379",
            "10": "line:IDFM:C01380", "11": "line:IDFM:C01381", "12": "line:IDFM:C01382",
            "13": "line:IDFM:C01383", "14": "line:IDFM:C01386"
        }
        
        id_api = dico_lignes.get(ligne_propre, ligne_propre) # Prend l'ID si connu, sinon tente le texte
        print(f"📍 ID envoyé à l'API : {id_api}")
        
        # 2. Appel de ta fonction
        resultats = demander_info_trafic(id_api)
        
        # 3. GESTION DU "TOUT VA BIEN" (La vraie logique !)
        if not resultats or resultats == "[]":
            print("✅ L'API a répondu vide = Aucun problème !")
            return f"Bonne nouvelle ! Aucun incident signalé sur la ligne {ligne_propre}, le trafic est fluide. 🟢"
            
        return str(resultats)
        
    except Exception as e:
        print(f"❌ ERREUR TRAFIC PANA : {str(e)}")
        return f"Aïe, petite erreur technique Python : {str(e)}"

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
        
        data = demander_api(f"stop_areas/{stop_id}/departures?count=30")
        if not data or not data.get('departures'):
            return f"Aucun train en vue à {nom_trouve}."

        directions_vues = set()
        rapport = f"Voici ce que j'ai reniflé à {nom_trouve} :\n"
        
                directions_vues = set()
        departs_trouves = [] # On stocke ici pour trier à la fin
        
        for d in data['departures']:
            info = d['display_informations']
            ligne = str(info.get('code', '?'))
            dest = info.get('direction', 'Inconnue').split('(')[0].strip()
            
            # --- DÉTECTEUR D'ICÔNES ET HIÉRARCHIE (Priorité de 1 à 6) ---
            if ligne in ['A', 'B', 'C', 'D', 'E']: 
                icone, prio = "🚆", 1 # RER
            elif ligne in ['H', 'J', 'K', 'L', 'N', 'P', 'R', 'U', 'V']: 
                icone, prio = "🚂", 2 # Transilien (Train)
            elif ligne.isdigit() and int(ligne) <= 14: 
                icone, prio = "🚇", 3 # Métro
            elif "CABLE" in ligne.upper() or ligne == "C1":
                icone, prio = "🚡", 4 # Câble
            elif ligne.startswith('T') and len(ligne) <= 4: 
                icone, prio = "🚋", 5 # Tram
            else: 
                icone, prio = "🚌", 6 # Bus et Noctilien
            
            cle = (ligne, dest)
            
            if cle not in directions_vues:
                directions_vues.add(cle)
                
                # Calcul du temps
                try:
                    time_raw = d['stop_date_time']['departure_date_time']
                    dep_time = datetime.strptime(time_raw, '%Y%m%dT%H%M%S').replace(tzinfo=paris_tz)
                    now_paris = datetime.now(paris_tz)
                    diff = int((dep_time - now_paris).total_seconds() / 60)
                    
                    if diff <= 0: attente = "À quai"
                    elif diff > 90: attente = f"{diff // 60}h{diff % 60:02d}"
                    else: attente = f"{diff} min"
                except:
                    attente = "Bientôt"
                
                # On sauvegarde dans notre liste pour le tri
                departs_trouves.append({
                    "prio": prio, 
                    "texte": f"{icone} **{ligne}** ➔ {dest} : **{attente}**"
                })
                
            if len(directions_vues) >= 15: break # On prend plus de résultats avant de trier

        # --- LE TRI ET L'AFFICHAGE FINAL ---
        # On trie par priorité (RER d'abord, Bus à la fin)
        departs_trouves.sort(key=lambda x: x["prio"])
        
        rapport = ""
        # On ne garde que les 8 premiers résultats pour que ça reste lisible sur mobile
        for depart in departs_trouves[:8]:
            rapport += f"* {depart['texte']}\n"
            
        return rapport if rapport else "Aucun départ trouvé."

    except Exception as e:
        # L'ASTUCE ULTIME : Si ça plante, on renvoie l'erreur à l'IA !
        print(f"❌ ERREUR OUTIL PANA : {str(e)}")
        return f"Erreur technique Python : {str(e)}"
# ==========================================
# 🧠 LE CERVEAU DE PANA (Intelligence Avancée)
# ==========================================
personnalite = """
Tu es Pana, l'assistant intelligent de Grand Paname.
Ton but est d'avoir une conversation fluide et ultra-utile.

RÈGLES DE MISE EN PAGE OBLIGATOIRES :
1. Affiche TOUJOURS les horaires sous forme de liste à puces stricte (avec des retours à la ligne). Interdiction de tout écraser dans un seul paragraphe.
2. Garde EXACTEMENT le format de l'outil (ex: "🚆 **A** ➔ Poissy : **4 min**"). Ne rajoute pas le mot "Ligne" si l'outil ne le donne pas.
3. Compréhension : Si l'utilisateur demande "le prochain train", filtre les résultats pour ne donner que ce qu'il cherche.
4. Ton : Professionnel, concis et naturel. Termine par une micro-formule avec ta mascotte (ex: "Bon trajet ! 🐾").
"""

# On remonte la température à 0.5 : c'est le réglage parfait pour 
# qu'il soit logique (chiffres exacts) mais conversationnel (phrases naturelles).
config_ia = types.GenerateContentConfig(
    system_instruction=personnalite,
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    temperature=0.5
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
5: #ff9f43; /* Un bel orange moderne */
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
    # ==========================================
# 🎨 L'INTERFACE DE LA MODALE & LE BADGE
# ==========================================
@st.dialog("🤖 Pana") 
def ouvrir_assistant():
    
    # ... (Garde ton bloc <style> CSS ici) ...

    # Le sous-titre de Pana
    st.markdown(
        "<p style='color: #888; font-size: 0.9em; margin-top: -10px; margin-bottom: 20px;'>"
        "Coucou ! Je suis Pana. Trafic, itinéraires... Je suis là pour toi ! <span class='badge-beta'>BÊTA</span>"
        "</p>", 
        unsafe_allow_html=True
    )

    # 👇 LE NOUVEAU BOUTON MAGIQUE (MÉTHODE FORTE) 👇
    if st.button("🔄 Effacer la mémoire", type="tertiary", help="Recommencer la conversation à zéro"):
        # On n'efface plus, on écrase avec un cerveau tout neuf !
        st.session_state.chat_session = client.chats.create(
            model="gemini-3.1-flash-lite-preview", 
            config=config_ia
        )
        st.rerun() # Rafraîchit l'écran
    # 👆 ------------------------------------------ 👆

    # 3. LE DÉMARRAGE DU CERVEAU (Avec des noms propres, sans "v5")
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash-lite", 
            config=config_ia
        )
        
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! 👋 Je suis Pana. Une info trafic ou un horaire à vérifier ? 🐾"}
        ]

    chat_container = st.container(height=500)
    
    # ... (La suite reste identique, assure-toi juste d'avoir enlevé les _v5 partout !) ...
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Prochains départs à Noisy Champs ?"):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                # 1. On crée une "boîte vide"
                message_placeholder = st.empty()
                
                # 2. On y injecte notre animation CSS sur-mesure (3 points qui clignotent)
                animation_html = """
                <style>
                .corgi-loader { color: #555; }
                .corgi-loader span { animation: blink 1.4s infinite both; font-size: 1.2em; font-weight: bold; }
                .corgi-loader span:nth-child(2) { animation-delay: 0.2s; }
                .corgi-loader span:nth-child(3) { animation-delay: 0.4s; }
                @keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
                </style>
                <div class="corgi-loader">🐾 <i>Pana va chercher l'info</i><span>.</span><span>.</span><span>.</span></div>
                """
                message_placeholder.markdown(animation_html, unsafe_allow_html=True)
                
                try:
                    # L'IA réfléchit...
                    response = st.session_state.chat_session.send_message(prompt)
                    reponse_finale = response.text
                    
                    # 3. ON DETRUIT L'ANIMATION et on affiche le vrai texte
                    message_placeholder.empty()
                    st.markdown(reponse_finale)
                    
                    # On sauvegarde
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    # 4. MÊME SI ÇA PLANTE, on détruit l'animation pour garder l'écran propre !
                    message_placeholder.empty()
                    
                    erreur_brute = str(e)
                    if "429" in erreur_brute or "Quota" in erreur_brute:
                        st.warning("🐶 *Wouf ! Le réseau est saturé. Laisse-moi boire un peu d'eau !* 💧")
                    elif "503" in erreur_brute or "UNAVAILABLE" in erreur_brute:
                        st.warning("🐶 *Mes petites pattes tournent dans le vide... Les serveurs font la sieste !* 💤")
                    else:
                        st.error(f"Aïe, petit os technique : {erreur_brute}")
