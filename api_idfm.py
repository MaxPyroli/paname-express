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
    """Récupère les bulletins de la ligne en se basant UNIQUEMENT sur le statut 'en cours' de l'API."""
    suffixe = f"lines/{line_id}/line_reports"
    data = demander_api(suffixe)
    
    alertes = []
    if data and 'disruptions' in data:
        for disruption in data['disruptions']:
            # On récupère le statut et on le met en minuscules
            status = disruption.get('status', '').lower()
            
            # 🛑 LE SEUL ET UNIQUE FILTRE : On ne garde que ce qui est "En cours" (Actif)
            if status not in ['active', 'in_progress']:
                continue

            # --- Extraction du texte ---
            messages = disruption.get('messages', [])
            texte_complet = " ".join([m.get('text', '') for m in messages])
            header = disruption.get('header_text', '')
            
            if not texte_complet:
                texte_complet = header

            texte_lower = texte_complet.lower()
            
            # 🗑️ LE RETOUR DU BOUCLIER ANTI-SPAM 🗑️
            mots_spam = [
                "ascenseur", "escalator", 
                "dos du téléphone", "titres-et-tarifs", "rechargez",
                "files d'attente", "bonne nouvelle", "mode raccourci",
                "titre sur votre téléphone", "lutte contre la fraude"
            ]
            if any(mot in texte_lower for mot in mots_spam):
                continue
                
            severity_obj = disruption.get('severity', {})
            effect = severity_obj.get('effect', '')
            
            # 🔥 LE SCORING BASIQUE (Pour garder les bonnes couleurs) 🔥
            score = 10 
            mots_coupure = ["interrompu", "fermé", "fermeture", "coupé", "aucun train"]
            mots_pertu = ["perturbé", "non desservi", "dévié", "déviation", "ralenti", "retard"]

            if any(mot in texte_lower for mot in ["dévié", "déviation"]):
                score = 20
            elif effect == "NO_SERVICE" or any(mot in texte_lower for mot in mots_coupure):
                score = 50 
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE"] or any(mot in texte_lower for mot in mots_pertu):
                score = 20 

            # On ajoute l'alerte validée
            alertes.append({'text': texte_complet, 'severity': score, 'header': header})
                
    return alertes
