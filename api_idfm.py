import requests
import streamlit as st
import re
from constants import API_KEY, BASE_URL
from datetime import datetime

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
@st.cache_data(ttl=300)
def demander_info_trafic(line_id):
    """Récupère les bulletins avec horloge intelligente pour les travaux."""
    suffixe = f"lines/{line_id}/line_reports"
    data = demander_api(suffixe)
    
    alertes = []
    if data and 'disruptions' in data:
        heure_actuelle = datetime.now().hour
        
        for disruption in data['disruptions']:
            status = disruption.get('status', '')
            messages = disruption.get('messages', [])
            texte_complet = " ".join([m.get('text', '') for m in messages])
            header = disruption.get('header_text', '')
            
            if not texte_complet:
                texte_complet = header

            texte_lower = texte_complet.lower()

            # 🗑️ LE BOUCLIER ANTI-SPAM & ANTI-PUB 🗑️
            # Si le texte contient un de ces mots, on jette l'alerte à la poubelle
            mots_spam = [
                "ascenseur", "escalator", "bagage", 
                "@idfmobilites", "ouvrez l'app", "app de mobilité",
                "dos du téléphone", "titres-et-tarifs", "rechargez",
                "files d'attente", "bonne nouvelle", "mode raccourci",
                "titre sur votre téléphone", "lutte contre la fraude"
            ]
            
            # On vérifie si un mot spam est dans le texte
            if any(mot in texte_lower for mot in mots_spam):
                continue

            # ... (juste en dessous de la suppression des ascenseurs)

            severity_obj = disruption.get('severity', {})
            effect = severity_obj.get('effect', '')
            
            # 🔥 LE NOUVEAU SCORING "FILET DE SÉCURITÉ" 🔥
            score = 10 
            
            # On prépare nos listes de mots-clés AVANT les conditions (la voilà la correction !)
            mots_coupure = ["interrompu", "fermé", "fermeture", "coupé", "aucun train"]
            mots_pertu = ["perturbé", "non desservi", "dévié", "ralenti", "retard"]

            # On vérifie les coupures
            if effect == "NO_SERVICE" or any(mot in texte_lower for mot in mots_coupure):
                score = 50 
            # On vérifie les perturbations
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE"] or any(mot in texte_lower for mot in mots_pertu):
                score = 20 

            # 🌙 L'ANTI-PANIQUE HORAIRE (Le réveil intelligent)
            mots_nuit = r"(?i)(dès|à partir de)\s*(2[0-3]|0[0-4])[:h]|en soirée|les soirs|nuits?"
            if re.search(mots_nuit, texte_lower):
                if 5 <= heure_actuelle < 17:
                    # Entre 5h et 17h : Trop tôt, on jette
                    continue 
                elif 17 <= heure_actuelle < 21:
                    # Entre 17h et 21h : On rétrograde en Orange (score 20)
                    if score >= 40:
                        score = 20

            # On valide l'alerte si elle est active
            if score >= 10 and status == 'active':
                alertes.append({'text': texte_complet, 'severity': score, 'header': header})
                
    return alertes
