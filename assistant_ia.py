import streamlit as st
import google.generativeai as genai
import re  # 👈 Nouveau : Pour lire les textes d'erreurs intelligemment

# ⚠️ À MODIFIER : Importe tes vraies fonctions !
from api_idfm import demander_info_trafic
# Ajoute ici l'import de ta fonction qui gère les départs dans la V2 :
# from nom_de_ton_fichier_api import demander_prochains_departs 

# 1. Configuration de l'API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Attention : Clé API introuvable dans st.secrets !")

# ==========================================
# 🧰 OUTIL 1 : INFO TRAFIC
# ==========================================
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
# 🧰 OUTIL 2 : PROCHAINS DÉPARTS (NOUVEAU ✨)
# ==========================================
def outil_prochains_departs_ia(nom_station: str) -> str:
    """
    Récupère les horaires des prochains départs pour une gare ou une station.
    Args:
        nom_station: Le nom de la station (ex: 'Châtelet', 'Gare de Lyon', 'La Défense').
    """
    # ⚠️ À FAIRE : Connecter ta vraie fonction ici !
    # Exemple de ce que tu devras coder :
    # resultats = demander_prochains_departs(nom_station)
    # return resultats
    
    # Pour l'instant, on simule pour voir si l'IA comprend l'outil :
    return f"Données trouvées pour {nom_station} : Prochain train dans 3 min, le suivant dans 8 min."

# ==========================================
# 🧠 LE CERVEAU & LA PERSONNALITÉ
# ==========================================
# On donne un "caractère" à l'IA avant même qu'elle ne parle
personnalite = """
Tu es l'assistant virtuel de l'application Grand Paname, spécialisée dans les transports en Île-de-France.
- Tu es ultra-sympathique, chaleureux, et tu as beaucoup d'humour.
- Utilise des emojis pour rendre la conversation vivante (🚇, 🥐, ☔, 🏃‍♂️).
- Si le trafic est bon, sois enthousiaste ("Excellente nouvelle ! 🎉").
- S'il y a des retards, sois compatissant et encourageant ("Courage pour l'attente 😔").
- Fais parfois de très courtes blagues sur la vie parisienne (la pluie, les touristes, le café).
- Fais des réponses courtes et aérées.
"""

# On déclare le modèle avec ses 2 outils et sa personnalité
model = genai.GenerativeModel(
    'gemini-2.5-flash', # Garde celui qui fonctionnait pour toi !
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    system_instruction=personnalite
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Trafic, horaires, itinéraires... Demandez-moi tout !</p>", unsafe_allow_html=True)

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Coucou ! 👋 Je suis prêt à t'accompagner. Tu vas où de beau aujourd'hui ? 🚇"}
        ]

    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Dans combien de temps est le prochain RER A à Châtelet ?"):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je fouille dans les serveurs...*")
                
                try:
                    # Plus besoin de lui répéter de répondre gentiment, 
                    # c'est ancré dans sa "system_instruction" en haut !
                    response = st.session_state.chat_session.send_message(prompt)
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    erreur_brute = str(e)
                    
                    # 🛡️ INTERCEPTION INTELLIGENTE DU QUOTA (429)
                    if "429" in erreur_brute or "Quota exceeded" in erreur_brute:
                        # On cherche le nombre de secondes dans l'erreur avec une expression régulière
                        match = re.search(r'retry in (\d+)', erreur_brute)
                        if match:
                            secondes = match.group(1)
                            erreur_texte = f"**Oups !** 🥵 On va un peu trop vite ! Laisse-moi reprendre mon souffle pendant environ **{secondes} secondes** avant ta prochaine question. ☕"
                        else:
                            erreur_texte = "**Oups !** 🥵 Beaucoup trop de questions à la fois, le serveur surchauffe. Laisse-moi souffler une petite minute. ☕"
                        
                        message_placeholder.warning(erreur_texte)
                    else:
                        # Si c'est une autre erreur, on l'affiche normalement
                        message_placeholder.error(f"Erreur technique : {erreur_brute}")
