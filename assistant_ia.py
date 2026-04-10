import streamlit as st
import time
import google.generativeai as genai

# 1. Configuration de l'API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 🧠 LES OUTILS DE L'IA (Function Calling)
# ==========================================
# C'est ici qu'on définit ce que l'IA a le droit de faire.
# Les "docstrings" (les textes entre guillemets triples) sont CRUCIAUX : 
# c'est ce que l'IA lit pour comprendre à quoi sert l'outil !

def obtenir_info_trafic(ligne: str) -> str:
    """
    Récupère l'état du trafic en temps réel pour une ligne de métro ou RER.
    Args:
        ligne: Le nom de la ligne (ex: 'RER A', '1', '14', 'RER B').
    """
    # ⚠️ PLUS TARD : Tu remplaceras ce code par ta VRAIE fonction API IDFM
    # Pour l'instant, on simule des réponses pour vérifier que l'IA comprend
    ligne_up = ligne.upper()
    if "A" in ligne_up:
        return "Trafic fortement perturbé sur le RER A suite à un bagage oublié à Châtelet."
    elif "14" in ligne_up:
        return "Ligne 14 fermée pour cause de travaux de prolongement."
    else:
        return f"Trafic parfaitement normal sur la ligne {ligne}."

# 2. Initialisation du modèle en lui branchant notre outil
# On active 'enable_automatic_function_calling' : le SDK Google gèrera tout tout seul !
model = genai.GenerativeModel(
    'gemini-1.5-flash', 
    tools=[obtenir_info_trafic]
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Posez-moi vos questions sur le trafic (ex: RER A, Ligne 14...).</p>", unsafe_allow_html=True)

    # Initialisation du CHAT GEMINI dans la mémoire (pour garder le contexte)
    if "chat_session" not in st.session_state:
        # On démarre une vraie session de chat avec Gemini
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
        # On initialise aussi notre affichage local
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis connecté au réseau. Demande-moi l'état d'une ligne ! 🚇"}
        ]

    # Conteneur avec scroll
    chat_container = st.container(height=350)
    
    # Affichage de l'historique
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Barre de saisie
    if prompt := st.chat_input("Ex: Y a-t-il des problèmes sur le RER A ?"):
        # Affichage immédiat de la question
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        st.rerun() 
        
    # --- LA MAGIE OPÈRE ICI ---
    if st.session_state.messages_ia and st.session_state.messages_ia[-1]["role"] == "user":
        dernier_prompt = st.session_state.messages_ia[-1]["content"]
        
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je consulte le réseau...*")
                
                try:
                    # On envoie le message au chat Gemini.
                    # S'il a besoin de l'info trafic, il va de lui-même exécuter
                    # la fonction 'obtenir_info_trafic', lire le résultat, et te faire une belle phrase !
                    response = st.session_state.chat_session.send_message(
                        f"Consigne : Tu es l'assistant de l'app Grand Paname. Réponds de façon concise. Question : {dernier_prompt}"
                    )
                    reponse_finale = response.text
                    
                    message_placeholder.markdown(reponse_finale)
                    
                except Exception as e:
                    reponse_finale = "Oups, impossible de joindre le centre de contrôle. 😅"
                    message_placeholder.markdown(reponse_finale)
                    print(f"Erreur API : {e}")
                
        st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
