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
            # 1. FILTRE ANTI-TRAVAUX RADICAL
            tags = [str(t).lower() for t in disruption.get('tags', [])]
            if "travaux" in tags:
                continue
                
            # 2. EXTRACTION DU TEXTE
            titre = disruption.get('header_text', '')
            if not titre:
                msgs = disruption.get('messages', [])
                if msgs:
                    titre = msgs[0].get('text', '')
                    
            # Double vérification : si ça parle de dates/périodes, c'est des travaux déguisés
            if "période :" in titre.lower() or "travaux" in titre.lower() or "dates :" in titre.lower():
                continue

            # 3. FORCER LA SÉVÉRITÉ
            severity_obj = disruption.get('severity', {})
            effect = severity_obj.get('effect', '')
            
            score = 0
            # Si l'API dit "pas de service" OU si le texte contient "interrompu", on force le ROUGE 🚨
            if effect == "NO_SERVICE" or "interrompu" in titre.lower():
                score = 50 
            # Sinon, si c'est perturbé, on met ORANGE ⚠️
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE"] or "perturbé" in titre.lower():
                score = 20 

            if score > 0 and titre:
                alertes.append({'text': titre, 'severity': score})
                
    return alertes
