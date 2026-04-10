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
    """Affiche les 3 cartes de tutoriel sur la page d'accueil avec effet de survol."""
    html_content = """
    <style>
    /* La classe de base pour tes cartes */
    .tuto-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        min-width: 200px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease; /* C'est ça qui rend l'animation fluide */
    }

    /* L'effet magique au survol de la souris */
    .tuto-card:hover {
        transform: translateY(-8px); /* Soulève la carte */
        box-shadow: 0 12px 25px rgba(52, 152, 219, 0.25); /* Crée un halo bleu en dessous */
        border: 1px solid rgba(52, 152, 219, 0.5); /* Allume la bordure en bleu */
        cursor: pointer; /* Transforme le curseur en petite main */
    }
    </style>

    <div style="text-align: center; margin-top: 40px; margin-bottom: 40px; animation: float 3s ease-in-out infinite;">
        <span style="font-size: 50px;">👋</span>
    </div>
    
    <div style="text-align: center; margin-bottom: 30px;">
        <h3 style="color: var(--text-color); margin-bottom: 10px;">Bienvenue sur Grand Paname</h3>
        <p style="font-size: 1.1em; opacity: 0.8; color: var(--text-color);">Votre compagnon de voyage en Île-de-France.</p>
    </div>
    
    <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">
        <div class="tuto-card">
            <div style="font-size: 24px; margin-bottom: 10px;">🔍</div>
            <div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Recherchez</div>
            <div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Entrez le nom de votre arrêt et sélectionnez-le dans la liste déroulante</div>
        </div>
        
        <div class="tuto-card">
            <div style="font-size: 24px; margin-bottom: 10px;">⚡</div>
            <div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Temps Réel</div>
            <div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Vos prochains départs et votre info trafic sont actualisés en temps réel</div>
        </div>
        
        <div class="tuto-card">
            <div style="font-size: 24px; margin-bottom: 10px;">⭐</div>
            <div style="font-weight: bold; color: var(--text-color); margin-bottom: 5px;">Favoris</div>
            <div style="font-size: 0.9em; opacity: 0.7; color: var(--text-color);">Cliquez sur l'étoile pour sauvegarder votre arrêt et le retrouver lors de votre prochain trajet</div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
