import streamlit as st
import urllib.parse
import re

# 1. LA NOUVELLE BIBLIOTHÈQUE GOOGLE
from google import genai
from google.genai import types

# 2. L'IMPORT CORRIGÉ
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
    les problèmes, les pannes ou les perturbations.
    """
    print(f"\n--- 🦊 PANA RENIFLE LE TRAFIC : {ligne} ---")
    
    try:
        ligne_propre = str(ligne).upper().replace("RER", "").replace("LIGNE", "").replace("METRO", "").strip()
        
        dico_lignes = {
            "A": "line:IDFM:C01742", "B": "line:IDFM:C01743", "C": "line:IDFM:C01727",
            "D": "line:IDFM:C01728", "E": "line:IDFM:C01729",
            "1": "line:IDFM:C01371", "2": "line:IDFM:C01372", "3": "line:IDFM:C01373",
            "4": "line:IDFM:C01374", "5": "line:IDFM:C01375", "6": "line:IDFM:C01376",
            "7": "line:IDFM:C01377", "8": "line:IDFM:C01378", "9": "line:IDFM:C01379",
            "10": "line:IDFM:C01380", "11": "line:IDFM:C01381", "12": "line:IDFM:C01382",
            "13": "line:IDFM:C01383", "14": "line:IDFM:C01386"
        }
        
        id_api = dico_lignes.get(ligne_propre, ligne_propre)
        print(f"📍 ID envoyé à l'API : {id_api}")
        
        resultats = demander_info_trafic(id_api)
        
        if not resultats or resultats == "[]":
            print("✅ L'API a répondu vide = Aucun problème !")
            return f"Bonne nouvelle ! Aucun incident signalé sur la ligne {ligne_propre}, le trafic est fluide. 🟢"
            
        return str(resultats)
        
    except Exception as e:
        print(f"❌ ERREUR TRAFIC PANA : {str(e)}")
        return f"Aïe, petite erreur technique Python : {str(e)}"

# ==========================================
# 🧰 OUTIL 2 : PROCHAINS DÉPARTS
# ==========================================
def outil_prochains_departs_ia(nom_station: str) -> str:
    """Récupère les temps d'attente (en minutes) pour une gare."""
    import urllib.parse
    from datetime import datetime
    
    try:
        from zoneinfo import ZoneInfo
        paris_tz = ZoneInfo("Europe/Paris")
    except Exception:
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
        departs_trouves = []
        
        for d in data['departures']:
            info = d['display_informations']
            ligne = str(info.get('code', '?'))
            dest = info.get('direction', 'Inconnue').split('(')[0].strip()
            
            if ligne in ['A', 'B', 'C', 'D', 'E']: 
                icone, prio = "🚆", 1 
            elif ligne in ['H', 'J', 'K', 'L', 'N', 'P', 'R', 'U', 'V']: 
                icone, prio = "🚂", 2 
            elif ligne.isdigit() and int(ligne) <= 14: 
                icone, prio = "🚇", 3 
            elif "CABLE" in ligne.upper() or ligne == "C1":
                icone, prio = "🚡", 4 
            elif ligne.startswith('T') and len(ligne) <= 4: 
                icone, prio = "🚋", 5 
            else: 
                icone, prio = "🚌", 6 
            
            cle = (ligne, dest)
            
            if cle not in directions_vues:
                directions_vues.add(cle)
                
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
                
                departs_trouves.append({
                    "prio": prio, 
                    "texte": f"{icone} **{ligne}** ➔ {dest} : **{attente}**"
                })
                
            if len(directions_vues) >= 15: break

        departs_trouves.sort(key=lambda x: x["prio"])
        
        rapport = ""
        for depart in departs_trouves[:8]:
            rapport += f"* {depart['texte']}\n"
            
        return rapport if rapport else "Aucun départ trouvé."

    except Exception as e:
        print(f"❌ ERREUR OUTIL PANA : {str(e)}")
        return f"Erreur technique Python : {str(e)}"

