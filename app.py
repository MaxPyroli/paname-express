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
#              STYLE CSS (Copie conforme v0.12.2)
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

    .custom-loader {
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-left-color: #3498db; border-radius: 50%; width: 14px; height: 14px;
        animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

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
    
    .bus-card, .rail-card {
        background-color: #1a1a1a; padding: 12px; margin-bottom: 15px; border-radius: 8px; border-left: 5px solid #666; color: #ddd; 
    }

    .bus-row, .rail-row {
        display: flex; justify-content: space-between; padding-top: 8px; padding-bottom: 2px; border-top: 1px solid #333; 
    }
    
    .rer-direction + .rail-row { border-top: none; padding-top: 8px; }
    
    .bus-dest, .rail-dest { color: #ccc; font-size: 15px; font-weight: 500; }
    
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
    "B": {
        "labels": ("⇩ SUD (St-Rémy)", "⇧ NORD (Roissy)"),
        "mots_1": ["REMY", "ROBINSON", "MASSY"], "term_1": ["REMY"],
        "mots_2": ["GAULLE", "MITRY", "NORD"], "term_2": ["GAULLE"]
    }
}

ICONES_TITRE = {
    "RER": "🚆 RER", "TRAIN": "🚆 TRAIN", "METRO": "🚇 MÉTRO", 
    "TRAM": "🚋 TRAMWAY", "CABLE": "🚠 CÂBLE", "BUS": "🚌 BUS", "AUTRE": "🌙 AUTRE"
}

# Générateur de temps relatif pour la démo
def make_time(minutes):
    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(paris_tz)
    future = now + timedelta(minutes=minutes)
    return future.strftime('%Y%m%dT%H%M%S')

def format_html_time(minutes):
    if minutes > 120: return (3000, "<span class='service-end'>Service terminé</span>")
    if minutes <= 0: return (0, "<span class='text-red'>À quai</span>")
    if minutes == 1: return (1, "<span class='blink text-orange'>À l'approche</span>")
    if minutes < 5: return (minutes, f"<span class='text-orange'>{minutes} min</span>")
    return (minutes, f"<span class='text-green'>{minutes} min</span>")

# ==========================================
#      GÉNÉRATEUR DE SCÉNARIOS FICTIFS
# ==========================================
def get_demo_data(scenario):
    data = {'lines': [], 'departures': []}
    
    if scenario == "rush_hour":
        # Scénario : Gare Centrale (Châtelet) en heure de pointe
        # RER A et B avec beaucoup de monde, tri géographique actif
        data['lines'] = [
            {'physical_mode': 'RER', 'code': 'A', 'color': 'E3051C'},
            {'physical_mode': 'RER', 'code': 'B', 'color': '5291CE'},
            {'physical_mode': 'METRO', 'code': '1', 'color': 'FFCD00'},
        ]
        # Départs RER A
        for m in [1, 4, 8, 15]:
            data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Marne-la-Vallée Chessy', 'min': m, 'color': 'E3051C'})
        for m in [0, 6, 12]:
            data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Saint-Germain-en-Laye', 'min': m, 'color': 'E3051C'})
        
        # Départs RER B (Dernier départ simulé)
        data['departures'].append({'mode': 'RER', 'code': 'B', 'dest': 'Aéroport Ch. de Gaulle 2', 'min': 2, 'color': '5291CE'})
        data['departures'].append({'mode': 'RER', 'code': 'B', 'dest': 'Saint-Rémy-lès-Chevreuse', 'min': 5, 'color': '5291CE'})
        
        # Métro 1
        data['departures'].append({'mode': 'METRO', 'code': '1', 'dest': 'La Défense', 'min': 1, 'color': 'FFCD00'})
        data['departures'].append({'mode': 'METRO', 'code': '1', 'dest': 'Château de Vincennes', 'min': 3, 'color': 'FFCD00'})

    elif scenario == "night_mode":
        # Scénario : Fin de service, Derniers départs et Noctiliens
        data['lines'] = [
            {'physical_mode': 'BUS', 'code': 'N01', 'color': '000000'},
            {'physical_mode': 'METRO', 'code': '4', 'color': 'BB4D98'},
        ]
        # Dernier Métro 4 (Imminent)
        data['departures'].append({'mode': 'METRO', 'code': '4', 'dest': 'Bagneux', 'min': 3, 'color': 'BB4D98', 'is_last': True})
        
        # Noctilien (Fréquence faible, on affiche le suivant même si loin)
        data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 8, 'color': '000000'})
        data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 68, 'color': '000000'}) # Test > 62 min

    elif scenario == "cable_future":
        # Scénario : Câble C1 (Futur)
        data['lines'] = [
            {'physical_mode': 'CABLE', 'code': 'C1', 'color': '56CCF2'},
            {'physical_mode': 'BUS', 'code': 'J2', 'color': 'FF0000'}
        ]
        # Le Câble n'a pas de départ (non inauguré), mais on veut voir le bandeau
        # On met juste un bus à côté pour pas que ce soit vide
        data['departures'].append({'mode': 'BUS', 'code': 'J2', 'dest': 'Limeil-Brévannes', 'min': 12, 'color': 'FF0000'})

    elif scenario == "empty":
        # Scénario : Désert total
        data['lines'] = [{'physical_mode': 'BUS', 'code': '117', 'color': '666666'}] # Ligne théorique mais pas de départ
        data['departures'] = []

    return data

