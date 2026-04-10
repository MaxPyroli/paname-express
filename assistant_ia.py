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
    """Récupère les horaires uniques par direction pour une gare."""
    try:
        nom_station_propre = urllib.parse.quote(nom_station)
        recherche_data = demander_api(f"places?q={nom_station_propre}")
        
        if not recherche_data or not recherche_data.get('places'):
            return f"Je n'ai pas trouvé la gare '{nom_station}'."
            
        stop_id = recherche_data['places'][0]['id']
        nom_trouve = recherche_data['places'][0].get('name', nom_station)
        
        # On demande 20 trains pour être sûr d'avoir plusieurs directions
        data = demander_api(f"stop_areas/{stop_id}/departures?count=20")
        
        if not data or not data.get('departures'):
            return f"Aucun départ à {nom_trouve}."
            
        # --- LOGIQUE DE TRI ET FILTRAGE ---
        directions_vues = set()
        departs_uniques = []
        
        for d in data['departures']:
            # ... (garde le début de la boucle identique) ...
            
            if cle_unique not in directions_vues:
                directions_vues.add(cle_unique)
                
                try:
                    # 1. On récupère l'heure du train (ISO format)
                    time_str = d['stop_date_time']['departure_date_time']
                    dep_time = datetime.strptime(time_str, '%Y%m%dT%H%M%S')
                    
                    # 2. On récupère l'heure actuelle SANS fuseau pour comparer des pommes avec des pommes
                    # On utilise utcnow() pour éviter les soucis de serveurs décalés
                    now = datetime.now() 
                    
                    # Si tu es sur Streamlit Cloud, on ajoute manuellement les 2h de décalage de Paris
                    # ou on utilise cette méthode plus propre :
                    import pytz
                    paris_tz = pytz.timezone('Europe/Paris')
                    now_paris = datetime.now(paris_tz).replace(tzinfo=None) 
                    dep_time_clean = dep_time.replace(tzinfo=None)

                    diff = int((dep_time_clean - now_paris).total_seconds() / 60)
                    
                    if diff <= 0: 
                        temps = "À quai"
                    elif diff > 60:
                        temps = f"{dep_time_clean.strftime('%H:%M')}"
                    else:
                        temps = f"{diff} min"
                except Exception as e:
                    temps = "Heure indisponible"

        # On limite à 8 directions max pour rester concis
        rapport = f"Voici ce que j'ai trouvé pour {nom_trouve} :\n"
        for dep in departs_uniques[:8]:
            icone = "🚇" if "RER" in dep['mode'] or "METRO" in dep['mode'] else "🚌"
            rapport += f"- {icone} **{dep['ligne']}** vers **{dep['dest']}** : ⏱️ {dep['temps']}\n"
            
        return rapport
        
    except Exception as e:
        return f"Petit souci technique pour {nom_station}."
# ==========================================
# 🧠 LE CERVEAU & LA PERSONNALITÉ (SYNTAXE V2)
# ==========================================
personnalite = """
Tu es l'assistant Grand Paname. Sois bref, efficace et chaleureux. ✨

RÈGLES DE RÉPONSE :
1. Affiche EXACTEMENT la liste fournie par l'outil, sans regrouper les horaires.
2. N'invente jamais d'horaires. Si l'outil affiche "15h", n'écris pas "08h".
3. Un seul train par direction.
4. Finis par une micro-phrase de bon voyage.
"""

config_ia = types.GenerateContentConfig(
    system_instruction=personnalite,
    tools=[outil_info_trafic_ia, outil_prochains_departs_ia],
    temperature=0.6 # On remonte un peu pour plus de chaleur humaine
)
# ==========================================
# 🎨 L'INTERFACE DE LA MODALE
# ==========================================
@st.dialog("🤖 Assistant Paname") # On retire le width="large"
def ouvrir_assistant():
    # 👇 Ce petit bloc de code ajuste la largeur précisément (ici 600px)
    st.markdown(
        """
        <style>
            div[data-testid="stDialog"] div[role="dialog"] {
                max-width: 650px !important; /* Ajuste ce chiffre selon ton goût */
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<p style='color: #888; font-size: 0.9em; margin-top: -10px;'>Trafic, horaires, itinéraires... Demandez-moi tout !</p>", unsafe_allow_html=True)
    
    # ... (Le reste de ton code avec la hauteur à 500 ou 600) ...
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
