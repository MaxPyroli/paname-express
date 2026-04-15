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

def afficher_bandeau_trafic(line_id, nom_ligne=""):
    """Retourne le HTML du bandeau trafic (Dynamique, limité en hauteur)."""
    if not line_id: return ""
    
    alertes = demander_info_trafic(line_id, nom_ligne)
    interruption = next((a for a in alertes if a['severity'] >= 40), None)
    perturbation = next((a for a in alertes if 10 <= a['severity'] < 40), None)

    if not interruption and not perturbation:
        return ""

    css_and_script = """
    <style>
    details.traffic-icon { display: inline-block; position: relative; margin-left: 8px; vertical-align: middle; z-index: 50; }
    
    div[data-testid="stElementContainer"]:has(details.traffic-icon[open]) {
        position: relative !important;
        z-index: 90 !important; 
    }

    details.traffic-icon > summary::-webkit-details-marker { display: none; }
    details.traffic-icon > summary { 
        list-style: none; cursor: pointer; outline: none; display: flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; transition: all 0.2s; font-size: 1.1em; user-select: none;
    }
    details.traffic-icon > summary:hover { opacity: 0.8; }
    
    /* On customise la barre de défilement pour qu'elle soit jolie ! */
    .traffic-content-scroll::-webkit-scrollbar { width: 6px; }
    .traffic-content-scroll::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
    .traffic-content-scroll::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
    .traffic-content-scroll::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }
    </style>
    
    <img src="x" style="display:none;" onerror="
        if (!window.traficJSV4) {
            window.traficJSV4 = true;
            
            function setZ90() {
                document.querySelectorAll('div[data-testid=stElementContainer]').forEach(c => {
                    if (c.querySelector('details.traffic-icon[open]')) {
                        c.style.setProperty('position', 'relative', 'important');
                        c.style.setProperty('z-index', '90', 'important');
                    } else if (c.style.zIndex === '90') {
                        c.style.removeProperty('z-index');
                    }
                });
            }

            document.addEventListener('click', e => {
                document.querySelectorAll('details.traffic-icon[open]').forEach(d => {
                    if (!d.contains(e.target)) d.removeAttribute('open');
                });
                setTimeout(setZ90, 10);
            });

            document.addEventListener('toggle', e => {
                if (e.target && e.target.classList && e.target.classList.contains('traffic-icon')) setZ90();
            }, true);
        }
    ">
    """

    html_output = css_and_script + '<div style="display: inline-flex; gap: 6px; vertical-align: middle;">'

    # --- NETTOYAGE DU TEXTE ---
    def preparer_texte(texte_brut):
        if not texte_brut or str(texte_brut).strip().lower() == "none": 
            return "Information non disponible."
        t = str(texte_brut)
        t = re.sub(r'(?i)<br\s*/?>|</p>|</li>', '\n', t)
        t = re.sub(r'<[^>]+>', '', t)
        
        bouts_a_effacer = [
            r"(?i)bus \d+\s*:\s*travaux\s*[-:]?\s*",
            r"(?i)arrêt\(s\) non desservi\(s\)\s*[-:]?\s*",
            r"(?i)motif\s*:\s*travaux sur le réseau ferroviaire\.?",
            r"(?i)métro \d+\s*:\s*travaux de modernisation\s*[-:]?\s*(autre)?\s*(autre)?\s*",
            r"(?i)trafic perturbé\s*[-:]?\s*",
            r"(?i)trafic interrompu\s*[-:]?\s*"
        ]
        for bout in bouts_a_effacer:
            t = re.sub(bout, '', t)
            
        try:
            t_propre = nettoyer_texte_details(t)
            if t_propre: t = t_propre
        except: pass

        lignes_a_zapper = [
            "les horaires du calculateur", "un service de bus de remplacement",
            "détails et calendrier", "autre autre", "consultez le fil x",
            "consultez le compte x", "plus d'informations sur cette perturbation",
            "nous vous prions de bien vouloir", "pour la gêne occasionnée", "fi :"
        ]

        lignes = t.split('\n')
        lignes_finales = []
        for l in lignes:
            l_clean = l.strip()
            l_clean = re.sub(r'^[-:.,;]\s*', '', l_clean)
            if not l_clean or len(l_clean) < 3 or l_clean.lower() == "none": continue
            if any(z in l_clean.lower() for z in lignes_a_zapper): continue
                
            est_doublon = False
            for i, existante in enumerate(lignes_finales):
                if l_clean.lower() in existante.lower() or existante.lower() in l_clean.lower():
                    lignes_finales[i] = l_clean if len(l_clean) > len(existante) else existante
                    est_doublon = True
                    break
            
            if not est_doublon:
                l_clean = l_clean[0].upper() + l_clean[1:]
                lignes_finales.append(l_clean)
        
        if not lignes_finales:
            secours = str(texte_brut).replace('\n', ' ').strip()
            if secours.lower() == "none" or not secours: return "Information non disponible."
            return secours
        return '<br>'.join(lignes_finales)

    interruptions = [a for a in alertes if a['severity'] >= 40]
    perturbations = [a for a in alertes if 10 <= a['severity'] < 40]

    # --- AFFICHAGE DES BULLETINS ---
    # Pour les interruptions ROUGES :
    for inter in interruptions:
        info_longue = preparer_texte(inter.get('text', ''))
        html_output += f"""
        <details class="traffic-icon" name="trafic" style="position: relative; z-index: 95;">
            <summary style="background: rgba(231, 76, 60, 0.15); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid rgba(231, 76, 60, 0.5); border-radius: 8px;" title="Trafic Interrompu">❌</summary>
            <div style="margin-top: 4px; -webkit-mask-image: linear-gradient(to bottom, transparent 0px, black 8px, black calc(100% - 15px), transparent 100%); mask-image: linear-gradient(to bottom, transparent 0px, black 8px, black calc(100% - 15px), transparent 100%);">
                        background: var(--gp-card-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); 
                        border: 1px solid color-mix(in srgb, var(--gp-text) 15%, transparent); border-left: 4px solid #e74c3c; padding: 12px; border-radius: 12px; box-shadow: var(--gp-card-shadow);">
                <strong style="color: #e74c3c; font-size: 0.9em; display: flex; align-items: center; gap: 6px;">❌ TRAFIC INTERROMPU</strong>
                <div class="traffic-content-scroll" style="font-size: 0.85em; color: var(--gp-text); opacity: 0.9; line-height: 1.5; white-space: normal; max-height: 220px; overflow-y: auto; padding-right: 5px; padding-top: 8px; padding-bottom: 15px;">{info_longue}</div>
            </div>
        </details>
        """
        
    for pert in perturbations:
        texte_brut = pert.get('text', '')
        type_pert = determiner_type_perturbation(texte_brut, pert.get('header', ''))
        if type_pert == "TROP_LOIN": continue
            
        info_longue = preparer_texte(texte_brut)
        est_travaux = "travaux" in texte_brut.lower() or "travaux" in type_pert.lower()
        est_futur = "À venir" in type_pert
        
        if est_futur: icone_emoji, couleur_hex, couleur_rgb, titre = "ℹ️", "#3498db", "52, 152, 219", f"Information • {type_pert}"
        elif est_travaux: icone_emoji, couleur_hex, couleur_rgb, titre = "🚧", "#f39c12", "243, 156, 18", f"TRAVAUX • {type_pert}"
        else: icone_emoji, couleur_hex, couleur_rgb, titre = "⚠️", "#f39c12", "243, 156, 18", f"Trafic perturbé • {type_pert}"

        html_output += f"""
        <details class="traffic-icon" name="trafic" style="position: relative; z-index: 95;">
            <summary style="background: rgba({couleur_rgb}, 0.15); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid rgba({couleur_rgb}, 0.5); border-radius: 8px;" title="{titre}">{icone_emoji}</summary>
            <div style="margin-top: 4px; -webkit-mask-image: linear-gradient(to bottom, transparent 0px, black 8px, black calc(100% - 15px), transparent 100%); mask-image: linear-gradient(to bottom, transparent 0px, black 8px, black calc(100% - 15px), transparent 100%);">
                        background: var(--gp-card-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); 
                        border: 1px solid color-mix(in srgb, var(--gp-text) 15%, transparent); border-left: 4px solid {couleur_hex}; padding: 12px; border-radius: 12px; box-shadow: var(--gp-card-shadow);">
                <strong style="color: {couleur_hex}; font-size: 0.9em; display: flex; align-items: center; gap: 6px;">{icone_emoji} {titre}</strong>
                <div class="traffic-content-scroll" style="font-size: 0.85em; color: var(--gp-text); opacity: 0.9; line-height: 1.5; white-space: normal; max-height: 220px; overflow-y: auto; padding-right: 5px; padding-top: 8px; padding-bottom: 15px;">{info_longue}</div>
            </div>
        </details>
        """

    html_output += '</div>'
    return html_output.replace('\n', '')
