import streamlit as st
import os
import base64

def charger_police_locale(file_path, font_name):
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.split('.')[-1].lower()
        format_str = "opentype" if ext == "otf" else "truetype"
        css = f"""
            <style>
            @font-face {{
                font-family: '{font_name}';
                src: url('data:font/{ext};base64,{b64}') format('{format_str}');
            }}
            html, body, [class*="css"] {{ font-family: '{font_name}', sans-serif; }}
            h1, h2, h3, h4, h5, h6, p, a, li, button, input, label, textarea, div, td, th {{
                font-family: '{font_name}', sans-serif !important;
            }}
            .station-title, .rail-dest, .bus-dest, .version-badge, .last-dep-label {{
                font-family: '{font_name}', sans-serif !important;
            }}
            .stMarkdown, .stButton, .stTextInput, .stSelectbox, .stExpander {{
                font-family: '{font_name}', sans-serif !important;
            }}
            button[data-testid="stSidebarCollapsedControl"] *,
            button[data-testid="stSidebarExpandedControl"] * {{
                font-family: "Material Symbols Rounded", sans-serif !important;
                font-weight: normal !important; font-style: normal !important;
                letter-spacing: normal !important; text-transform: none !important;
                white-space: nowrap !important; direction: ltr !important;
            }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except Exception:
        pass

def appliquer_style_global():
    # 1. On charge la police
    charger_police_locale("GrandParis.otf", "Grand Paris")
    
    # 2. On injecte tout le CSS (colle ici TOUT ton bloc <style> actuel)
    st.markdown("""
    <style>
        /* --- CSS NINJA : SUPPRESSIONS VISUELLES --- */
        div[data-testid="InputInstructions"] { display: none !important; }
        [data-testid="stHeaderAction"] { display: none !important; }
        div[data-testid="stFragment"] { opacity: 1 !important; transform: none !important; transition: none !important; filter: none !important; }
        div.element-container { opacity: 1 !important; filter: none !important; }
        div[data-testid="stSpinner"] { display: none !important; }
        .stApp > header { visibility: hidden !important; }
        
        /* Animation Clignotement (Blink) */
        @keyframes blink-live { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
        .live-icon { display: inline-block; animation: blink-live 1.5s infinite step-start; margin: 0 4px; vertical-align: middle; font-size: 0.6em; }
        @keyframes blinker { 50% { opacity: 0; } }
        .blink { animation: blinker 1s linear infinite; font-weight: bold; }
        @keyframes yellow-pulse { 0% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); } 50% { border-color: #fff; box-shadow: 0 0 15px rgba(241, 196, 15, 0.6); } 100% { border-color: #f1c40f; box-shadow: 0 0 5px rgba(241, 196, 15, 0.2); } }
        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } } 
        .cable-icon { display: inline-block; animation: float 3s ease-in-out infinite; }

        h1 { display: flex !important; align-items: center !important; flex-wrap: wrap !important; gap: 15px !important; margin-bottom: 0.5rem !important; font-size: 3.5rem !important; line-height: 1.1 !important; }
        .custom-loader { border: 2px solid rgba(255, 255, 255, 0.1); border-left-color: #3498db; border-radius: 50%; width: 14px; height: 14px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 8px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .text-red { color: #e74c3c; font-weight: bold; }
        .text-orange { color: #f39c12; font-weight: bold; }
        .text-green { color: #2ecc71; font-weight: bold; }
        .text-blue { color: #3498db; font-weight: bold; }
        
        .line-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 900; color: white; text-align: center; min-width: 35px; margin-right: 12px; font-size: 16px; text-shadow: 0px 1px 2px rgba(0,0,0,0.3); box-shadow: 0 2px 4px rgba(0,0,0,0.2); flex-shrink: 0; }
        .footer-container { display: flex; align-items: center; margin-bottom: 8px; }
        .footer-icon { display: inline-flex !important; align-items: center !important; flex-shrink: 0 !important; margin-right: 10px; font-size: 14px; color: var(--text-color); opacity: 0.7; white-space: nowrap !important; }
        .footer-badge { font-size: 12px !important; padding: 2px 8px !important; min-width: 30px !important; margin-right: 5px !important; }
        .time-sep { color: #888; margin: 0 8px; font-weight: lighter; }
        
        .section-header { display: flex !important; align-items: center !important; margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid rgba(128, 128, 128, 0.5); font-size: 20px; font-weight: bold; color: var(--text-color); letter-spacing: 1px; }
        .station-title { font-size: 24px; font-weight: 800; color: #fff; text-align: center; margin: 10px 0 20px 0; text-transform: uppercase; background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 12px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .rer-direction { margin-top: 12px; font-size: 13px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #444; padding-bottom: 4px; margin-bottom: 0px; }
        
        .bus-card, .rail-card { background-color: #041b3b !important; padding: 12px; margin-bottom: 15px; border-radius: 8px; border-left-width: 5px !important; border-left-style: solid !important; color: #ffffff !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .bus-dest, .rail-dest { color: #e0e0e0 !important; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 10px; flex: 1; }
        .bus-row, .rail-row { display: flex; justify-content: space-between; align-items: center; padding-top: 8px; padding-bottom: 2px; border-top: 1px solid rgba(255, 255, 255, 0.1) !important; }
        .bus-row > span:last-child, .rail-row > span:last-child { color: #ffffff !important; white-space: nowrap; flex-shrink: 0; text-align: right; }
        
        .service-box { text-align: left; padding: 10px 12px; color: #888; font-style: italic; font-size: 0.95em; background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-top: 5px; margin-bottom: 5px; border-left: 3px solid #444; }
        .service-end { color: #999; font-style: italic; font-size: 0.9em; }

        .last-dep-box { border: 2px solid #f1c40f; border-radius: 6px; padding: 8px 10px; margin-top: 8px; margin-bottom: 8px; background-color: rgba(241, 196, 15, 0.1); animation: yellow-pulse 2s infinite; }
        .last-dep-label { display: block; font-size: 0.75em; text-transform: uppercase; font-weight: bold; color: #f1c40f; margin-bottom: 4px; letter-spacing: 1px; }
        .last-dep-box .rail-row, .last-dep-box .bus-row { border-top: none !important; padding-top: 0 !important; margin-top: 0 !important; }
        .last-dep-small-frame { border: 1px solid #f1c40f; border-radius: 4px; padding: 1px 5px; color: #f1c40f; font-weight: bold; }
        .last-dep-text-only { color: #f1c40f; font-weight: bold; }

        .version-badge { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.4em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-left: 0 !important; }
        .verified-badge { color: #3498db; font-size: 0.8em; margin-left: 5px; }

        @media (max-width: 480px) {
            .block-container { padding-top: 1rem !important; }
            .station-title, .station-title-pole { font-size: 20px; }
            h1 { font-size: 35px !important; gap: 10px !important; margin-top: 0 !important; }
            .version-badge { font-size: 0.45em !important; }
            .bus-row { flex-direction: column !important; align-items: flex-start !important; padding-top: 10px !important; padding-bottom: 10px !important; }
            .bus-dest { width: 100% !important; white-space: normal !important; margin-bottom: 6px !important; font-size: 16px !important; margin-right: 0 !important; }
            .bus-row > span:last-child { width: 100% !important; text-align: left !important; font-size: 0.9em !important; color: #ccc !important; }
            .rail-row { padding-top: 8px !important; padding-bottom: 8px !important; }
            .rail-dest { max-width: 65% !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
            .time-sep { display: inline-block !important; margin: 0 5px !important; color: #666 !important; font-weight: lighter !important; }
        }
        
        div[data-testid="column"] { display: flex; align-items: center; }
        div[data-testid="column"] button { border: none; background: transparent; font-size: 1.5rem; padding: 0; }
        div[data-testid="column"] button:hover { color: #f1c40f; border: none; background: transparent; }
        
        .replacement-box { border: 2px dashed #e74c3c; border-radius: 6px; padding: 8px 10px; margin-top: 8px; margin-bottom: 8px; background-color: rgba(231, 76, 60, 0.1); }
        .replacement-label { display: block; font-size: 0.75em; text-transform: uppercase; font-weight: bold; color: #e74c3c; margin-bottom: 4px; letter-spacing: 1px; }
        .replacement-box .rail-row, .replacement-box .bus-row { border-top: none !important; padding-top: 0 !important; margin-top: 0 !important; }
        
        /* CSS ICONES INLINE */
        svg.mode-icon-inline {
            height: 1.5em !important;
            width: auto !important;
            vertical-align: middle !important;
            color: var(--text-color) !important; 
        }

        .fav-btn-container { width: 100%; }
        .fav-btn-container button { background-color: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #f1c40f !important; font-size: 16px !important; font-weight: 600 !important; height: 45px !important; border-radius: 8px !important; transition: background-color 0.2s, transform 0.1s !important; }
        .fav-btn-container button:hover { background-color: rgba(24
