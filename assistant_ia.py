import streamlit as st
import google.generativeai as genai
from api_idfm import demander_info_trafic

# 1. Configuration de l'API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Attention : Clé API introuvable dans st.secrets !")

# ==========================================
# 🧠 L'OUTIL DE L'IA (Le Pont vers tes vraies données)
# ==========================================
def outil_info_trafic_ia(nom_ligne: str) -> str:
    """
    Récupère l'état du trafic en temps réel pour une ligne de métro ou RER.
    Args:
        nom_ligne: Le nom de la ligne demandée (ex: 'RER A', '1', '14', 'RER B').
    """
    # J'ai pré-rempli les vrais IDs IDFM pour te faire gagner du temps !
    dico_lignes = {
        "1": "line:IDFM:C01371", "2": "line:IDFM:C01372", "3": "line:IDFM:C01373",
        "4": "line:IDFM:C01374", "5": "line:IDFM:C01375", "6": "line:IDFM:C01376",
        "7": "line:IDFM:C01377", "8": "line:IDFM:C01378", "9": "line:IDFM:C01379",
        "10": "line:IDFM:C01380", "11": "line:IDFM:C01381", "12": "line:IDFM:C01382",
        "13": "line:IDFM:C01383", "14": "line:IDFM:C01386",
        "RER A": "line:IDFM:C01742", "RER B": "line:IDFM:C01743", 
        "RER C": "line:IDFM:C01727", "RER D": "line:IDFM:C01728", "RER E": "line:IDFM:C01729"
    }
    
    # Nettoyage de la demande de l'IA (si elle écrit "Ligne 14", on garde "14")
    nom_propre = str(nom_ligne).upper().replace("LIGNE ", "").strip()
    line_id = dico_lignes.get(nom_propre)
    
    if not line_id:
        return f"Désolé, je ne connais pas l'ID de la ligne {nom_ligne}. Demande à l'utilisateur de reformuler."

    try:
        # Appel de TA fonction ultra-robuste
        alertes = demander_info_trafic(line_id, nom_propre)
    except Exception as e:
        return f"Erreur technique lors de la récupération : {str(e)}"

    # Si la liste est vide, tout va bien
    if not alertes or len(alertes) == 0:
        return f"Il n'y a aucune alerte en cours. Le trafic est normal sur la ligne {nom_propre}."
    
    # S'il y a des alertes, on rédige un rapport brut pour l'IA
    rapport = f"Voici les problèmes actuels sur la ligne {nom_propre} :\n"
    for alerte in alertes:
        rapport += f"- {alerte.get('header', 'Alerte')} : {alerte.get('text', '')}\n"
        
    return rapport

# 2. Initialisation du Cerveau avec le nouveau modèle
model = genai.GenerativeModel(
    'gemini-3.1-flash-lite', 
    tools=[outil_info_trafic_ia]
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Je suis connecté aux serveurs d'Île-de-France Mobilités.</p>", unsafe_allow_html=True)
    # 👇 AJOUTE CES 3 LIGNES ICI 👇
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'flash-lite' in m.name:
            st.warning(m.name)
    # 👆 ---------------------- 👆
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages_ia = [
            {"role": "assistant", "content": "Salut ! Je suis ton assistant info trafic. Quelle ligne dois-tu prendre aujourd'hui ? 🚇"}
        ]

    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Quel est le trafic sur la 14 ?"):
        st.session_state.messages_ia.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je consulte le réseau IDFM...*")
                
                try:
                    # L'IA analyse la phrase, choisit la fonction, lit le retour, et répond !
                    response = st.session_state.chat_session.send_message(
                        f"Tu es l'assistant de l'app Grand Paname. Réponds de façon naturelle, concise et chaleureuse. Question : {prompt}"
                    )
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    st.session_state.messages_ia.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    erreur_texte = f"**Erreur technique :**\n`{str(e)}`"
                    message_placeholder.error(erreur_texte)
