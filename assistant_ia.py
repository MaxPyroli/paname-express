import streamlit as st
import time
import google.generativeai as genai
# Importe ta vraie fonction ici ! (Remplace 'ton_fichier' par api ou utils)
from api_idfm import demander_info_trafic

# 1. Configuration de l'API
# On s'assure que la clé est bien lue
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Attention : Clé API introuvable dans st.secrets !")

# ==========================================
# 🧠 L'OUTIL DE L'IA (Le Pont)
# ==========================================
def outil_info_trafic_ia(nom_ligne: str) -> str:
    """
    Récupère l'état du trafic en temps réel pour une ligne de métro ou RER.
    Args:
        nom_ligne: Le nom de la ligne demandée (ex: 'RER A', '1', '14').
    """
    # 1. 🔄 CONVERSION NOM -> ID (À FAIRE TOI-MÊME)
    # L'IA va envoyer "RER A" ou "1". Il faut le traduire en IDFM.
    # Tu dois avoir un dictionnaire de lignes dans ton projet. 
    # Exemple (à adapter avec tes vrais IDs) :
    dico_lignes = {
        "RER A": "line:IDFM:C01742",
        "RER B": "line:IDFM:C01743",
        "1": "line:IDFM:C01371",
        "14": "line:IDFM:C01386"
    }
    
    # On nettoie un peu le nom envoyé par l'IA au cas où
    nom_propre = nom_ligne.upper().replace("LIGNE ", "").strip()
    
    line_id = dico_lignes.get(nom_propre)
    
    if not line_id:
        return f"Je ne trouve pas l'ID de la ligne {nom_ligne}. Demande à l'utilisateur de préciser."

    # 2. ⚡ APPEL À TA VRAIE FONCTION
    alertes = demander_info_trafic(line_id, nom_propre)

    # 3. 📝 TRADUCTION POUR LE CERVEAU DE L'IA
    if len(alertes) == 0:
        return f"Il n'y a aucune alerte en cours. Le trafic est normal sur la ligne {nom_ligne}."
    
    # S'il y a des alertes, on crée un petit rapport texte pour l'IA
    rapport = f"Voici les problèmes actuels sur la ligne {nom_ligne} :\n"
    for alerte in alertes:
        rapport += f"- {alerte['header']} : {alerte['text']}\n"
        
    return rapport

# Initialisation du modèle avec notre NOUVEL outil
model = genai.GenerativeModel(
    'gemini-2.5-flash', 
    tools=[outil_info_trafic_ia]
)
