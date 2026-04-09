import streamlit.components.v1 as components
import base64
from utils import get_img_as_base64

def rendre_installable():
    # 1. On récupère ton icône
    icon_b64 = get_img_as_base64("app_icon.png")
    icon_data_uri = f"data:image/png;base64,{icon_b64}" if icon_b64 else ""

    # 2. Le Manifest (Version simplifiée et robuste)
    manifest = f"""
    {{
        "name": "Grand Paname",
        "short_name": "Paname",
        "start_url": ".",
        "display": "standalone",
        "theme_color": "#041b3b",
        "background_color": "#041b3b",
        "icons": [
            {{
                "src": "{icon_data_uri}",
                "sizes": "192x192",
                "type": "image/png"
            }},
            {{
                "src": "{icon_data_uri}",
                "sizes": "512x512",
                "type": "image/png"
            }}
        ]
    }}
    """
    
    b64_manifest = base64.b64encode(manifest.encode('utf-8')).decode('utf-8')
    manifest_url = f"data:application/manifest+json;base64,{b64_manifest}"

    # 3. Le script de nettoyage et d'injection
    html_code = f"""
    <script>
        const parentHead = window.parent.document.head;

        // 🧹 ÉTAPE 1 : On nettoie toutes les icônes Streamlit existantes
        const streamlitIcons = parentHead.querySelectorAll('link[rel*="icon"], link[rel="manifest"], link[rel="apple-touch-icon"]');
        streamlitIcons.forEach(el => el.remove());

        // 🏗️ ÉTAPE 2 : On injecte notre Manifest
        const manifestLink = window.parent.document.createElement('link');
        manifestLink.rel = 'manifest';
        manifestLink.href = '{manifest_url}';
        parentHead.appendChild(manifestLink);

        // 🍎 ÉTAPE 3 : On injecte l'icône spécifique Apple (Indispensable pour iPhone)
        if ('{icon_data_uri}' !== '') {{
            const appleIcon = window.parent.document.createElement('link');
            appleIcon.rel = 'apple-touch-icon';
            appleIcon.href = '{icon_data_uri}';
            parentHead.appendChild(appleIcon);
            
            // On en rajoute une pour être sûr (favicon de secours)
            const favIcon = window.parent.document.createElement('link');
            favIcon.rel = 'icon';
            favIcon.href = '{icon_data_uri}';
            parentHead.appendChild(favIcon);
        }}

        // Meta tags pour le plein écran
        const metas = [
            {{name: 'apple-mobile-web-app-capable', content: 'yes'}},
            {{name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'}},
            {{name: 'apple-mobile-web-app-title', content: 'Grand Paname'}}
        ];
        
        metas.forEach(m => {{
            const meta = window.parent.document.createElement('meta');
            meta.name = m.name;
            meta.content = m.content;
            parentHead.appendChild(meta);
        }});
    </script>
    """
    
    components.html(html_code, height=0, width=0)
