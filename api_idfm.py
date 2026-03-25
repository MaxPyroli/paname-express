import requests
import streamlit as st
from constants import API_KEY, BASE_URL

def demander_api(suffixe):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/{suffixe}", headers=headers)
        return r.json()
    except Exception as e: 
        # On pourrait ajouter un st.error() ici plus tard pour mieux gérer les pannes !
        return None

@st.cache_data(ttl=3600)
def demander_lignes_arret(stop_id):
    headers = {'apiKey': API_KEY.strip()}
    try:
        r = requests.get(f"{BASE_URL}/stop_areas/{stop_id}/lines", headers=headers)
        return r.json()
    except: 
        return None

def demander_arrets_proches(lat, lon, rayon=3000): # <-- On passe à 3000 mètres
    # ATTENTION AU PIÈGE NAVITIA : C'est {longitude};{latitude} !
    suffixe = f"coords/{lon};{lat}/places_nearby?type[]=stop_area&distance={rayon}"
    return demander_api(suffixe)

@st.cache_data(ttl=86400)
def demander_coordonnees_arret(stop_id):
    """Récupère la latitude et longitude d'un arrêt précis."""
    data = demander_api(f"stop_areas/{stop_id}")
    if data and 'stop_areas' in data and len(data['stop_areas']) > 0:
        coord = data['stop_areas'][0].get('coord')
        if coord:
            # Plus besoin de Pandas, un dictionnaire classique suffit !
            return {
                "lat": [float(coord['lat'])],
                "lon": [float(coord['lon'])]
            }
    return None

@st.cache_data(ttl=300)
def demander_info_trafic(line_id):
    """Récupère les bulletins de trafic pour une ligne donnée."""
    suffixe = f"lines/{line_id}/line_reports"
    data = demander_api(suffixe)
    
    alertes = []
    if data and 'disruptions' in data:
        for disruption in data['disruptions']:
            # 1. LE FILTRE MAGIQUE : Seulement ce qui est en cours !
            if disruption.get('status', '') != 'active':
                continue

            # 2. RÉCUPÉRATION DU TEXTE
            messages = disruption.get('messages', [])
            texte_complet = " ".join([m.get('text', '') for m in messages])
            header = disruption.get('header_text', '') # Le titre court (ex: "Arrêt non desservi")
            
            if not texte_complet:
                texte_complet = header

            texte_lower = texte_complet.lower()

            # 3. ON DÉGAGE LA POLLUTION
            if "ascenseur" in texte_lower or "escalator" in texte_lower or "bagage" in texte_lower:
                continue

            # 4. ANALYSE DE LA GRAVITÉ
            severity_obj = disruption.get('severity', {})
            effect = severity_obj.get('effect', '')
            
            score = 0
            if effect == "NO_SERVICE" or "interrompu" in texte_lower:
                score = 50 # 🚨 Interruption
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR"] or "perturbé" in texte_lower or "non desservi" in texte_lower:
                score = 20 # ⚠️ Perturbation

            if score > 0 and texte_complet:
                # On sauvegarde aussi le titre court (header) pour le menu déroulant
                alertes.append({'text': texte_complet, 'severity': score, 'header': header})
                
    return alertes
