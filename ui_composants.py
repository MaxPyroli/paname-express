import streamlit as st

def afficher_titre_app(app_name, app_version, app_subtitle, icone_html):
    """Affiche le grand titre principal de l'application."""
    st.markdown(f"""
    <style>
    .titre-geant-custom {{
        font-size: clamp(2rem, 11.5vw, 4rem) !important;
        font-weight: 900 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.1 !important;
        letter-spacing: -1.5px !important;
        display: flex !important;
        align-items: center !important;
        flex-wrap: wrap !important; 
        white-space: normal !important; 
    }}
    .badge-geant-custom {{
        font-size: clamp(0.9rem, 4vw, 1.1rem) !important;
        padding: 4px 12px !important;
        display: inline-block !important;
    }}
    .sous-titre-geant-custom {{
        color: #aaa !important;
        font-style: italic !important;
        font-size: clamp(1rem, 4vw, 1.15rem) !important;
    }}
    </style>

    <div style="margin-top: 10px; margin-bottom: 25px; text-align: left;">
        <div class="titre-geant-custom">
            {icone_html}<span>{app_name}</span>
        </div>
        <div style="margin-top: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 12px;">
            <span class='version-badge badge-geant-custom'>{app_version}</span>
            <span class="sous-titre-geant-custom">{app_subtitle}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def afficher_tuto_bienvenue():
    """Affiche les 3 cartes de tutoriel sur la page d'accueil."""
    html_content = "".join([
        '<div style="text-align: center; margin-top: 40px; margin-bottom: 40px; animation: float 3s ease-in-out infinite;">',
            '<span style="font-size: 50px;">👋</span>',
        '</div>',
        '<div style="text-align: center; margin-bottom: 30px;">',
            '<h3 style="color: var(--text-color); margin-bottom: 10px;">Bienvenue sur Grand Paname</h3>',
            '<p style="font-size: 1.1em; opacity: 0.8; color: var(--text-color);">Votre compagnon de voyage en Île-de-France.</p>',
        '</div>',
        '<div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; width: 100%;">',
            # CARTE 1
            '<div class="tuto-card">',
                '<div style="font-size: 24px; margin-bottom: 10px;">🔍</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Recherchez</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Entrez le nom de votre arrêt et sélectionnez-le dans la liste déroulante</div>',
            '</div>',
            # CARTE 2
            '<div class="tuto-card">',
                '<div style="font-size: 24px; margin-bottom: 10px;">⚡</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Temps Réel</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Vos prochains départs et votre info trafic sont actualisés en temps réel</div>',
            '</div>',
            # CARTE 3
            '<div class="tuto-card">',
                '<div style="font-size: 24px; margin-bottom: 10px;">⭐</div>',
                '<div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Favoris</div>',
                '<div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Cliquez sur l\'étoile pour sauvegarder votre arrêt et le retrouver lors de votre prochain trajet</div>',
            '</div>',
        '</div>'
    ])
    st.markdown(html_content, unsafe_allow_html=True)

def afficher_testeur_de_glassmorphism():
    """Un laboratoire intégré avec un VRAI fond pour voir le flou et le code CSS exact."""
    st.divider()
    st.subheader("🧪 Banc d'Essai : Couleurs & Glassmorphism")
    
    col_c, col_v = st.columns([0.4, 0.6])
    
    with col_c:
        st.write("**Réglages CSS :**")
        var_fond = st.selectbox(
            "Variable de fond :",
            ["--background-color", "--secondary-background-color"],
            help="Les variables que Streamlit change selon le thème."
        )
        
        alpha = st.slider("Opacité (Alpha) :", 0.0, 1.0, 0.5) 
        blur = st.slider("Flou (Blur) :", 0, 30, 15)
        
        texte_custom = st.text_input("Texte de test :", "C'est lisible ?")

    with col_v:
        # Le vrai code CSS qu'on va générer et afficher
        pourcentage = int(alpha * 100)
        code_css_valide = f"""background: color-mix(in srgb, var({var_fond}) {pourcentage}%, transparent) !important;
backdrop-filter: blur({blur}px) !important;
-webkit-backdrop-filter: blur({blur}px) !important;"""

        css_preview = f"""
        <div style="
            background: linear-gradient(45deg, #4158D0 0%, #C850C0 46%, #FFCC70 100%);
            padding: 40px;
            border-radius: 20px;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
            display: flex;
            justify-content: center;
            align-items: center;
        ">
            <div style="
                background: color-mix(in srgb, var({var_fond}) {pourcentage}%, transparent);
                backdrop-filter: blur({blur}px);
                -webkit-backdrop-filter: blur({blur}px);
                border: 1px solid color-mix(in srgb, var(--text-color) 20%, transparent);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                width: 100%;
            ">
                <h2 style="color: var(--text-color); margin-bottom: 10px; font-weight: 800;">Aperçu Réel</h2>
                <p style="color: var(--text-color); font-size: 1.2em; font-weight: bold;">
                    {texte_custom}
                </p>
                
                <div style="margin-top: 25px; text-align: left; background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 0.7em; color: #aaa; margin-bottom: 5px; text-transform: uppercase; font-weight: bold;">Code CSS à copier :</div>
                    <pre style="margin: 0; padding: 0; background: transparent; border: none; overflow-x: auto;">
<code style="color: #4ade80; font-family: monospace; font-size: 0.85em; white-space: pre-wrap;">{code_css_valide}</code>
                    </pre>
                </div>

            </div>
        </div>
        """
        st.markdown(css_preview, unsafe_allow_html=True)
    
    st.info("""
    💡 **Astuce :** Trouve le réglage parfait où le texte reste lisible en mode **Clair ET Sombre**, puis copie le code vert directement dans tes fichiers `style.py` ou `assistant_ia.py` !
    """)
