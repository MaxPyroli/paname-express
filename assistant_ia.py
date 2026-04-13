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
# 🎨 L'INTERFACE DE LA MODALE & LE DESIGN (LISIBLE)
# ==========================================
@st.dialog(" ") 
def ouvrir_assistant():
    
    # 1. LE STYLE CSS (Thème Dynamique & Bulles)
    st.markdown(
        """
        <style>
            /* La fenêtre principale (S'adapte au Clair/Sombre magiquement) */
            div[data-testid="stDialog"] div[role="dialog"] { 
                max-width: 600px !important; 
                /* On prend le fond natif (blanc/noir) et on le rend 85% opaque */
                background: color-mix(in srgb, var(--background-color) 85%, transparent) !important;
                backdrop-filter: blur(20px) !important; 
                -webkit-backdrop-filter: blur(20px) !important;
                border: 1px solid var(--secondary-background-color) !important; 
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15) !important;
                border-radius: 28px !important;
            }
            
            /* Titre stylé */
            .titre-container {
                margin-top: -30px;
                margin-bottom: 25px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .titre-pana {
                font-size: 2.4rem;
                font-weight: 900;
                display: flex;
                align-items: center;
                gap: 15px;
                color: #ff9f43; /* Orange toujours visible */
            }
            
            .badge-beta {
                background: rgba(255, 159, 67, 0.15);
                color: #ff9f43;
                border: 1px solid rgba(255, 159, 67, 0.3);
                padding: 2px 10px;
                border-radius: 8px;
                font-size: 0.7rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .sous-titre-pana {
                color: var(--text-color);
                opacity: 0.7;
                font-size: 0.95em; 
                font-weight: 500;
            }

            /* --- LES NOUVELLES BULLES DE CHAT --- */
            /* 1. On enlève le fond de la ligne entière */
            div[data-testid="stChatMessage"] {
                background-color: transparent !important;
                border: none !important;
            }
            
            /* 2. On crée la bulle uniquement autour du texte */
            div[data-testid="stChatMessageContent"] {
                background-color: var(--secondary-background-color) !important; /* Gris très clair en mode clair */
                padding: 16px 20px !important;
                border-radius: 22px !important;
                border: 1px solid rgba(150, 150, 150, 0.1) !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                color: var(--text-color) !important;
            }
            
            /* Ajustement de la barre d'entrée texte */
            .stChatInput {
                background: var(--secondary-background-color) !important;
                border-radius: 18px !important;
                border: 1px solid rgba(150, 150, 150, 0.2) !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. AFFICHAGE DU TITRE DÉSIGN
    st.markdown(
        """
        <div class="titre-container">
            <div class="titre-pana">
                🐾 Pana <span class="badge-beta">BÊTA</span>
            </div>
            <div class="sous-titre-pana">
                Assistant intelligent • Trafic & Horaires
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 3. BOUTON DE RÉINITIALISATION (Plus discret)
    if st.button("🔄 Réinitialiser la discussion", type="tertiary"):
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash-lite", 
            config=config_ia
        )
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! 👋 Je suis Pana. Comment puis-je t'aider aujourd'hui ? 🐾"}
        ]
        st.rerun()

    # 4. INITIALISATION / SESSION
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash-lite", 
            config=config_ia
        )
        st.session_state.messages_ia = [{"role": "assistant", "content": "Salut ! 👋 Je suis Pana. Une info trafic ou un horaire à vérifier ? 🐾"}]

    # 5. CONTENEUR DE CHAT (Sans bordure pour l'effet flottant)
    chat_container = st.container(height=450, border=False)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 6. ENTRÉE UTILISATEUR
    if prompt := st.chat_input("Demande-moi un horaire..."):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Animation des points
                message_placeholder.markdown("""
                <div class="corgi-loader">🐾 <i>Analyse en cours</i><span>.</span><span>.</span><span>.</span></div>
                """, unsafe_allow_html=True)
                
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    reponse_finale = response.text
                    
                    message_placeholder.empty()
                    st.markdown(reponse_finale)
                    
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    message_placeholder.empty()
                    st.error(f"Oups, Pana a glissé : {str(e)}")
