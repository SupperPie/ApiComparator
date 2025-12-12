import streamlit as st
from logic import load_json_file
import ui

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="API Comparator Pro",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- File Paths ---
ENV_CONFIG_FILE = "environments.json"
API_TEMPLATE_FILE = "api_templates_UAT.json"
HISTORY_FILE = "comparison_history.json"

# --- Session State Init ---
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"
if 'current_run_results' not in st.session_state:
    st.session_state.current_run_results = None
if 'environments' not in st.session_state:
    st.session_state.environments = load_json_file(ENV_CONFIG_FILE)
if 'api_templates' not in st.session_state:
    st.session_state.api_templates = load_json_file(API_TEMPLATE_FILE)
if 'comparison_history' not in st.session_state:
    st.session_state.comparison_history = load_json_file(HISTORY_FILE)

# --- Inject CSS ---
ui.inject_custom_css()

#    # Sidebar Navigation
with st.sidebar:
    st.title("🔍 API Comparator")
    
    # Custom Navigation Menu (Styled by CSS)
    # We use radio but style it to look like a list
    selected_page = st.radio(
        "Navigate", 
        ["Dashboard", "Configuration", "Comparator", "Playground"],
        index=["dashboard", "configuration", "comparator", "playground"].index(st.session_state.page) if st.session_state.page in ["dashboard", "configuration", "comparator", "playground"] else 0,
        label_visibility="collapsed"
    )
    
    page_map = {
        "Dashboard": "dashboard",
        "Configuration": "configuration",
        "Comparator": "comparator",
        "Playground": "playground"
    }
    
    if page_map[selected_page] != st.session_state.page:
        st.session_state.page = page_map[selected_page]
        st.rerun()
        
    st.markdown("---")
    st.caption("v2.1.0 | Modular Architecture")

# --- Page Routing ---
if st.session_state.page == "dashboard":
    ui.render_dashboard()
elif st.session_state.page == "configuration":
    ui.render_configuration(API_TEMPLATE_FILE, ENV_CONFIG_FILE)
elif st.session_state.page == "comparator":
    ui.render_comparator(HISTORY_FILE)
elif st.session_state.page == "playground":
    ui.render_debugger()