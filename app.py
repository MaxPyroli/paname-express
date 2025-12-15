import streamlit as st
from datetime import datetime, timedelta
import pytz
import base64
import os

# ==========================================
#              CONFIGURATION DÉMO
# ==========================================
st.set_page_config(
    page_title="Grand Paname (DÉMO)",
    page_icon="🧪",
    layout="centered"
)

# ==========================================
#              FONCTION POLICE
# ==========================================
def charger_police_locale(file_path, font_name):
    if not os.path.exists(file_path): return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.split('.')[-1].lower()
        format_str = "opentype" if ext == "otf" else "truetype"
        css = f"""
            <style>
            @font-face {{ font-family: '{font_name}'; src: url('data:font/{ext};base64,{b64}') format('{format_str}'); }}
            html, body {{ font-family: '{font_name}', sans-serif; }}
            h1, h2, h3, h4, h5, h6, p, a, li, button, input, label, textarea {{ font-family: '{font_name}', sans-serif !important; }}
            .stMarkdown, .stButton, .stTextInput, .stSelectbox {{ font-family: '{font_name}', sans-serif !important; }}
            .streamlit-expanderHeader {{ font-family: '{font_name}', sans-serif !important; }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except: pass

charger_police_locale("GrandParis.otf", "Grand Paris")

# ==========================================
#                  STYLE CSS
# ==========================================
st.markdown("""
<style>
    @keyframes blinker { 50% { opacity: 0; } }
    .blink { animation: blinker 1s linear infinite; font-weight: bold; }
    
    @keyframes yellow-pulse {
        0% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); }
        50% { border-color: #fff; box-shadow: 0 0 15px rgba(241, 196, 15, 0.6); }
        100% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); }
    }
    
    @keyframes float { 
        0% { transform: translateY(0px); } 
        50% { transform: translateY(-6px); } 
        100% { transform: translateY(0px); } 
    } 
    .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }

    .text-red { color: #e74c3c; font-weight: bold; }
    .text-orange { color: #f39c12; font-weight: bold; }
    .text-green { color: #2ecc71; font-weight: bold; }
    .text-blue { color: #3498db; font-weight: bold; }
    
    .line-badge {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-weight: 900; color: white; text-align: center; min-width: 35px;
        margin-right: 12px; font-size: 16px; text-shadow: 0px 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .footer-container { display: flex; align-items: center; margin-bottom: 8px; }
    .footer-icon { margin-right: 10px; font-size: 14px; color: var(--text-color); opacity: 0.7; }
    .footer-badge { font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important; }

    .time-sep { color: #888; margin: 0 8px; font-weight: lighter; }
    
    .section-header {
        margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5); 
        font-size: 20px; font-weight: bold; color: var(--text-color); letter-spacing: 1px;
    }
    
    .station-title {
        font-size: 24px; font-weight: 800; color: #fff;
        text-align: center; margin: 10px 0 20px 0; text-transform: uppercase;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .rer-direction {
        margin-top: 12px; font-size: 13px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 1px solid #444; padding-bottom: 4px; margin-bottom: 0px; 
    }
    
    /* --- MISE A JOUR : COULEUR ANTHRACITE IDFM --- */
    .bus-card, .rail-card {
        background-color: #383E42 !important; /* Anthracite plus doux */
        padding: 12px; 
        margin-bottom: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #666; 
        color: #f5f5f5 !important; /* Texte blanc cassé pour la douceur */
        box-shadow: 0 2px 6px rgba(0,0,0,0.15); /* Ombre légère pour le relief */
    }

    .bus-row, .rail-row {
        display: flex; justify-content: space-between; padding-top: 8px; padding-bottom: 2px; border-top: 1px solid rgba(255,255,255,0.1); 
    }
    
    .rer-direction + .rail-row { border-top: none; padding-top: 8px; }
    
    .bus-dest, .rail-dest { color: #eee; font-size: 15px; font-weight: 500; }
    
    .service-box { 
        text-align: left; padding: 10px 12px; color: #888; font-style: italic; font-size: 0.95em;
        background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-top: 5px; margin-bottom: 5px; border-left: 3px solid #444;
    }
    .service-end { color: #999; font-style: italic; font-size: 0.9em; }

    .last-dep-box {
        border: 2px solid #f1c40f; border-radius: 6px; padding: 8px 10px; margin-top: 8px; margin-bottom: 8px;
        background-color: rgba(241, 196, 15, 0.1); animation: yellow-pulse 2s infinite;
    }
    .last-dep-label { display: block; font-size: 0.75em; text-transform: uppercase; font-weight: bold; color: #f1c40f; margin-bottom: 4px; letter-spacing: 1px; }
    .last-dep-box .rail-row, .last-dep-box .bus-row { border-top: none !important; padding-top: 0 !important; margin-top: 0 !important; }
    
    .custom-loader {
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-left-color: #3498db; border-radius: 50%; width: 14px; height: 14px;
        animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    
    .replacement-box {
        border: 2px dashed #e74c3c;
        border-radius: 6px; 
        padding: 8px 10px; 
        margin-top: 8px; 
        margin-bottom: 8px;
        background-color: rgba(231, 76, 60, 0.1);
    }
    .replacement-label { 
        display: block; 
        font-size: 0.75em; 
        text-transform: uppercase; 
        font-weight: bold; 
        color: #e74c3c; 
        margin-bottom: 4px; 
        letter-spacing: 1px; 
    }
    .replacement-box .rail-row, .replacement-box .bus-row { 
        border-top: none !important; 
        padding-top: 0 !important; 
        margin-top: 0 !important; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
#        OUTILS & LOGIQUE (MOCK)
# ==========================================

GEOGRAPHIE_RER = {
    "A": {
        "labels": ("⇦ OUEST (Cergy / Poissy)", "⇨ EST (Marne-la-Vallée)"),
        "mots_1": ["CERGY", "POISSY", "DEFENSE"], "term_1": ["CERGY"],
        "mots_2": ["MARNE", "BOISSY", "TORCY"], "term_2": ["MARNE"]
    },
    "H": {
        "labels": ("⇧ NORD (Pontoise / Persan / Creil)", "⇩ PARIS NORD"),
        "mots_1": ["PONTOISE", "PERSAN", "BEAUMONT", "LUZARCHES", "CREIL"], "term_1": ["PONTOISE"],
        "mots_2": ["PARIS", "NORD"], "term_2": ["PARIS"]
    }
}

ICONES_TITRE = {
    "RER": "🚆 RER", "TRAIN": "🚆 TRAIN", "METRO": "🚇 MÉTRO", 
    "TRAM": "🚋 TRAMWAY", "CABLE": "🚠 CÂBLE", "BUS": "🚌 BUS", "AUTRE": "🌙 AUTRE"
}

def format_html_time(minutes):
    if minutes > 120: return (3000, "<span class='service-end'>Service terminé</span>")
    if minutes <= 0: return (0, "<span class='text-red'>À quai</span>")
    if minutes == 1: return (1, "<span class='blink text-orange'>À l'approche</span>")
    if minutes < 5: return (minutes, f"<span class='text-orange'>{minutes} min</span>")
    return (minutes, f"<span class='text-green'>{minutes} min</span>")

# ==========================================
#      GÉNÉRATEUR DE SCÉNARIOS FICTIFS
# ==========================================
def get_demo_data():
    # Scénario ULTIME : Tout en un
    data = {'lines': [], 'departures': []}
    
    # 1. CABLE C1 (Normal)
    data['lines'].append({'physical_mode': 'CABLE', 'code': 'C1', 'color': '56CCF2'})
    data['departures'].append({'mode': 'CABLE', 'code': 'C1', 'dest': 'Pointe du Lac', 'min': 0, 'color': '56CCF2'})
    data['departures'].append({'mode': 'CABLE', 'code': 'C1', 'dest': 'Villa Nova', 'min': 0, 'color': '56CCF2'})

    # 2. RER A (Smart Geo + "À l'approche")
    data['lines'].append({'physical_mode': 'RER', 'code': 'A', 'color': 'E3051C'})
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'St-Germain-en-Laye', 'min': 1, 'color': 'E3051C'})
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Cergy-le-Haut', 'min': 8, 'color': 'E3051C'})
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Marne-la-Vallée Chessy', 'min': 15, 'color': 'E3051C', 'is_last': True})

    # 3. TRAIN H (Branches)
    data['lines'].append({'physical_mode': 'TRAIN', 'code': 'H', 'color': '8D5E2A'})
    data['departures'].append({'mode': 'TRAIN', 'code': 'H', 'dest': 'Pontoise', 'min': 4, 'color': '8D5E2A'})
    data['departures'].append({'mode': 'TRAIN', 'code': 'H', 'dest': 'Paris Gare du Nord', 'min': 0, 'color': '8D5E2A'})

    # 4. METRO 1 (Dernier départ IMMINENT)
    data['lines'].append({'physical_mode': 'METRO', 'code': '1', 'color': 'FFCD00'})
    data['departures'].append({'mode': 'METRO', 'code': '1', 'dest': 'Château de Vincennes', 'min': 4, 'color': 'FFCD00', 'is_last': True})

    # 5. BUS 172 (Standard)
    data['lines'].append({'physical_mode': 'BUS', 'code': '172', 'color': 'F68F2D'})
    data['departures'].append({'mode': 'BUS', 'code': '172', 'dest': 'Bourg-la-Reine RER', 'min': 0, 'color': 'F68F2D'})
    data['departures'].append({'mode': 'BUS', 'code': '172', 'dest': 'Bourg-la-Reine RER', 'min': 9, 'color': 'F68F2D'})

    # 6. BUS N01 (Noctilien)
    data['lines'].append({'physical_mode': 'BUS', 'code': 'N01', 'color': '000000'})
    data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 15, 'color': '000000'})
    data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 75, 'color': '000000'})

    # 7. SUBSTITUTIONS
    data['lines'].append({'physical_mode': 'BUS', 'code': 'A', 'color': 'E3051C'})
    data['departures'].append({'mode': 'BUS', 'code': 'A', 'dest': 'Poissy (Bus de remplacement)', 'min': 5, 'color': 'E3051C'})
    
    data['lines'].append({'physical_mode': 'METRO', 'code': '6', 'color': '75C695'})
    data['departures'].append({'mode': 'BUS', 'code': 'M6', 'dest': 'Nation', 'min': 2, 'color': '75C695'})
    data['departures'].append({'mode': 'BUS', 'code': 'M6', 'dest': 'Charles de Gaulle - Étoile', 'min': 6, 'color': '75C695'})

    return data

# ==========================================
#              MOTEUR D'AFFICHAGE
# ==========================================
def afficher_demo():
    st.title("💎 Grand Paname - SHOWCASE")
    st.caption("Vitrine des fonctionnalités & Design")
    
    # Zone Statut Fixe
    st.markdown("""<div style='display: flex; align-items: center; color: #888; font-size: 0.8rem; font-style: italic; margin-bottom: 10px;'><span class="custom-loader"></span> Démonstration temps réel...</div>""", unsafe_allow_html=True)

    mock_data = get_demo_data()
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    
    # 1. Calcul des max
    last_departures_map = {}
    for d in mock_data['departures']:
        key = (d['mode'], d['code'], d['dest'])
        current_max = last_departures_map.get(key, -999)
        if d['min'] > current_max: last_departures_map[key] = d['min']

    # 2. Remplissage INTELLIGENT
    for d in mock_data['departures']:
        mode = d['mode']
        code = d['code']
        dest = d['dest']
        color = d['color']
        minutes = d['min']
        
        # --- LOGIQUE DE DÉTECTION SUBSTITUTION ---
        is_replacement = False
        
        if mode == "BUS":
            if code in ["A", "B", "C", "D", "E", "H", "J", "K", "L", "N", "P", "R", "U", "V"]:
                is_replacement = True
                mode = "RER" if code in ["A", "B", "C", "D", "E"] else "TRAIN"
            elif code.startswith('M') and code[1:].isdigit():
                is_replacement = True
                mode = "METRO"
                code = code[1:] 
        # -----------------------------------------

        is_last = False
        if d.get('is_last'): is_last = True
            
        _, html = format_html_time(minutes)
        displayed_lines_keys.add((mode, code))
        
        if mode in buckets:
            cle = (mode, code, color)
            if cle not in buckets[mode]: buckets[mode][cle] = []
            buckets[mode][cle].append({'dest': dest, 'html': html, 'tri': minutes, 'is_last': is_last, 'is_replacement': is_replacement})

    # Footer filling
    for l in mock_data['lines']:
        mode = l['physical_mode']
        code = l['code']
        if (mode, code) not in displayed_lines_keys:
            footer_data[mode][code] = l['color']

    # 3. Rendu
    count_visible_footer = sum(len(footer_data[m]) for m in footer_data if m != "AUTRE")
    ordre = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    
    for mode_actuel in ordre:
        lignes = buckets[mode_actuel]
        if not lignes and not footer_data[mode_actuel]: continue
        
        if lignes:
            st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)
        
        for cle in sorted(lignes.keys(), key=lambda k: k[1]):
            _, code, color = cle
            departs = lignes[cle]
            
            # --- CAS 1 & 2 : RER / TRAIN (Avec Branches) ---
            if mode_actuel in ["RER", "TRAIN"] and code in GEOGRAPHIE_RER:
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                
                geo = GEOGRAPHIE_RER[code]
                p1 = [d for d in departs if d['tri'] < 3000 and any(k in d['dest'].upper() for k in geo['mots_1'])] 
                p2 = [d for d in departs if d['tri'] < 3000 and any(k in d['dest'].upper() for k in geo['mots_2'])]
                
                def render_grp(t, l):
                    h = f"<div class='rer-direction'>{t}</div>"
                    for it in l:
                        dest_txt = f"{it['dest']}"
                        if it.get('is_replacement'):
                            h += f"""<div class='replacement-box'><span class='replacement-label'>🚍 Bus de substitution</span><div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div></div>"""
                        elif it.get('is_last'):
                             h += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div></div>"""
                        else:
                             h += f"""<div class='rail-row'><span class='rail-dest'>{dest_txt}</span><span>{it['html']}</span></div>"""
                    return h
                
                if p1: card_html += render_grp(geo['labels'][0], p1)
                if p2: card_html += render_grp(geo['labels'][1], p2)
                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # --- CAS SPÉCIAL DÉMO : CÂBLE C1 (SHOWROOM) ---
            # On force l'affichage de 2 cartes pour montrer les 2 états (Normal et Perturbé)
            elif code == "C1":
                # --- CARTE 1 : FONCTIONNEMENT NORMAL (Rotation) ---
                st.caption("Scénario 1 : Fonctionnement Normal")
                rows_normal = ""
                dests_demo = ["Pointe du Lac", "Villa Nova"]
                for dn in dests_demo:
                    freq_text = "Départ toutes les ~30s"
                    rows_normal += f"""<div class="bus-row" style="align-items:center;"><span class="bus-dest">➜ {dn}</span><span style="background-color:rgba(255,255,255,0.1);padding:4px 10px;border-radius:12px;font-size:0.85em;color:#a9cce3;white-space:nowrap;">⏱ {freq_text}</span></div>"""
                
                st.markdown(f"""
                <div class="bus-card" style="border-left-color: #{color}; position: relative;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span><span style="font-weight:bold; color:#fff; font-size: 1.1em;">Câble 1</span></div>
                <span style="font-size:1.5em;" title="Téléphérique">🚡</span>
                </div>
                {rows_normal}
                </div>
                """, unsafe_allow_html=True)

                # --- CARTE 2 : PERTURBATION (Alerte) ---
                st.caption("Scénario 2 : Perturbation Majeure")
                alert_html = f"<div style='background:rgba(231,76,60,0.15);border-left:4px solid #e74c3c;color:#ffadad;padding:10px;margin-bottom:12px;border-radius:4px;display:flex;align-items:start;gap:10px;'><span style='font-size:1.2em;'>⚠️</span><span style='font-size:0.9em;line-height:1.4;'>Arrêt temporaire : Vent violent (> 90km/h)</span></div>"
                
                st.markdown(f"""
                <div class="bus-card" style="border-left-color: #{color}; position: relative;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span><span style="font-weight:bold; color:#fff; font-size: 1.1em;">Câble 1</span></div>
                <span style="font-size:1.5em;" title="Téléphérique">🚡</span>
                </div>
                {alert_html}
                <div class="service-box">😴 Service suspendu</div>
                </div>
                """, unsafe_allow_html=True)

            # --- CAS 3 : AUTRES (Bus / Métro Standard) ---
            else:
                rows_html = ""
                # Tri
                if mode_actuel in ["METRO", "CABLE"]: departs.sort(key=lambda x: x['dest'])
                else: departs.sort(key=lambda x: x['tri'])
                
                grouped = {}
                for d in departs:
                    if d['dest'] not in grouped: grouped[d['dest']] = []
                    grouped[d['dest']].append(d)

                for dest_name, items in grouped.items():
                    html_list = []
                    contains_last = False
                    last_val_tri = 999
                    is_group_replacement = items[0].get('is_replacement') if items else False

                    for idx, d in enumerate(items):
                         if idx > 0 and d['tri'] > 62 and not str(code).startswith('N'): continue
                         txt = d['html']
                         if d.get('is_last'):
                             contains_last = True
                             last_val_tri = d['tri']
                             if d['tri'] < 60:
                                 if d['tri'] < 30: txt = f"<span style='border: 1px solid #f1c40f; border-radius: 4px; padding: 0 4px; color: #f1c40f;'>{txt} 🏁</span>"
                                 else: txt += " <span style='opacity:0.7; font-size:0.9em'>🏁</span>"
                         html_list.append(txt)
                    
                    times_str = "<span class='time-sep'>|</span>".join(html_list)
                    row_html_content = f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'

                    if is_group_replacement:
                        rows_html += f"""<div class='replacement-box'><span class='replacement-label'>🚍 Bus de substitution</span>{row_html_content}</div>"""
                    elif contains_last and len(html_list) == 1 and last_val_tri < 10:
                         rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ (Imminent)</span>{row_html_content}</div>"""
                    else:
                        rows_html += row_html_content
                
                st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>{rows_html}</div>""", unsafe_allow_html=True)

    if count_visible_footer > 0:
        st.markdown("<div style='margin-top: 10px; border-top: 1px solid #333; padding-top: 15px;'></div>", unsafe_allow_html=True)
        st.caption("Autres lignes (Démo) :")
        for mode in ordre:
            if mode in footer_data and footer_data[mode]:
                badges = "".join([f'<span class="line-badge footer-badge" style="background-color:#{c};">{cd}</span>' for cd, c in footer_data[mode].items()])
                st.markdown(f"""<div class="footer-container"><span class="footer-icon">{ICONES_TITRE[mode]}</span><div>{badges}</div></div>""", unsafe_allow_html=True)
# ==========================================
#              FAUX PANNEAU LATÉRAL
# ==========================================
with st.sidebar:
    st.caption("v0.13.0 - Anthracite • 🧪 SHOWROOM") 
    st.header("🗄️ Informations")
    st.info("Ce mode **SHOWROOM** permet de visualiser tous les styles graphiques et scénarios possibles (perturbations, derniers départs, travaux, téléphérique...) sans dépendre de l'API réelle.")
    st.markdown("---")
    with st.expander("🎨 Nouveautés Design"):
        st.markdown("""
        **Update Anthracite**
        * Cartes plus douces (`#383E42`)
        * Ombres portées pour le relief
        * Textes blanc cassé (`#F5F5F5`)
        
        **Câble C1**
        * Affichage "Rotation continue"
        * Gestion des alertes météo
        """)
    st.markdown("---")
    st.caption("✨ Réalisé à l'aide de l'IA **Gemini**")

afficher_demo()
