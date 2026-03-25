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

def generer_icones_html():
    mapping_files = {
        "RER":   "img/rer.svg",
        "TRAIN": "img/train.svg",
        "METRO": "img/metro.svg",
        "TRAM":  "img/tram.svg",
        "CABLE": "img/cable.svg",
        "BUS":   "img/bus.svg",
        "AUTRE": "img/autre.svg"
    }
    labels = {
        "RER": "RER", "TRAIN": "TRAIN", "METRO": "MÉTRO", 
        "TRAM": "TRAMWAY", "CABLE": "CÂBLE", "BUS": "BUS", "AUTRE": "AUTRE"
    }
    fallbacks = {
        "RER": "🚆", "TRAIN": "🚆", "METRO": "🚇", 
        "TRAM": "🚋", "CABLE": "🚠", "BUS": "🚌", "AUTRE": "🌙"
    }
    resultat = {}
    for mode, label in labels.items():
        filepath = mapping_files.get(mode)
        svg_html = get_svg_inline(filepath) if filepath else None
        if svg_html:
            html = f'<span style="display:inline-flex; align-items:center;">{svg_html}<span style="margin-left:8px;">{label}</span></span>'
            resultat[mode] = html
        else:
            emoji = fallbacks.get(mode, "❓")
            resultat[mode] = f"{emoji} {label}"
    return resultat

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
    """Garde uniquement l'essentiel et met en valeur les gares/heures."""
    # 1. Nettoyage de base
    texte = re.sub(r'<[^>]+>', '', texte.replace('\n', ' ')).strip()
    
    # 2. On supprime le bégaiement ("Trafic interrompu : le trafic est interrompu...")
    texte = re.sub(r'(?i)^(Le )?trafic est interrompu\s*(:)?\s*', '', texte)
    texte = re.sub(r'(?i)^trafic interrompu\s*(:)?\s*', '', texte)

    # 3. Le style CSS pour les petits encadrés (façon badge)
    badge_style = "background:rgba(255,255,255,0.15); padding:2px 6px; border-radius:4px; color:#fff; font-weight:bold; letter-spacing:0.5px;"
    
    # 4. On détecte les HEURES (jusqu'à 23h) et on les met en rouge/gras
    texte = re.sub(r'(?i)(jusqu\'à|vers|à|reprise prévue vers|reprise estimée vers|jusqu\'en) (\d{1,2}h\d*|\w+ de service)', 
                   r'\1 <span style="color:#ffadad; font-weight:bold;">\2</span>', texte)
                   
    # 5. On détecte les GARES (entre X et Y) et on met des badges
    texte = re.sub(r'(?i)\bentre\b\s+(.*?)\s+\bet\b\s+(.*?)(?=\s+(?:jusqu|reprise|suite|en raison|à partir|le)|[,.]|$)',
                   fr'entre <span style="{badge_style}">\1</span> et <span style="{badge_style}">\2</span>', texte)
                   
    # 6. On détecte les GARES (de X vers Y) et on met des badges
    texte = re.sub(r'(?i)\bde\b\s+(.*?)\s+(?:vers|à)\s+(.*?)(?=\s+(?:jusqu|reprise|suite|en raison|à partir|le)|[,.]|$)',
                   fr'de <span style="{badge_style}">\1</span> vers <span style="{badge_style}">\2</span>', texte)

    # On met une majuscule à la première lettre restante
    if len(texte) > 1:
        texte = texte[0].upper() + texte[1:]
        
    return texte


def afficher_bandeau_trafic(line_id):
    """Retourne le HTML du bandeau trafic avec icône fixe et texte défilant."""
    if not line_id: return ""
    
    alertes = demander_info_trafic(line_id)
    interruption = next((a for a in alertes if a['severity'] >= 40), None)
    perturbation = next((a for a in alertes if 10 <= a['severity'] < 40), None)

    if interruption:
        info = synthetiser_alerte(interruption['text'])
        # 🚨 LA NOUVELLE STRUCTURE : Icône Fixe + Zone Défilante
        return f"""
            <div style="display: flex; align-items: stretch; background: rgba(231, 76, 60, 0.1); border-radius: 4px; margin: 4px 0 8px 0; border-left: 3px solid #e74c3c; overflow: hidden;">
                <div style="padding: 4px 10px; display: flex; align-items: center; background: rgba(231, 76, 60, 0.2); z-index: 10; border-right: 1px solid rgba(231,76,60,0.3);">
                    <span class="blink" style="font-size: 1.1em; text-shadow: 0 0 5px rgba(231,76,60,0.5);">❌</span>
                </div>
                <div style="flex: 1; overflow: hidden; white-space: nowrap; position: relative; padding: 6px 0;">
                    <div style="display: inline-block; padding-left: 100%; animation: ticker 20s linear infinite; color: #ffb8b8; font-size: 0.85em;">
                        <span style="font-weight: 800; color: #e74c3c; margin-right: 4px;">TRAFIC INTERROMPU :</span> {info} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
                        <span style="font-weight: 800; color: #e74c3c; margin-right: 4px;">TRAFIC INTERROMPU :</span> {info}
                    </div>
                </div>
            </div>
        """
    elif perturbation:
        info = synthetiser_alerte(perturbation['text'])
        return f'<div class="traffic-warning" style="margin-bottom:8px; padding-left:4px; border-left: 2px solid #f39c12;">⚠️ {info}</div>'
    
    return ""
