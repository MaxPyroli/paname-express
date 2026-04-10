import streamlit as st
import time
import google.generativeai as genai

# 1. Configuration de l'API
# On s'assure que la clé est bien lue
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Attention : Clé API introuvable dans st.secrets !")

# 🧠 LES OUTILS DE L'IA
def obtenir_info_trafic(ligne: str) -> str:
    """
    Récupère l'état du trafic en temps réel pour une ligne de métro ou RER.
    Args:
        ligne: Le nom de la ligne (ex: 'RER A', '1', '14').
    """
    ligne_up = ligne.upper()
    if "A" in ligne_up:
        return "Trafic fortement perturbé sur le RER A suite à un incident."
    elif "14" in ligne_up:
        return "Ligne 14 fermée pour cause de travaux."
    else:
        return f"Trafic parfaitement normal sur la ligne {ligne}."

# Initialisation du modèle
model = genai.GenerativeModel(
    'gemini-2.5-flash', 
    tools=[obtenir_info_trafic]
)

# 🎨 L'INTERFACE DE LA MODALE
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Posez-moi vos questions sur le trafic.</p>", unsafe_allow_html=True)

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis connecté au réseau. Demande-moi l'état d'une ligne ! 🚇"}
        ]

    # 1. On crée la zone d'historique (en haut)
    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 2. On place la barre de chat TOUT EN BAS
    if prompt := st.chat_input("Ex: Y a-t-il des problèmes sur le RER A ?"):
        
        # On sauvegarde le message utilisateur
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        # On l'affiche instantanément dans le conteneur du haut (sans faire clignoter la page)
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # L'IA répond dans la foulée
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je consulte le réseau...*")
                
                try:
                    # L'appel à l'API
                    response = st.session_state.chat_session.send_message(
                        f"Tu es l'assistant de l'app Grand Paname. Réponds de façon concise. Question de l'utilisateur : {prompt}"
                    )
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    # On sauvegarde la réponse
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    # ICI : On affiche la vraie erreur technique envoyée par Google !
                    erreur_texte = f"**Erreur technique détectée :**\n`{str(e)}`"
                    message_placeholder.error(erreur_texte)
