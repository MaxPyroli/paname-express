import streamlit as st
import base64
import json
from utils import get_img_as_base64

def rendre_installable():
    # 1. On récupère ton icône
    icon_b64 = get_img_as_base64("app_icon.png")
    if not icon_b64:
        return
        
    icon_data_uri = f"data:image/png;base64,{icon_b64}"

    # 2. Le Manifest compressé
    manifest = {
        "name": "Grand Paname",
        "short_name": "GP",
        "start_url": ".",
        "display": "standalone",
        "theme_color": "#041b3b",
        "background_color": "#041b3b",
        "icons": [
            {"src": icon_data_uri, "sizes": "192x192", "type": "image/png"},
            {"src": icon_data_uri, "sizes": "512x512", "type": "image/png"}
        ]
    }
    
    b64_manifest = base64.b64encode(json.dumps(manifest).encode('utf-8')).decode('utf-8')
    manifest_url = f"data:application/manifest+json;base64,{b64_manifest}"

    # 3. Le script JS (sans aucun guillemet double pour ne pas casser le HTML)
    js_code = f"""
    const h=document.head; 
    h.querySelectorAll('link[rel*=icon], link[rel=manifest], link[rel=apple-touch-icon]').forEach(e=>e.remove()); 
    const m=document.createElement('link'); m.rel='manifest'; m.href='{manifest_url}'; h.appendChild(m); 
    const a=document.createElement('link'); a.rel='apple-touch-icon'; a.href='{icon_data_uri}'; h.appendChild(a);
    """

    # 4. L'injection ultra-rapide via la balise image invisible !
    st.markdown(f'<img src="x" style="display:none;" onerror="{js_code}">', unsafe_allow_html=True)
