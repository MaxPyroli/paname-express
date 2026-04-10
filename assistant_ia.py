import streamlit as st
import time

# Le décorateur transforme cette fonction en fenêtre pop-up (modale) !
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Posez-moi vos questions sur le trafic ou les horaires.</p>", unsafe_allow_html=True)

    # 1. Initialisation de la mémoire
    if "messages_ia" not in st.session_state:
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis l'assistant IA. Demande-moi ce que tu veux sur le réseau ! 🚇"}
        ]

    # 2. Conteneur avec une hauteur fixe pour scroller à l'intérieur
    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 3. La barre de saisie (qui se calera parfaitement en bas de la modale)
    if prompt := st.chat_input("Ex : Y a-t-il des retards sur la ligne 1 ?"):
        
        # On sauvegarde et on affiche la question
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        # On force le rafraîchissement de la modale pour afficher la question de suite
        st.rerun() 
        
    # --- LOGIQUE DE RÉPONSE (Si le dernier message vient de l'utilisateur) ---
    if st.session_state.messages_ia and st.session_state.messages_ia[-1]["role"] == "user":
        dernier_prompt = st.session_state.messages_ia[-1]["content"]
        
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *L'assistant réfléchit...*")
                time.sleep(1.5) # Faux temps de chargement
                
                reponse = f"J'ai bien noté ta question : **{dernier_prompt}** ! Mon cerveau n'est pas encore branché à l'API, mais ça ne saurait tarder."
                message_placeholder.markdown(reponse)
                
        # On sauvegarde la réponse
        st.session_state.messages_ia.append({"role": "assistant", "content": reponse})
