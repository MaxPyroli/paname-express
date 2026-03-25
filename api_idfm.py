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

@st.cache_data(ttl=86400) # En cache pour 24h, ça économise les requêtes !
def demander_coordonnees_arret(stop_id):
    """Récupère la latitude et longitude d'un arrêt précis."""
    data = demander_api(f"stop_areas/{stop_id}")
    if data and 'stop_areas' in data and len(data['stop_areas']) > 0:
        coord = data['stop_areas'][0].get('coord')
        if coord:
            import pandas as pd
            # Streamlit adore les DataFrames pour les cartes
            return pd.DataFrame({
                "lat": [float(coord['lat'])],
                "lon": [float(coord['lon'])]
            })
    return None
