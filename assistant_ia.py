import streamlit as st
import time
import google.generativeai as genai

# Configuration de l'API avec la clé secrète
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# On utilise le modèle Flash : ultra rapide et parfait pour du chat
model = genai.GenerativeModel('gemini-1.5-flash')

@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Posez-moi vos questions sur le trafic ou les horaires.</p>", unsafe_allow_html=True)

    if "messages_ia" not in st.session_state:
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis l'assistant IA de Grand Paname. Comment puis-je t'aider aujourd'hui ? 🚇"}
        ]

    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Posez votre question..."):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        st.rerun() 
        
    # --- LA MAGIE OPÈRE ICI ---
    if st.session_state.messages_ia and st.session_state.messages_ia[-1]["role"] == "user":
        dernier_prompt = st.session_state.messages_ia[-1]["content"]
        
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *L'assistant réfléchit...*")
                
                try:
                    # On crée un "contexte" pour que l'IA sache qui elle est
                    prompt_systeme = f"""Tu es l'assistant virtuel de l'application Grand Paname, une app de transports en Île-de-France. 
                    Réponds de manière concise, chaleureuse et utile à cette question de l'utilisateur : {dernier_prompt}"""
                    
                    # On envoie la requête à Gemini
                    response = model.generate_content(prompt_systeme)
                    reponse_finale = response.text
                    
                    # On affiche la vraie réponse !
                    message_placeholder.markdown(reponse_finale)
                    
                except Exception as e:
                    reponse_finale = "Oups, j'ai eu un petit problème de connexion avec mon cerveau. 😅"
                    message_placeholder.markdown(reponse_finale)
                    print(f"Erreur API : {e}")
                
        st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
