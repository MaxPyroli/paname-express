import streamlit as st
import datetime as dt
import random

# ==========================================
#          EASTER EGG 1 : POP-UP FEUR
# ==========================================
@st.dialog("🚨 ALERTE GÉNÉRALE 🚨")
def afficher_popup_feur(mot_declencheur):
    # 1. Les Ballons (S'affichent sur toute l'app)
    st.balloons()
    
    # 2. Le Titre dans la boite de dialogue
    if mot_declencheur == "quoi":
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 20px;'>FEUR ! 💇‍♂️</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 20px;'>ROUGE ! 🚤</h1>", unsafe_allow_html=True)
    
    # 3. La Vidéo (Centrée)
    st.video("autre/feur.mp4", autoplay=True)
    
    st.markdown("*Cliquez en dehors de la fenêtre pour fermer.*")


# ==========================================
#       EASTER EGG 2 : CHARRETTE EXPRESS
# ==========================================
def afficher_cheval_express():
    """Affiche le faux mode de transport 'CHEVAL' uniquement le 1er avril."""
    now = dt.datetime.now()
    if now.month == 4 and now.day == 1:
        # Génération des temps aléatoires basés sur la minute
        random.seed(now.minute)
        
        t1_1 = "À l'approche"
        t1_2 = f"{random.randint(8, 14)} min"
        t1_3 = f"{random.randint(18, 25)} min"
        
        t2_1 = f"{random.randint(4, 7)} min"
        t2_2 = f"{random.randint(15, 20)} min"
        t2_3 = f"{random.randint(28, 35)} min"
        
        t3 = random.randint(15, 45)
        
        fausses_dest = [
            "Perpette-les-Oies - Université", 
            "Pétaouchnok RER", 
            "Eglise de Trifouillis-les-Oies",
            "Trou-Perdu-sous-Bois METRO",
            "Montcuq (Centre)",
            "Mairie de Villeneuve-Bad-Loin",
            "Stade de Nulle-Part-sur-Oise",
            "Melun (🐄)",
            "Gare de Bled-Paumé-sur-Yvette",
            "Marché International de Chépaou",
            "Bout-du-Monde (Z.I.)"
        ]
        
        random.shuffle(fausses_dest)
        d1, d2, d3 = fausses_dest[0], fausses_dest[1], fausses_dest[2]
        
        # Le code HTML/CSS collé tout à gauche pour désactiver le mode "code brut" de Streamlit
        html_poisson = f"""
<style>
@media(max-width: 480px) {{
    .ch-row {{ flex-direction:column !important; align-items:flex-start !important; }}
    .ch-times {{ width:100% !important; text-align:left !important; margin-top:6px !important; }}
    .ch-dest {{ white-space:normal !important; text-overflow:clip !important; display:block !important; width:100% !important; }}
}}
</style>
<div style="margin-top: 10px; margin-bottom: 20px;">
<div style="background-color: #041b3b; height: 54px; width: 100%; border-radius: 12px; box-sizing: border-box;"></div>
<div style="margin-top: -54px; height: 54px; width: 100%; box-sizing: border-box; background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.15); display: flex; align-items: center; padding: 0 16px; gap: 12px; color: #ffffff; font-size: 1.15rem; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 15px;">🐴 CHEVAL EXPRESS</div>
<div class="rail-card" style="border-left-color: #ff5500 !important; background-color: #041b3b; padding: 12px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
<div style="display: flex; align-items: center; margin-bottom: 8px;"><span class="line-badge" style="background-color: #ff5500; font-size: 16px; padding: 4px 10px; margin-right: 10px; border-radius: 6px;">CH</span><span style="background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; padding: 2px 6px; font-size: 14px;">🚧</span></div>
<div style="color: #f39c12; font-size: 0.85em; margin-bottom: 15px; font-weight: 500; border-left: 2px solid #f39c12; padding-left: 8px; font-style: italic;">⚠️ Mouvement social : Grève surprise des juments. Des retards sont à prévoir sur l'ensemble du réseau équestre. Prévoyez des carottes.</div>
<div class="rail-row ch-row" style="border-top: 1px solid rgba(255, 255, 255, 0.1) !important; padding-top: 8px; margin-top: 8px;"><span class="ch-dest" style="color: #e0e0e0; font-weight: 500; flex: 1; margin-right: 10px;">➔ {d1}</span><span class="ch-times" style="white-space: nowrap; text-align: right;"><span style="color: #f39c12; font-weight: bold;">{t1_1}</span> <span style="color: #888; margin: 0 6px; font-weight: lighter;">|</span> <span style="color: #2ecc71; font-weight: bold;">{t1_2}</span> <span style="color: #888; margin: 0 6px; font-weight: lighter;">|</span> <span style="color: #2ecc71; font-weight: bold;">{t1_3}</span></span></div>
<div class="rail-row ch-row" style="border-top: 1px solid rgba(255, 255, 255, 0.1) !important; padding-top: 8px; margin-top: 8px;"><span class="ch-dest" style="color: #e0e0e0; font-weight: 500; flex: 1; margin-right: 10px;">➔ {d2}</span><span class="ch-times" style="white-space: nowrap; text-align: right;"><span style="color: #2ecc71; font-weight: bold;">{t2_1}</span> <span style="color: #888; margin: 0 6px; font-weight: lighter;">|</span> <span style="color: #2ecc71; font-weight: bold;">{t2_2}</span> <span style="color: #888; margin: 0 6px; font-weight: lighter;">|</span> <span style="color: #2ecc71; font-weight: bold;">{t2_3}</span></span></div>
<div class="rail-row ch-row" style="border-top: 1px solid rgba(255, 255, 255, 0.1) !important; padding-top: 8px; margin-top: 8px;"><span class="ch-dest" style="color: #e0e0e0; font-weight: 500; flex: 1; margin-right: 10px;">➔ {d3}</span><span class="ch-times" style="white-space: nowrap; text-align: right;"><del style="color: #888;">{t3} min</del> &nbsp;<span style="color: #e74c3c; font-weight: bold; font-style: italic;">Cheval enfui</span></span></div>
</div>
</div>
"""
        st.markdown(html_poisson, unsafe_allow_html=True)
