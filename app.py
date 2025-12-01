import streamlit as st
from datetime import datetime, timedelta
import pytz
import base64
import os

# ==========================================
#              CONFIGURATION DÉMO
# ==========================================
st.set_page_config(
    page_title="Grand Paname (DÉMO ULTIME)",
    page_icon="🧪",
    layout="centered"
)

# ==========================================
#              STYLE CSS (v0.12.2)
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
    .footer-icon { margin-right: 10px; font-size: 14px; color: #ccc; opacity: 0.7; }
    .footer-badge { font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important; }

    .time-sep { color: #888; margin: 0 8px; font-weight: lighter; }
    
    .section-header {
        margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5); 
        font-size: 20px; font-weight: bold; color: #ccc; letter-spacing: 1px;
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
    
    # 1. CABLE C1 (Pour le bandeau)
    data['lines'].append({'physical_mode': 'CABLE', 'code': 'C1', 'color': '56CCF2'})
    data['departures'].append({'mode': 'CABLE', 'code': 'C1', 'dest': 'Service terminé', 'min': 3000, 'color': '56CCF2'})

    # 2. RER A (Smart Geo + Dernier départ RER)
    data['lines'].append({'physical_mode': 'RER', 'code': 'A', 'color': 'E3051C'})
    # Ouest (Normal)
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'St-Germain-en-Laye', 'min': 2, 'color': 'E3051C'})
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Cergy-le-Haut', 'min': 8, 'color': 'E3051C'})
    # Est (Dernier départ)
    data['departures'].append({'mode': 'RER', 'code': 'A', 'dest': 'Marne-la-Vallée Chessy', 'min': 15, 'color': 'E3051C', 'is_last': True})

    # 3. TRAIN H (Liste simple)
    data['lines'].append({'physical_mode': 'TRAIN', 'code': 'H', 'color': '8D5E2A'})
    data['departures'].append({'mode': 'TRAIN', 'code': 'H', 'dest': 'Pontoise', 'min': 4, 'color': '8D5E2A'})
    data['departures'].append({'mode': 'TRAIN', 'code': 'H', 'dest': 'Persan-Beaumont', 'min': 22, 'color': '8D5E2A'})

    # 4. METRO 1 (Cas : Dernier départ IMMINENT < 10min)
    # -> Doit afficher la grosse boîte jaune
    data['lines'].append({'physical_mode': 'METRO', 'code': '1', 'color': 'FFCD00'})
    data['departures'].append({'mode': 'METRO', 'code': '1', 'dest': 'Château de Vincennes', 'min': 4, 'color': 'FFCD00', 'is_last': True})

    # 5. METRO 4 (Cas : Dernier départ PROCHE < 30min)
    # -> Doit afficher l'encadré jaune autour de l'heure
    data['lines'].append({'physical_mode': 'METRO', 'code': '4', 'color': 'BB4D98'})
    data['departures'].append({'mode': 'METRO', 'code': '4', 'dest': 'Bagneux - Lucie Aubrac', 'min': 25, 'color': 'BB4D98', 'is_last': True})

    # 6. METRO 14 (Cas : Dernier départ LOINTAIN > 30min)
    # -> Doit afficher juste le drapeau
    data['lines'].append({'physical_mode': 'METRO', 'code': '14', 'color': '662483'})
    data['departures'].append({'mode': 'METRO', 'code': '14', 'dest': 'Saint-Denis Pleyel', 'min': 2, 'color': '662483'})
    data['departures'].append({'mode': 'METRO', 'code': '14', 'dest': 'Saint-Denis Pleyel', 'min': 45, 'color': '662483', 'is_last': True})

    # 7. BUS N01 (Noctilien + Filtre 60min)
    # -> Doit afficher le bus de 75 min car c'est un Noctilien
    data['lines'].append({'physical_mode': 'BUS', 'code': 'N01', 'color': '000000'})
    data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 15, 'color': '000000'})
    data['departures'].append({'mode': 'BUS', 'code': 'N01', 'dest': 'Gare de l\'Est', 'min': 75, 'color': '000000'})

    # 8. TRAM T3a (Service terminé)
    # -> Doit aller dans le footer
    data['lines'].append({'physical_mode': 'TRAM', 'code': 'T3a', 'color': 'FF6600'})
    
    return data

