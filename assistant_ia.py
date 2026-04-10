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
# 🧰 OUTIL 2 : PROCHAINS DÉPARTS (100% AUTOMATIQUE 🤖)
# ==========================================
def outil_prochains_departs_ia(nom_station: str) -> str:
    """Récupère les horaires des prochains départs pour une gare."""
    
    print(f"🚀 L'IA cherche la gare : {nom_station}")
    
    try:
        # 1. RECHERCHE DE L'ID (Automatique via l'API)
        # On utilise le point d'accès /places pour chercher le texte tapé par l'utilisateur
        recherche_data = demander_api(f"places?q={nom_station}")
        
        # On vérifie si l'API a trouvé quelque chose
        if not recherche_data or 'places' not in recherche_data or len(recherche_data['places']) == 0:
            return f"Je n'ai pas réussi à trouver l'arrêt '{nom_station}' sur le réseau."
            
        # On prend l'ID du tout premier résultat (le plus pertinent)
        stop_id = recherche_data['places'][0]['id']
        nom_trouve = recherche_data['places'][0].get('name', nom_station)
        
        # 2. RÉCUPÉRATION DES 10 PROCHAINS TRAINS (Rapide !)
        data = demander_api(f"stop_areas/{stop_id}/departures?count=10")
        
        if not data or 'departures' not in data or len(data['departures']) == 0:
            return f"Aucun départ trouvé pour {nom_trouve} actuellement."
            
        # 3. CRÉATION DU RAPPORT POUR L'IA
        rapport = f"Prochains départs à {nom_trouve} :\n"
        lignes_vues = 0
        
        for d in data['departures']:
            if lignes_vues >= 6:  
                break
                
            info = d['display_informations']
            ligne = info.get('code', '?')
            dest = info.get('direction', 'Inconnue')
            
            try:
                time_str = d['stop_date_time']['departure_date_time']
                heure_min = time_str.split('T')[1][:4]
                heure_formatee = f"{heure_min[:2]}h{heure_min[2:]}"
            except:
                heure_formatee = "Bientôt"
                
            rapport += f"- Ligne {ligne} vers {dest} à {heure_formatee}\n"
            lignes_vues += 1
            
        return rapport
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return f"Erreur réseau pour {nom_station}. Le serveur est peut-être occupé."

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
    'gemini-3.1-flash-lite-preview', # Garde celui qui fonctionnait pour toi !
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    system_instruction=personnalite
)

# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
@st.dialog("🤖 Assistant Paname")
def ouvrir_assistant():
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Trafic, horaires, itinéraires... Demandez-moi tout !</p>", unsafe_allow_html=True)

    # 1. ON CHANGE LE NOM DES VARIABLES POUR VIDER LE CACHE
    if "chat_session_v2" not in st.session_state:
        # Assure-toi que ton modèle s'appelle bien model = genai.GenerativeModel('gemini-3.1-flash', ...) plus haut !
        st.session_state.chat_session_v2 = model.start_chat(enable_automatic_function_calling=True)
        st.session_state.messages_ia_v2 = [
            {"role": "assistant", "content": "Coucou ! 👋 J'ai un tout nouveau cerveau. Tu vas où de beau aujourd'hui ? 🚇"}
        ]

    chat_container = st.container(height=350)
    
    with chat_container:
        for message in st.session_state.messages_ia_v2:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Dans combien de temps est le prochain RER A à Châtelet ?"):
        st.session_state.messages_ia_v2.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 *Je fouille dans les serveurs...*")
                
                try:
                    # On utilise bien la nouvelle session V2
                    response = st.session_state.chat_session_v2.send_message(prompt)
                    reponse_finale = response.text
                    message_placeholder.markdown(reponse_finale)
                    
                    st.session_state.messages_ia_v2.append({"role": "assistant", "content": reponse_finale})
                    
                except Exception as e:
                    erreur_brute = str(e)
                    
                    if "429" in erreur_brute or "Quota exceeded" in erreur_brute:
                        match = re.search(r'retry in (\d+)', erreur_brute)
                        if match:
                            secondes = match.group(1)
                            erreur_texte = f"**Oups !** 🥵 Laisse-moi reprendre mon souffle pendant environ **{secondes} secondes**. ☕"
                        else:
                            erreur_texte = "**Oups !** 🥵 Le serveur surchauffe. Laisse-moi souffler une petite minute. ☕"
                        
                        message_placeholder.warning(erreur_texte)
                    else:
                        message_placeholder.error(f"Erreur technique : {erreur_brute}")
