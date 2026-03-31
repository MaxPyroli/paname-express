import streamlit as st
import json
import time
from streamlit_js_eval import streamlit_js_eval
from config import APP_VERSION, APP_CODENAME
from utils import get_all_changelogs

def initialiser_favoris():
    """Charge les favoris depuis le navigateur au démarrage."""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'favs_loaded' not in st.session_state:
        st.session_state.favs_loaded = False

    if not st.session_state.favs_loaded:
        favs_from_browser = streamlit_js_eval(js_expressions="localStorage.getItem('gp_favs')", key="get_favs_init")
        if favs_from_browser:
            try:
                st.session_state.favorites = json.loads(favs_from_browser)
                st.session_state.favs_loaded = True
                st.rerun()
            except:
                pass

def afficher_sidebar():
    """Gère l'affichage complet de la barre latérale."""
    with st.sidebar:
        st.caption(f"{APP_VERSION} - {APP_CODENAME}")
        
        # 🏠 Bouton Accueil
        if st.button("🏠 Retour à l'accueil", use_container_width=True):
            st.session_state.selected_stop = None
            st.session_state.selected_name = None
            st.session_state.search_results = {}
            st.query_params.clear()
            st.rerun()
            
        st.header("⭐ Mes Favoris")
        
        if not st.session_state.favorites:
            st.info("Ajoutez des gares en cliquant sur l'étoile à côté de leur nom !")
        else:
            for fav in st.session_state.favorites[:]:
                col_nav, col_del = st.columns([0.8, 0.2], gap="small", vertical_alignment="center")
                
                with col_nav:
                    if st.button(f"📍 {fav['name']}", key=f"btn_fav_{fav['id']}", use_container_width=True):
                        st.session_state.selected_stop = fav['id']
                        st.session_state.selected_name = fav['full_name']
                        st.session_state.search_results = {}
                        st.session_state.last_query = ""
                        st.session_state.search_key += 1
                        st.query_params["gare"] = fav['id']
                        st.session_state.fermer_sidebar = True 
                        st.rerun()

                with col_del:
                    if st.button("🗑️", key=f"del_fav_{fav['id']}", use_container_width=True):
                        st.session_state.favorites = [f for f in st.session_state.favorites if f['id'] != fav['id']]
                        json_data = json.dumps(st.session_state.favorites).replace("'", "\\'")
                        streamlit_js_eval(js_expressions=f"localStorage.setItem('gp_favs', '{json_data}')")
                        st.rerun()

            st.write("")
            if st.button("💥 Tout effacer", use_container_width=True, type="primary"):
                st.session_state.favorites = []
                streamlit_js_eval(js_expressions="localStorage.removeItem('gp_favs')")
                st.rerun()

        st.markdown("---")
        st.header("🗄️ Informations")
        st.success("🎉 **Bienvenue sur Grand Paname V2.0 !**")
        
        # Appel du composant WhatsApp que nous avons créé dans ui_components
        afficher_bouton_whatsapp()
        
        st.markdown("---")
        with st.expander("📜 Historique des versions"):
            notes_history = get_all_changelogs()
            for i, note in enumerate(notes_history):
                st.markdown(note)
                if i < len(notes_history) - 1: st.divider()
        
        st.markdown("---")
        st.caption("✨ Réalisé à l'aide de l'IA **Gemini**")
