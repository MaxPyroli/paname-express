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
    """Déduit le type de problème pour faire un sous-titre propre."""
    t_low = texte.lower()
    
    # On détecte si c'est une alerte de nuit pour mettre un titre rassurant
    if re.search(r"(?i)(dès|à partir de)\s*(2[0-3]|0[0-4])[:h]|en soirée|les soirs|nuits?", t_low): 
        return "Travaux ce soir"
        
    if "non desservi" in t_low or "plus desservi" in t_low: return "Arrêt non desservi"
    if "dévi" in t_low or "modifié" in t_low: return "Itinéraire dévié"
    if "ralentissement" in t_low or "retard" in t_low: return "Ralentissements"
    if "supprim" in t_low: return "Suppressions"
    
    if header and len(header) < 30: return header
    return "En cours"

def afficher_bandeau_trafic(line_id):
    """Retourne le HTML du bandeau trafic (Propre, stable, avec tous les filtres)."""
    if not line_id: return ""
    
    alertes = demander_info_trafic(line_id)
    interruption = next((a for a in alertes if a['severity'] >= 40), None)
    perturbation = next((a for a in alertes if 10 <= a['severity'] < 40), None)

    if not interruption and not perturbation:
        return ""

    css = """<style>
    details.traffic-box > summary::-webkit-details-marker { display: none; }
    details.traffic-box .chevron { display: inline-block; transition: transform 0.3s ease; }
    details.traffic-box[open] .chevron { transform: rotate(180deg); }
    </style>"""

    html_output = css

    # 🌬️ LE MOTEUR INTÉGRÉ (100% blindé)
    def preparer_texte(texte_brut):
        if not texte_brut or str(texte_brut).strip().lower() == "none": 
            return "Information non disponible."
        
        # On force en string au cas où l'API envoie un format bizarre
        t = str(texte_brut)
        
        # 1. On remplace les balises de structure par des sauts de ligne
        t = re.sub(r'(?i)<br\s*/?>|</p>|</li>', '\n', t)
        t = re.sub(r'<[^>]+>', '', t)
        
        # 2. GOMMAGE EXTRÊME : On détruit les bégaiements IDFM / RATP
        bouts_a_effacer = [
            r"(?i)bus \d+\s*:\s*travaux\s*[-:]?\s*",
            r"(?i)arrêt\(s\) non desservi\(s\)\s*[-:]?\s*",
            r"(?i)en raison de travaux\s*[-:,]?\s*",
            r"(?i)motif\s*:\s*travaux sur le réseau ferroviaire\.?",
            r"(?i)métro \d+\s*:\s*travaux de modernisation\s*[-:]?\s*(autre)?\s*(autre)?\s*",
            r"(?i)trafic perturbé\s*[-:]?\s*",
            r"(?i)trafic interrompu\s*[-:]?\s*"
        ]
        for bout in bouts_a_effacer:
            t = re.sub(bout, '', t)
            
        # 🛡️ Sécurité anti-crash sur ta fonction existante
        try:
            t_propre = nettoyer_texte_details(t)
            if t_propre: t = t_propre
        except:
            pass # Si ça plante, on garde le texte tel quel

        # 3. Phrases entières à zapper complètement
        lignes_a_zapper = [
            "les horaires du calculateur",
            "un service de bus de remplacement",
            "détails et calendrier", 
            "autre autre",
            "consultez le fil x",
            "consultez le compte x",
            "plus d'informations sur cette perturbation"
        ]

        lignes = t.split('\n')
        lignes_finales = []
        
        for l in lignes:
            l_clean = l.strip()
            # Nettoyage de la ponctuation résiduelle en début de phrase
            l_clean = re.sub(r'^[-:.,;]\s*', '', l_clean)
            
            if not l_clean or len(l_clean) < 3 or l_clean.lower() == "none":
                continue
                
            if any(z in l_clean.lower() for z in lignes_a_zapper):
                continue
                
            # 4. ANTI-DOUBLONS INTELLIGENT
            est_doublon = False
            for i, existante in enumerate(lignes_finales):
                if l_clean.lower() in existante.lower():
                    est_doublon = True
                    break
                elif existante.lower() in l_clean.lower():
                    lignes_finales[i] = l_clean
                    est_doublon = True
                    break
            
            if not est_doublon:
                l_clean = l_clean[0].upper() + l_clean[1:]
                lignes_finales.append(l_clean)
        
        # 5. SÉCURITÉ ANTI-VIDE ABSOLUE
        if not lignes_finales:
            secours = str(texte_brut).replace('\n', ' ').strip()
            if secours.lower() == "none" or not secours:
                return "Information non disponible."
            return secours
            
        return '<br>'.join(lignes_finales)

    # --- ASSEMBLAGE DES BANDEAUX ---
    if interruption:
        info_longue = preparer_texte(interruption.get('text', ''))
        
        html_output += f"""
        <details class="traffic-box" style="margin-bottom:8px; border-radius: 4px; overflow: hidden; background: rgba(231, 76, 60, 0.1); border-left: 3px solid #e74c3c;">
            <summary style="cursor: pointer; list-style: none; display: block; outline: none; margin: 0;">
                <div style="display: flex; align-items: stretch;">
                    <div style="padding: 8px 12px; display: flex; align-items: center; background: rgba(231, 76, 60, 0.2); font-size: 1.1em;">❌</div>
                    <div style="flex: 1; display: flex; align-items: center; padding: 8px 12px; color: #e74c3c; font-size: 0.85em; font-weight: 900; letter-spacing: 0.5px;">TRAFIC INTERROMPU</div>
                    <div style="padding: 0 12px; display: flex; align-items: center; color: #e74c3c; font-size: 0.8em;"><span class="chevron">▼</span></div>
                </div>
            </summary>
            <div style="color: #ddd; font-size: 0.8em; padding: 12px; border-top: 1px solid rgba(231, 76, 60, 0.2); line-height: 1.6;">
                {info_longue}
            </div>
        </details>
        """
        
    elif perturbation:
        texte_brut = perturbation.get('text', '')
        header_brut = perturbation.get('header', '')
        
        type_pert = determiner_type_perturbation(texte_brut, header_brut)
        icone = "🚧" if "Travaux" in type_pert else "⚠️"
        
        titre_affiche = f"Trafic perturbé <span style='margin: 0 8px; opacity: 0.5;'>•</span> <span style='color:#f1c40f; font-weight:normal;'>{type_pert}</span>"
        info_longue = preparer_texte(texte_brut)
        
        html_output += f"""
        <details class="traffic-box" style="margin-bottom:8px; border-radius: 4px; overflow: hidden; background: rgba(243, 156, 18, 0.1); border-left: 3px solid #f39c12;">
            <summary style="cursor: pointer; list-style: none; display: block; outline: none; margin: 0;">
                <div style="display: flex; align-items: stretch;">
                    <div style="padding: 8px 12px; display: flex; align-items: center; background: rgba(243, 156, 18, 0.2); font-size: 1.1em;">{icone}</div>
                    <div style="flex: 1; display: flex; align-items: center; padding: 8px 12px; color: #f39c12; font-size: 0.85em; font-weight: bold;">{titre_affiche}</div>
                    <div style="padding: 0 12px; display: flex; align-items: center; color: #f39c12; font-size: 0.8em;"><span class="chevron">▼</span></div>
                </div>
            </summary>
            <div style="color: #ddd; font-size: 0.8em; padding: 12px; border-top: 1px solid rgba(243, 156, 18, 0.2); line-height: 1.6;">
                {info_longue}
            </div>
        </details>
        """

    return html_output.replace('\n', '')
