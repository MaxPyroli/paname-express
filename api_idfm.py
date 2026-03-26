import requests
import streamlit as st
import re
from constants import API_KEY, BASE_URL
from datetime import datetime
from zoneinfo import ZoneInfo

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

def demander_arrets_proches(lat, lon, rayon=3000): 
    # ATTENTION AU PIÈGE NAVITIA : C'est {longitude};{latitude} !
    # 🚀 NOUVEAU : On ajoute &count=60 pour forcer la recherche au-delà des 10 premiers bus
    suffixe = f"coords/{lon};{lat}/places_nearby?type[]=stop_area&distance={rayon}&count=60"
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
def demander_info_trafic(line_id, nom_ligne=""):
    suffixe = f"lines/{line_id}/line_reports"
    data = demander_api(suffixe)
    
    alertes = []
    if data and 'disruptions' in data:
        for disruption in data['disruptions']:
            # On chope le statut brut
            status = disruption.get('status', 'STATUT_VIDE')
            
            # On chope le texte
            messages = disruption.get('messages', [])
            texte_complet = " ".join([m.get('text', '') for m in messages])
            if not texte_complet:
                texte_complet = disruption.get('header_text', 'ALERTE SANS TEXTE')

            # ☢️ AUCUN FILTRE : ON PREND ABSOLUMENT TOUT EN ROUGE !
            alertes.append({
                'text': f"[DEBUG STATUT: {status}] {texte_complet}", 
                'severity': 50, 
                'header': disruption.get('header_text', '')
            })
            
    return alertes
