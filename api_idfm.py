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
    """Récupère les bulletins avec horloge intelligente et filtre anti-pollution."""
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
            mots_spam = [
                "ascenseur", "escalator", "bagage", 
                "@idfmobilites", "ouvrez l'app", "app de mobilité",
                "dos du téléphone", "titres-et-tarifs", "rechargez",
                "files d'attente", "bonne nouvelle", "mode raccourci",
                "titre sur votre téléphone", "lutte contre la fraude"
            ]
            if any(mot in texte_lower for mot in mots_spam):
                continue

            # 🛑 ANTI-POLLUTION INTER-LIGNES (Smarter Version) 🛑
            if nom_ligne:
                match_autre = re.search(r"(?i)la ligne\s+([a-zA-Z0-9]+)\s+(?:est|sera|ne|circule)", texte_lower)
                if match_autre:
                    ligne_mentionnee = match_autre.group(1).lower()
                    nom_propre = str(nom_ligne).lower()
                    
                    # On nettoie les préfixes "ex", "express", ou "bus" pour garder que le numéro
                    coeur_mention = re.sub(r'^(ex|express|bus)\s*', '', ligne_mentionnee)
                    coeur_nom = re.sub(r'^(ex|express|bus)\s*', '', nom_propre)
                    
                    # Si les coeurs ne se ressemblent pas (ex: "19" vs "6"), on jette !
                    if coeur_nom not in coeur_mention and coeur_mention not in coeur_nom:
                        continue 

            severity_obj = disruption.get('severity', {})
            effect = severity_obj.get('effect', '')
            
            # 🔥 LE NOUVEAU SCORING "FILET DE SÉCURITÉ" 🔥
            score = 10 
            mots_coupure = ["interrompu", "fermé", "fermeture", "coupé", "aucun train"]
            mots_pertu = ["perturbé", "non desservi", "dévié", "déviation", "ralenti", "retard"]

            # 🔥 CORRECTION : Si c'est dévié, c'est Orange (20), pas Rouge (50) !
            if any(mot in texte_lower for mot in ["dévié", "déviation"]):
                score = 20
            elif effect == "NO_SERVICE" or any(mot in texte_lower for mot in mots_coupure):
                score = 50 
            elif effect in ["SIGNIFICANT_DELAYS", "REDUCED_SERVICE", "DETOUR", "MODIFIED_SERVICE"] or any(mot in texte_lower for mot in mots_pertu):
                score = 20 

            # 🌙 L'ANTI-PANIQUE HORAIRE (Le réveil intelligent)
            mots_nuit = r"(?i)(dès|à partir de)\s*(2[0-3]|0[0-4])[:h]|en soirée|les soirs|nuits?"
            if re.search(mots_nuit, texte_lower):
                if 5 <= heure_actuelle < 17:
                    continue 
                elif 17 <= heure_actuelle < 21:
                    if score >= 40:
                        score = 20

            if score >= 10 and status == 'active':
                alertes.append({'text': texte_complet, 'severity': score, 'header': header})
                
    return alertes
