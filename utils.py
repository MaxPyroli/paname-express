import os
import base64
import re
from datetime import datetime
import pytz
from api_idfm import demander_lignes_arret, demander_info_trafic

def get_img_as_base64(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: 
        return None

def get_svg_inline(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        svg_content = re.sub(r'<\?xml.*?\?>', '', svg_content)
        if '<svg' in svg_content:
            svg_content = svg_content.replace('<svg', '<svg class="mode-icon-inline" fill="currentColor"', 1)
        return svg_content
    except Exception: 
        return None

def normaliser_mode(mode_brut):
    if not mode_brut: return "AUTRE"
    m = mode_brut.upper()
    if "FUNI" in m or "CABLE" in m or "TÉLÉPHÉRIQUE" in m: return "CABLE"
    if "RER" in m or "RAPIDTRANSIT" in m: return "RER"
    if "TRAIN" in m or "RAIL" in m or "SNCF" in m or "EXPRESS" in m or "TER" in m: return "TRAIN"
    if "METRO" in m or "MÉTRO" in m: return "METRO"
    if "TRAM" in m: return "TRAM"
    if "BUS" in m: return "BUS"
    return "AUTRE"

def clean_code_line(code):
    return str(code).strip().upper()

def format_html_time(heure_str, data_freshness):
    paris_tz = pytz.timezone('Europe/Paris')
    obj_naive = datetime.strptime(heure_str, '%Y%m%dT%H%M%S')
    obj = paris_tz.localize(obj_naive)
    now = datetime.now(paris_tz)
    delta = int((obj - now).total_seconds() / 60)
    
    if data_freshness == 'base_schedule':
        return (2000, f"<span class='text-blue'>~{obj.strftime('%H:%M')}</span>")
    if delta > 120: return (3000, "<span class='service-end'>Service terminé</span>")
    if delta <= 0: return (0, "<span class='text-red'>À quai</span>")
    if delta == 1: return (1, "<span class='blink text-orange'>À l'approche</span>")
    if delta < 5: return (delta, f"<span class='text-orange'>{delta} min</span>")
    return (delta, f"<span class='text-green'>{delta} min</span>")

def get_all_changelogs():
    log_dir = "changelogs"
    all_notes = []
    if not os.path.exists(log_dir): return ["*Aucune note de version trouvée.*"]
    files = [f for f in os.listdir(log_dir) if f.endswith(".md")]
    def version_key(filename):
        try:
            clean = filename.lower().replace('v', '').replace('.md', '')
            return [int(part) for part in clean.split('.') if part.isdigit()]
        except: return [0]
    files.sort(key=version_key, reverse=True)
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f: all_notes.append(f.read())
        except Exception as e: all_notes.append(f"Erreur de lecture de {filename}: {e}")
    return all_notes if all_notes else ["*Aucune note de version trouvée.*"]

def analyser_importance_arret(stop_area_node):
    meilleur_rang = 99
    meilleur_mode = "AUTRE"
    hierarchie = {"RER": 1, "TRAIN": 2, "METRO": 3, "CABLE": 4, "TRAM": 5, "BUS": 6, "AUTRE": 99}
    modes_a_tester = []
    
    if 'commercial_modes' in stop_area_node:
        modes_a_tester.extend([m.get('id', '') + " " + m.get('name', '') for m in stop_area_node['commercial_modes']])
    if 'physical_modes' in stop_area_node:
        modes_a_tester.extend([m.get('id', '') + " " + m.get('name', '') for m in stop_area_node['physical_modes']])
        
    if not modes_a_tester:
        stop_id = stop_area_node.get('id')
        if stop_id:
            data_lines = demander_lignes_arret(stop_id)
            if data_lines and 'lines' in data_lines:
                for line in data_lines['lines']:
                    if 'commercial_mode' in line:
                        m = line['commercial_mode']
                        if isinstance(m, dict):
                            modes_a_tester.append(m.get('id', '') + " " + m.get('name', ''))
                    if 'physical_mode' in line:
                        m = line['physical_mode']
                        if isinstance(m, dict):
                            modes_a_tester.append(m.get('id', '') + " " + m.get('name', ''))
                        elif isinstance(m, str):
                            modes_a_tester.append(m)

    if not modes_a_tester:
        nom_arret = stop_area_node.get('name', '').upper()
        if "GARE DE" in nom_arret or "GARE" in nom_arret or "RER" in nom_arret:
            modes_a_tester.append("TRAIN")
        elif "METRO" in nom_arret or "MÉTRO" in nom_arret:
            modes_a_tester.append("METRO")
        elif "TRAMWAY" in nom_arret or "TRAM" in nom_arret:
            modes_a_tester.append("TRAM")
        else:
            modes_a_tester.append("BUS")
            
    for nom_mode in modes_a_tester:
        mode_norm = normaliser_mode(nom_mode)
        rang = hierarchie.get(mode_norm, 99)
        if rang < meilleur_rang:
            meilleur_rang = rang
            meilleur_mode = mode_norm
            
    tags = {
        "RER": "[ RER/TRAIN ]", "TRAIN": "[ TRAIN ]", "METRO": "[ MÉTRO ]", 
        "TRAM": "[ TRAM ]", "CABLE": "[ CÂBLE ]", "BUS": "", "AUTRE": ""
    }
    return meilleur_rang, tags.get(meilleur_mode, "")

def get_alerte_style(severity):
    """Renvoie la couleur et l'icône selon la gravité du problème."""
    if severity >= 40: # Gros problèmes / Interruption
        return "🔴", "#e74c3c"
    if severity >= 10: # Travaux / Ralentissements
        return "⚠️", "#f39c12"
    return None, None

def synthetiser_alerte(texte):
    """Le juste milieu : une phrase complète, mais sans les bégaiements."""
    # Nettoyage HTML de base
    texte = re.sub(r'<[^>]+>', '', texte.replace('\n', ' ')).strip()
    
    # On supprime le bégaiement "Trafic interrompu" vu qu'on l'écrit déjà en gros en rouge
    texte = re.sub(r'(?i)\s*-\s*(Le )?trafic (est )?interrompu\s*', ' - ', texte)
    texte = re.sub(r'(?i)^(Le )?trafic (est )?interrompu\s*[-:]?\s*', '', texte)
    
    # On coupe au premier VRAI point pour éviter le pavé
    phrase = texte.split('.')[0].strip()
    
    # On limite à 120 caractères (assez long pour les dates/lieux, assez court pour lire)
    if len(phrase) > 120:
        phrase = phrase[:120] + "..."
        
    if phrase:
        phrase = phrase[0].upper() + phrase[1:]
        
    return phrase
def nettoyer_texte_details(texte):
    """Nettoie le texte brut (Anti-bégaiement, codes internes) pour un affichage clair."""
    # 1. On tronque les redondances polluantes à la fin des messages
    texte = re.sub(r"(?i)\s*Raison\s*:.*", "", texte)
    
    # 2. Nettoyage de base et Anti-bégaiement radical
    texte = re.sub(r'([A-Za-z0-9]+\s*\(\d+\)\s*)+-\s*', '', texte)
    texte = re.sub(r'Fi_\d+_\d+', '', texte)
    texte = re.sub(r'(.{20,})\1+', r'\1', texte) 
    texte = texte.replace("Arrêt(s) non desservi(s) Arrêt(s) non desservi(s)", "Arrêt(s) non desservi(s)")
    
    # 3. Séparer les mots collés de l'API & normaliser la ponctuation
    texte = texte.replace("’", "'").replace("‘", "'").replace("«", '"').replace("»", '"')
    texte = re.sub(r"([a-z])(L'arrêt|Les arrêts|Arrêt)", r"\1 \2", texte)
    
    return texte.strip()

def determiner_type_perturbation(texte, header):
    """Déduit le type et bloque les alertes de plus de 7 jours."""
    t_low = texte.lower()
    
    # 📅 LE RADAR TEMPOREL 7 JOURS
    mois_fr = {
        "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
    }
    jours = r"(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
    mois_regex = r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
    
    # On capture le jour, le mois, ET l'année (si elle est écrite)
    match_date = re.search(fr"(?i)(?:du|le|à partir du)\s+{jours}?\s*(\d{{1,2}})\s+{mois_regex}(?:\s+(\d{{4}}))?", t_low)
    
    if match_date:
        jour = int(match_date.group(1))
        mois_nom = match_date.group(2).lower()
        mois = mois_fr.get(mois_nom)
        annee_str = match_date.group(3)
        
        maintenant = datetime.now()
        annee = int(annee_str) if annee_str else maintenant.year
        
        try:
            date_alerte = datetime(annee, mois, jour)
            if date_alerte > maintenant:
                diff_jours = (date_alerte - maintenant).days
                if diff_jours > 7:
                    # C'est dans plus de 7 jours : On donne le code secret pour bloquer l'affichage
                    return "TROP_LOIN"
                else:
                    return f"À venir (dès le {jour} {mois_nom})"
        except ValueError:
            pass # Si la date est invalide, on ignore l'erreur

    # --- RESTE DES FILTRES CLASSIQUES ---
    # 🥇 PRIORITÉ 1 : Les arrêts sautés (On le met au-dessus !)
    if "non desservi" in t_low or "plus desservi" in t_low or "pas desservi" in t_low: 
        return "Arrêt(s) non desservi(s)"

    # 🥈 PRIORITÉ 2 : Les travaux du soir
    if re.search(r"(?i)(dès|à partir de)\s*(2[0-3]|0[0-4])[:h]|en soirée|les soirs|nuits?", t_low): 
        return "Travaux ce soir"
    if "dévi" in t_low or "modifié" in t_low: return "Itinéraire dévié"
    if "ralentissement" in t_low or "retard" in t_low: return "Ralentissements"
    if "supprim" in t_low: return "Suppressions"
    if "brocante" in t_low or "manifestation" in t_low: return "Événement"
    
    if header and len(header) < 30: return header
    return "En cours"
