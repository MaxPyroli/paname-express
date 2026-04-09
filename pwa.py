import streamlit.components.v1 as components
import base64
from utils import get_img_as_base64

def rendre_installable():
    # 1. On récupère ton logo existant pour le transformer en icône d'application
    icon_b64 = get_img_as_base64("app_icon.png")
    icon_data_uri = f"data:image/png;base64,{icon_b64}" if icon_b64 else ""

    # 2. Le Manifest (Le "Passeport" qui dit au téléphone que c'est une vraie app)
    # Note : On utilise un fond sombre cohérent avec ton design (#041b3b)
    manifest = f"""
    {{
        "name": "Grand Paname",
        "short_name": "Paname",
        "theme_color": "#041b3b",
        "background_color": "#041b3b",
        "display": "standalone",
        "orientation": "portrait",
        "scope": "/",
        "start_url": "/",
        "icons": [
            {{
                "src": "{icon_data_uri}",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }}
        ]
    }}
    """
    
    # On encode ce passeport pour pouvoir l'injecter sans créer de fichier physique
    b64_manifest = base64.b64encode(manifest.encode('utf-8')).decode('utf-8')
    manifest_url = f"data:application/manifest+json;base64,{b64_manifest}"

    # 3. Le script invisible qui installe tout ça dans le navigateur du joueur
    html_code = f"""
    <script>
        // On cible la vraie page (et pas la petite boîte isolée de Streamlit)
        const parentHead = window.parent.document.head;

        // On vérifie qu'on ne l'a pas déjà ajouté
        if (!parentHead.querySelector('link[rel="manifest"]')) {{
            
            // Ajout du Manifest Android / Chrome
            const manifestLink = window.parent.document.createElement('link');
            manifestLink.rel = 'manifest';
            manifestLink.href = '{manifest_url}';
            parentHead.appendChild(manifestLink);

            // --- ASTUCES SPÉCIFIQUES POUR APPLE (iPhone/iPad) ---
            // Forcer le plein écran sur iOS
            const metaApp = window.parent.document.createElement('meta');
            metaApp.name = 'apple-mobile-web-app-capable';
            metaApp.content = 'yes';
            parentHead.appendChild(metaApp);

            // Rendre la barre de batterie/heure noire et transparente
            const metaStatus = window.parent.document.createElement('meta');
            metaStatus.name = 'apple-mobile-web-app-status-bar-style';
            metaStatus.content = 'black-translucent';
            parentHead.appendChild(metaStatus);

            // Le nom sous l'icône sur l'écran d'accueil iPhone
            const metaTitle = window.parent.document.createElement('meta');
            metaTitle.name = 'apple-mobile-web-app-title';
            metaTitle.content = 'Paname';
            parentHead.appendChild(metaTitle);
            
            // L'icône pour iOS
            if ('{icon_data_uri}' !== '') {{
                const appleIcon = window.parent.document.createElement('link');
                appleIcon.rel = 'apple-touch-icon';
                appleIcon.href = '{icon_data_uri}';
                parentHead.appendChild(appleIcon);
            }}
        }}
    </script>
    """
    
    # On exécute ça de manière totalement invisible
    components.html(html_code, height=0, width=0)
