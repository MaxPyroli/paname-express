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

@st.cache_data(ttl=300) # Cache de 5 minutes
def demander_info_trafic(line_id):
    """Récupère les bulletins de trafic pour une ligne donnée."""
    suffixe = f"lines/{line_id}/line_reports"
    data = demander_api(suffixe)
    
    alertes = []
    # On tape dans 'disruptions' et pas dans 'line_reports' !
    if data and 'disruptions' in data:
        for disruption in data['disruptions']:
            # La sévérité est un dictionnaire complexe dans Navitia
            severity_obj = disruption.get('severity', {})
            
            # On regarde l'effet réel de la panne
            effect = severity_obj.get('effect', '') if isinstance(severity_obj, dict) else ''
            
            # On le traduit en score pour notre application
            if effect == "NO_SERVICE":
                score = 50 # 🚨 Interruption totale (Rouge)
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE"]:
                score = 20 # ⚠️ Perturbation (Orange)
            else:
                score = 0  # Info mineure ou travaux (On ignore)
                
            for info in disruption.get('messages', []):
                text = info.get('text', '')
                if text and score > 0:
                    alertes.append({'text': text, 'severity': score})
                    
    return alertes