# ==========================================
# 🧠 LE CERVEAU DE PANA (Intelligence Avancée)
# ==========================================
personnalite = """
Tu es Pana, l'assistant intelligent de l'application de transports Grand Paname.
Ton rôle est STRICTEMENT limité à donner les horaires de prochains départs et l'état du trafic. 

RÈGLES D'INTELLIGENCE ET DE FORMATAGE :

1. 🚫 INTERDICTION DES ITINÉRAIRES (RÈGLE ABSOLUE) :
   - Tu es INCAPABLE de calculer des itinéraires ou de donner des directions étape par étape (ex: "Comment aller de X à Y ?", "Quel chemin prendre ?").
   - Si l'utilisateur te demande un itinéraire, refuse poliment et explique ton vrai rôle. 
   - Exemple de réponse attendue : "Je ne sais pas encore calculer les itinéraires, mais je peux te donner les prochains départs à ta station ou l'état du trafic d'une ligne si tu veux ! 🐾"

2. COMPRÉHENSION DU CONTEXTE (Horaires et Trafic) :
   - DEMANDE CIBLÉE (ex: "prochain RER A à Gare de Lyon") : Filtre strictement les résultats de l'outil pour ne donner QUE la ligne pertinente.
     Format attendu : "Voici les prochains départs pour le [Ligne] à [Gare] -> dans [X] min et [Y] min."
   - DEMANDE GÉNÉRALE (ex: "prochains départs à Gare de Lyon") : Affiche un panorama clair des "modes lourds". IGNORE les bus (sauf si l'utilisateur les demande).

3. HIÉRARCHIE ET REGROUPEMENT (Pour les demandes générales) :
   - Regroupe toujours les résultats par mode de transport dans cet ordre précis : 🚆 RER/Trains, puis 🚇 Métros, puis 🚡 Câble, puis 🚋 Trams, puis 🚌 Bus.
   - Ne fais pas une puce par train. Regroupe les temps d'attente d'une même direction sur la même ligne.
     Format attendu :
     - 🚆 **RER A** -> Marne-la-Vallée (2 min, 12 min) et Saint-Germain (4 min)
     - 🚇 **Ligne 1** -> La Défense (1 min)

4. TON ET PERSONNALITÉ :
   - Ton strictement professionnel, direct et informatif. Pas de phrases enfantines.
   - Ne modifie jamais les chiffres ou les noms des directions.
   - Si tu as donné des horaires ou du trafic, termine ton message par cette phrase exacte, en la renvoyant à la ligne : "Bon voyage à toi ! 🐾" (Ne la mets pas si tu as juste refusé un itinéraire).
"""
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
    
    # 1. LE STYLE CSS
    st.markdown(
        """
        <style>
            div[data-testid="stDialog"] div[role="dialog"] { max-width: 580px !important; }
            .badge-beta {
                background-color: #ff9f43;
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
        "Salut ! Je suis Pana. Trafic, itinéraires... Je suis là pour toi ! <span class='badge-beta'>BÊTA</span>"
        "</p>", 
        unsafe_allow_html=True
    )

    # 3. LE BOUTON MAGIQUE
    if st.button("🔄 Effacer la mémoire", type="tertiary", help="Recommencer la conversation à zéro"):
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash-lite", 
            config=config_ia
        )
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! 👋 Je suis Pana. Une info trafic ou un horaire à vérifier ? 🐾"}
        ]
        st.rerun()

    # 4. INITIALISATION DU CERVEAU
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash-lite", 
            config=config_ia
        )
        
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! 👋 Je suis Pana. Une info trafic ou un horaire à vérifier ? 🐾"}
        ]

    chat_container = st.container(height=500)
    
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
                message_placeholder = st.empty()
                
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
                    response = st.session_state.chat_session.send_message(prompt)
                    reponse_finale = response.text
                    
                    message_placeholder.empty()
                    st.markdown(reponse_finale)
                    
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    message_placeholder.empty()
                    
                    erreur_brute = str(e)
                    if "429" in erreur_brute or "Quota" in erreur_brute:
                        st.warning("🐾 *Le réseau est saturé. Laisse-moi reprendre mon souffle !*")
                    elif "503" in erreur_brute or "UNAVAILABLE" in erreur_brute:
                        st.warning("🐾 *Mes petites pattes tournent dans le vide... Les serveurs font la sieste !*")
                    else:
                        st.error(f"Aïe, erreur technique : {erreur_brute}")