# ==========================================
#              MOTEUR D'AFFICHAGE
# ==========================================
def afficher_demo(scenario_name):
    st.title("🧪 Grand Paname - DÉMO")
    st.caption(f"Scénario : {scenario_name}")
    st.markdown("---")

    # Récupération des données fictives
    mock_data = get_demo_data(scenario_name)
    
    # Reconstruction des structures de données comme dans app.py
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    
    # 1. Traitement des lignes théoriques
    all_lines_at_stop = {}
    for l in mock_data['lines']:
        mode = l['physical_mode']
        code = l['code']
        color = l['color']
        all_lines_at_stop[(mode, code)] = {'color': color}

    # 2. Traitement des départs (Simulation Temps Réel)
    last_departures_map = {}
    
    # Calcul des max (pour is_last)
    for d in mock_data['departures']:
        key = (d['mode'], d['code'], d['dest'])
        current_max = last_departures_map.get(key, -999)
        if d['min'] > current_max: last_departures_map[key] = d['min']

    for d in mock_data['departures']:
        mode = d['mode']
        code = d['code']
        dest = d['dest']
        color = d['color']
        minutes = d['min']
        
        # Calcul is_last "Maison" pour la démo
        is_last = False
        # Si forcé dans la data démo OU calculé
        if d.get('is_last') or (minutes == last_departures_map.get((mode, code, dest)) and (minutes > 60 or scenario == "night_mode")):
            is_last = True
            
        _, html = format_html_time(minutes)
        
        displayed_lines_keys.add((mode, code))
        
        if mode in buckets:
            cle = (mode, code, color)
            if cle not in buckets[mode]: buckets[mode][cle] = []
            buckets[mode][cle].append({'dest': dest, 'html': html, 'tri': minutes, 'is_last': is_last})

    # 2.1 Ghost Lines (Footer)
    for (mode_t, code_t), info_t in all_lines_at_stop.items():
        if (mode_t, code_t) not in displayed_lines_keys:
            # On met dans le footer
            footer_data[mode_t][code_t] = info_t['color']
            # Si c'est un mode noble, on force aussi l'affichage "Service terminé"
            if mode_t in ["RER", "TRAIN", "METRO", "CABLE"]:
                cle_ghost = (mode_t, code_t, info_t['color'])
                if mode_t not in buckets: buckets[mode_t] = {}
                if cle_ghost not in buckets[mode_t]:
                     buckets[mode_t][cle_ghost] = [{'dest': 'Service terminé', 'html': "<span class='service-end'>-</span>", 'tri': 3000, 'is_last': False}]

    # 3. Rendu Visuel
    count_visible_footer = sum(len(footer_data[m]) for m in footer_data if m != "AUTRE")
    has_data = len(mock_data['departures']) > 0

    # Message d'état
    if not has_data:
        if count_visible_footer > 0:
            st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(52, 152, 219, 0.1); border-radius: 10px; margin-bottom: 20px;'><h3 style='margin:0; color: #3498db;'>😴 Aucun départ immédiat</h3></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style='text-align: center; padding: 20px; background-color: rgba(231, 76, 60, 0.1); border-radius: 10px; margin-bottom: 20px;'><h3 style='margin:0; color: #e74c3c;'>📭 Aucune information</h3></div>""", unsafe_allow_html=True)

    ordre = ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS", "AUTRE"]
    
    for mode_actuel in ordre:
        lignes = buckets[mode_actuel]
        if not lignes: continue
        
        st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)
        
        for cle in sorted(lignes.keys(), key=lambda k: k[1]): # Tri par code
            _, code, color = cle
            departs = lignes[cle]
            
            # --- CAS 1 : RER (Simulation Smart Geo) ---
            if mode_actuel == "RER" and code in GEOGRAPHIE_RER:
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                
                # Simulation de groupes
                geo = GEOGRAPHIE_RER[code]
                p1 = [d for d in departs if d['tri'] < 3000 and d['dest'] in ["Saint-Germain-en-Laye", "Saint-Rémy-lès-Chevreuse"]] # Exemples
                p2 = [d for d in departs if d['tri'] < 3000 and d['dest'] in ["Marne-la-Vallée Chessy", "Aéroport Ch. de Gaulle 2"]]
                
                def render_grp(t, l):
                    h = f"<div class='rer-direction'>{t}</div>"
                    for it in l:
                        if it.get('is_last'):
                             h += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div></div>"""
                        else:
                             h += f"""<div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div>"""
                    return h
                
                if p1: card_html += render_grp(geo['labels'][0], p1)
                if p2: card_html += render_grp(geo['labels'][1], p2)
                
                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # --- CAS 3 : BUS/METRO/CABLE ---
            else:
                rows_html = ""
                
                # Bandeau C1
                if code == "C1":
                    st.markdown("""<style>@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } } .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }</style>""", unsafe_allow_html=True)
                    st.markdown(f"""<div style="background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px;"><div style="font-size: 1.1em; font-weight: bold; text-transform: uppercase;">🚠 Câble C1 • A l'approche...</div><div style="font-size: 2.5em; font-weight: 900;">J-12</div></div>""", unsafe_allow_html=True)

                for d in departs:
                    if d['dest'] == 'Service terminé':
                         if code == "C1":
                             rows_html += f'<div class="bus-row"><span class="bus-dest">➜ Ouverture Public</span><span style="font-weight:bold; color:#56CCF2;">12j 4h 20min</span></div>'
                         else:
                             rows_html += f'<div class="service-box">😴 Service terminé</div>'
                    else:
                        txt = d['html']
                        is_noctilien = code.startswith('N')
                        
                        if d.get('is_last'):
                            if d['tri'] < 60:
                                if d['tri'] < 10: # Imminent
                                     rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ (Imminent)</span><div class='bus-row'><span class='bus-dest'>➜ {d['dest']}</span><span>{txt}</span></div></div>"""
                                     continue # On passe au suivant car déjà affiché
                                else:
                                     txt = f"<span style='border: 1px solid #f1c40f; border-radius: 4px; padding: 0 4px; color: #f1c40f;'>{txt} 🏁</span>"
                            else:
                                txt += " <span style='opacity:0.7; font-size:0.9em'>🏁</span>"

                        rows_html += f'<div class="bus-row"><span class="bus-dest">➜ {d["dest"]}</span><span>{txt}</span></div>'

                st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>{rows_html}</div>""", unsafe_allow_html=True)

    # Footer
    if count_visible_footer > 0:
        st.markdown("<div style='margin-top: 10px; border-top: 1px solid #333; padding-top: 15px;'></div>", unsafe_allow_html=True)
        st.caption("Autres lignes (Démo) :")
        for mode in ordre:
            if mode in footer_data and footer_data[mode]:
                badges = "".join([f'<span class="line-badge footer-badge" style="background-color:#{c};">{cd}</span>' for cd, c in footer_data[mode].items()])
                st.markdown(f"""<div class="footer-container"><span class="footer-icon">{ICONES_TITRE[mode]}</span><div>{badges}</div></div>""", unsafe_allow_html=True)

# ==========================================
#              MENU DE CONTRÔLE
# ==========================================
with st.sidebar:
    st.header("🎛️ Contrôle Démo")
    choix = st.radio("Scénario :", [
        ("rush_hour", "🏙️ Heure de Pointe (RER A/B)"),
        ("night_mode", "🌙 Nuit / Derniers Départs"),
        ("cable_future", "🚠 Futur (Câble C1)"),
        ("empty", "📭 Station Vide")
    ], format_func=lambda x: x[1])

afficher_demo(choix[0])
