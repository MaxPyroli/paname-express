import streamlit as st
import time

def afficher_assistant_ia():
    # En-tête de la page
    st.markdown("<h2 class='section-header'>🤖 Assistant Paname (Bêta)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888; font-style: italic;'>Posez-moi vos questions sur le trafic, les itinéraires ou les horaires en langage naturel.</p>", unsafe_allow_html=True)

    # 1. Initialisation de la mémoire (pour que l'IA se souvienne de la conversation)
    if "messages_ia" not in st.session_state:
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis ton nouvel assistant Grand Paname. Que veux-tu savoir aujourd'hui ? (Ex: *Y a-t-il des problèmes sur le RER A ?*)"}
        ]

    # 2. Affichage de l'historique des messages
    for message in st.session_state.messages_ia:
        # st.chat_message crée automatiquement les belles bulles avec les icônes
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. La barre de saisie utilisateur (en bas de l'écran)
    if prompt := st.chat_input("Demandez une info trafic ou un horaire..."):
        
        # On affiche immédiatement la question de l'utilisateur
        with st.chat_message("user"):
            st.markdown(prompt)
        # On la sauvegarde dans la mémoire
        st.session_state.messages_ia.append({"role": "user", "content": prompt})

        # 4. Simulation de la réflexion de l'IA
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 *Recherche dans les données du réseau...*")
            
            # On simule un petit temps d'attente (comme si on interrogeait l'API)
            time.sleep(1.5) 
            
            # La réponse "bouchon" (placeholder)
            reponse = f"J'ai bien compris que tu voulais savoir : **« {prompt} »**.\n\n*⚠️ Pour l'instant, mon cerveau n'est pas encore branché. Mais mon interface est prête !*"
            
            # On remplace le texte de chargement par la réponse finale
            message_placeholder.markdown(reponse)
            
        # On sauvegarde la réponse dans la mémoire
        st.session_state.messages_ia.append({"role": "assistant", "content": reponse})
