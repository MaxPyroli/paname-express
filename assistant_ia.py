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
    """
    UTILISE CET OUTIL OBLIGATOIREMENT pour obtenir les horaires, 
    les prochains trains ou les prochains départs d'une gare ou d'une station.
    """
    
    print(f"\n--- 🚀 DÉBUT RECHERCHE IA: {nom_station} ---")
    # ... la suite du code ...
    
    try:
        nom_station_propre = urllib.parse.quote(nom_station)
        print(f"📍 1. Texte nettoyé : {nom_station_propre}")
        
        recherche_data = demander_api(f"places?q={nom_station_propre}")
        
        if not recherche_data:
            print("⚠️ 2. CRASH SILENCIEUX : demander_api n'a rien renvoyé (None) pour la recherche.")
            return f"Je ne trouve pas {nom_station}."
            
        places = recherche_data.get('places', [])
        print(f"📍 2. Nombre de lieux trouvés par IDFM : {len(places)}")
        
        if len(places) == 0:
            print("⚠️ 3. CRASH SILENCIEUX : IDFM a répondu, mais la liste est vide.")
            return f"Je n'ai pas réussi à trouver l'arrêt '{nom_station}' sur le réseau."
            
        # On essaie de forcer la recherche sur une "stop_area" (une vraie gare)
        stop_id = places[0]['id']
        nom_trouve = places[0].get('name', nom_station)
        type_lieu = places[0].get('embedded_type', 'inconnu')
        
        print(f"📍 3. Lieu choisi : {nom_trouve} | ID : {stop_id} | Type : {type_lieu}")
        
        # Si l'API a trouvé une ville au lieu d'une gare, on prévient la console
        if type_lieu != 'stop_area':
            print("🚨 ATTENTION : L'API a trouvé une ville/région, pas une gare ! Ça risque de foirer.")

        data = demander_api(f"stop_areas/{stop_id}/departures?count=10")
        
        if not data:
            print("⚠️ 4. CRASH SILENCIEUX : demander_api n'a rien renvoyé pour les départs.")
            return f"Aucun réseau pour {nom_trouve}."
            
        departures = data.get('departures', [])
        print(f"📍 4. Nombre de trains trouvés : {len(departures)}")
        
        if len(departures) == 0:
            return f"Aucun départ trouvé pour {nom_trouve} actuellement."
            
        rapport = f"Prochains départs à {nom_trouve} :\n"
        lignes_vues = 0
        
        for d in departures:
            if lignes_vues >= 6: break
            info = d['display_informations']
            rapport += f"- {info.get('code', '?')} vers {info.get('direction', '?')}\n"
            lignes_vues += 1
            
        print("✅ 5. SUCCÈS : Rapport envoyé à l'IA !")
        print("------------------------------------------\n")
        return rapport
        
    except Exception as e:
        print(f"❌ 6. VRAIE ERREUR: {str(e)}")
        print("------------------------------------------\n")
        return f"Erreur réseau pour {nom_station}."

# ==========================================
# 🧠 LE CERVEAU & LA PERSONNALITÉ (SYNTAXE V2)
# ==========================================
personnalite = """
Tu es l'assistant virtuel de l'application Grand Paname, spécialisée dans les transports en Île-de-France.
- RÈGLE ABSOLUE 1 : Ne devine JAMAIS et n'invente JAMAIS d'horaires ou d'état du trafic.
- RÈGLE ABSOLUE 2 : Si l'utilisateur demande des horaires, des prochains trains ou des départs, tu DOIS OBLIGATOIREMENT utiliser l'outil 'outil_prochains_departs_ia'. 
- Tu es ultra-sympathique, chaleureux, et tu as beaucoup d'humour.
- Utilise des emojis pour rendre la conversation vivante (🚇, 🥐, ☔, 🏃‍♂️).
"""

# Dans la V2, on ne crée plus le modèle ici, on crée juste sa "Configuration"
config_ia = types.GenerateContentConfig(
    system_instruction=personnalite,
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    temperature=0.7
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
# 👇 Ajout de width="large" ici
@st.dialog("🤖 Assistant Paname", width="large")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Trafic, horaires, itinéraires... Demandez-moi tout !</p>", unsafe_allow_html=True)
    # On passe en V3 pour forcer Streamlit à oublier l'ancienne mémoire !
    if "chat_session_v3" not in st.session_state:
        
        # 👇 LA NOUVELLE FAÇON DE DÉMARRER LE CHAT EN V2 👇
        st.session_state.chat_session_v3 = client.chats.create(
            model="gemini-3.1-flash-lite-preview",
            config=config_ia
        )
        
        st.session_state.messages_ia_v3 = [
            {"role": "assistant", "content": "Coucou ! 👋 Mon nouveau cerveau V2 est enfin connecté. Tu vas où de beau aujourd'hui ? 🚇"}
        ]

    chat_container = st.container(height=500)
    
    with chat_container:
        for message in st.session_state.messages_ia_v3:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Prochains départs à Noisy Champs ?"):
        st.session_state.messages_ia_v3.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je fouille dans les serveurs...*")
                
                try:
                    # Envoi du message avec la nouvelle syntaxe
                    response = st.session_state.chat_session_v3.send_message(prompt)
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    st.session_state.messages_ia_v3.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    erreur_brute = str(e)
                    
                    if "429" in erreur_brute or "Quota" in erreur_brute:
                        match = re.search(r'retry in (\d+)', erreur_brute)
                        if match:
                            secondes = match.group(1)
                            erreur_texte = f"**Oups !** 🥵 Laisse-moi reprendre mon souffle pendant environ **{secondes} secondes**. ☕"
                        else:
                            erreur_texte = "**Oups !** 🥵 Le serveur surchauffe. Laisse-moi souffler une petite minute. ☕"
                        message_placeholder.warning(erreur_texte)
                    else:
                        message_placeholder.error(f"Erreur technique : {erreur_brute}")