# ==========================================
#              MOTEUR D'AFFICHAGE
# ==========================================
def afficher_demo():
    st.title("💎 Grand Paname - SHOWCASE")
    st.caption("Vitrine de toutes les fonctionnalités")
    
    # Zone Statut Fixe
    st.markdown("""<div style='display: flex; align-items: center; color: #888; font-size: 0.8rem; font-style: italic; margin-bottom: 10px;'><span class="custom-loader"></span> Démonstration temps réel...</div>""", unsafe_allow_html=True)

    mock_data = get_demo_data()
    
    buckets = {"RER": {}, "TRAIN": {}, "METRO": {}, "CABLE": {}, "TRAM": {}, "BUS": {}, "AUTRE": {}}
    displayed_lines_keys = set()
    footer_data = {m: {} for m in buckets.keys()}
    
    # Remplissage buckets
    for d in mock_data['departures']:
        mode = d['mode']
        code = d['code']
        dest = d['dest']
        color = d['color']
        minutes = d['min']
        
        is_last = d.get('is_last', False)
        _, html = format_html_time(minutes)
        displayed_lines_keys.add((mode, code))
        
        if mode in buckets:
            cle = (mode, code, color)
            if cle not in buckets[mode]: buckets[mode][cle] = []
            buckets[mode][cle].append({'dest': dest, 'html': html, 'tri': minutes, 'is_last': is_last})

    # Footer filling
    for l in mock_data['lines']:
        mode = l['physical_mode']
        code = l['code']
        if (mode, code) not in displayed_lines_keys:
            footer_data[mode][code] = l['color']

    # Rendu
    ordre = ["CABLE", "RER", "TRAIN", "METRO", "BUS", "TRAM"]
    
    for mode_actuel in ordre:
        lignes = buckets[mode_actuel]
        if not lignes and not footer_data[mode_actuel]: continue
        
        # Si y'a des lignes actives, on affiche le titre
        if lignes:
            st.markdown(f"<div class='section-header'>{ICONES_TITRE[mode_actuel]}</div>", unsafe_allow_html=True)
        
        for cle in sorted(lignes.keys(), key=lambda k: k[1]):
            _, code, color = cle
            departs = lignes[cle]
            
            # --- CAS 1 : RER ---
            if mode_actuel == "RER" and code in GEOGRAPHIE_RER:
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:5px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                
                geo = GEOGRAPHIE_RER[code]
                p1 = [d for d in departs if d['tri'] < 3000 and "Cergy" in d['dest']]
                p2 = [d for d in departs if d['tri'] < 3000 and "Marne" in d['dest']]
                
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

            # --- CAS 2 : TRAINS ---
            elif mode_actuel == "TRAIN":
                card_html = f"""<div class="rail-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center; margin-bottom:10px;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>"""
                for it in departs:
                    if it.get('is_last'):
                        card_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ</span><div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div></div>"""
                    else:
                        card_html += f"""<div class='rail-row'><span class='rail-dest'>{it['dest']}</span><span>{it['html']}</span></div>"""
                card_html += "</div>"
                st.markdown(card_html, unsafe_allow_html=True)

            # --- CAS 3 : AUTRES ---
            else:
                rows_html = ""
                
                # Bandeau C1
                if code == "C1":
                    st.markdown("""<style>@keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } } .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }</style>""", unsafe_allow_html=True)
                    st.markdown(f"""<div style="background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px;"><div style="font-size: 1.1em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><span class='cable-icon'>🚠</span> Câble C1 • A l'approche...</div><div style="font-size: 2.5em; font-weight: 900; line-height: 1.1;">J-12</div><div style="font-size: 0.9em; opacity: 0.9; font-style: italic; margin-top: 5px;">Inauguration le 13 décembre 2025 à 11h</div></div>""", unsafe_allow_html=True)

                # Tri (pour la démo on simplifie, on trie par temps)
                departs.sort(key=lambda x: x['tri'])
                
                html_list = []
                contains_last = False
                last_val_tri = 999
                dest_name = departs[0]['dest'] if departs else ""

                if dest_name == 'Service terminé':
                     if code == "C1":
                         rows_html += f'<div class="bus-row"><span class="bus-dest">➜ Ouverture Public</span><span style="font-weight:bold; color:#56CCF2;">12j 4h 20min</span></div>'
                else:
                    for idx, d in enumerate(departs):
                        txt = d['html']
                        # Les règles d'affichage Last
                        if d.get('is_last'):
                            contains_last = True
                            last_val_tri = d['tri']
                            if d['tri'] < 60:
                                if d['tri'] < 30:
                                    txt = f"<span style='border: 1px solid #f1c40f; border-radius: 4px; padding: 0 4px; color: #f1c40f;'>{txt} 🏁</span>"
                                else:
                                    txt += " <span style='opacity:0.7; font-size:0.9em'>🏁</span>"
                        html_list.append(txt)
                    
                    times_str = "<span class='time-sep'>|</span>".join(html_list)

                    if contains_last and len(html_list) == 1 and last_val_tri < 10:
                         rows_html += f"""<div class='last-dep-box'><span class='last-dep-label'>🏁 Dernier départ (Imminent)</span><div class='bus-row'><span class='bus-dest'>➜ {dest_name}</span><span>{times_str}</span></div></div>"""
                    else:
                        rows_html += f'<div class="bus-row"><span class="bus-dest">➜ {dest_name}</span><span>{times_str}</span></div>'

                st.markdown(f"""<div class="bus-card" style="border-left-color: #{color};"><div style="display:flex; align-items:center;"><span class="line-badge" style="background-color:#{color};">{code}</span></div>{rows_html}</div>""", unsafe_allow_html=True)

    # Footer
    count_visible_footer = sum(len(footer_data[m]) for m in footer_data if m != "AUTRE")
    if count_visible_footer > 0:
        st.markdown("<div style='margin-top: 10px; border-top: 1px solid #333; padding-top: 15px;'></div>", unsafe_allow_html=True)
        st.caption("Autres lignes (Service terminé / Non desservi) :")
        for mode in ["RER", "TRAIN", "METRO", "CABLE", "TRAM", "BUS"]:
            if mode in footer_data and footer_data[mode]:
                badges = "".join([f'<span class="line-badge footer-badge" style="background-color:#{c};">{cd}</span>' for cd, c in footer_data[mode].items()])
                st.markdown(f"""<div class="footer-container"><span class="footer-icon">{ICONES_TITRE[mode]}</span><div>{badges}</div></div>""", unsafe_allow_html=True)

afficher_demo()
