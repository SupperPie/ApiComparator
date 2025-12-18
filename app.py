import streamlit as st
from logic import load_json_file
import ui
from project_manager import ProjectManager

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="API Comparator Pro",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- Project Management Init ---
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"
if 'debug_method' not in st.session_state:
    st.session_state.debug_method = "GET"

if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProjectManager()

# Debugger State Init
for key in ['debug_method', 'debug_path', 'debug_headers', 'debug_params', 'debug_body']:
    if key not in st.session_state:
        st.session_state[key] = "" if key == 'debug_path' else ("GET" if key == 'debug_method' else "{}")

pm = st.session_state.project_manager
projects = pm.list_projects()

# Default to first project if none selected
if 'current_project_id' not in st.session_state:
    if projects:
        st.session_state.current_project_id = projects[0]['id']
    else:
        st.session_state.current_project_id = None

# Helper to load project data
def load_project_data(project_id):
    if not project_id:
        return [], [], []
    paths = pm.get_project_paths(project_id)
    envs = load_json_file(paths['env_file'])
    apis = load_json_file(paths['api_file'])
    hist = load_json_file(paths['history_file'])
    return envs, apis, hist

# Load data if not present or if explicit reload needed
# 'data_loaded_for_project' tracks which project is currently loaded in memory
if 'data_loaded_for_project' not in st.session_state or st.session_state.data_loaded_for_project != st.session_state.current_project_id:
    envs, apis, hist = load_project_data(st.session_state.current_project_id)
    st.session_state.environments = envs
    st.session_state.api_templates = apis
    st.session_state.comparison_history = hist
    st.session_state.data_loaded_for_project = st.session_state.current_project_id
    # Reset run results when switching projects
    st.session_state.current_run_results = None

# --- Inject CSS ---
ui.inject_custom_css()

# --- Sidebar Navigation & Project Selection ---
with st.sidebar:
    st.title("🔍 API Comparator")
    
    # Project Switcher
    st.caption("Current Project")
    project_names = [p['name'] for p in projects]
    current_proj_name = next((p['name'] for p in projects if p['id'] == st.session_state.current_project_id), "")
    
    # Locate index safely
    try:
        idx = project_names.index(current_proj_name)
    except ValueError:
        idx = 0
        
    selected_project_name = st.selectbox(
        "Select Project", 
        project_names, 
        index=idx, 
        label_visibility="collapsed",
        key="project_selector"
    )
    
    # Detect change and trigger rerun (Streamlit handles key change)
    # Strategy: st.selectbox updates session_state.project_selector automatically.
    # We just need to check if it matches current ID.
    selected_project_name = st.session_state.get("project_selector")
    if selected_project_name:
        new_project_id = next((p['id'] for p in projects if p['name'] == selected_project_name), None)
        if new_project_id and new_project_id != st.session_state.current_project_id:
            st.session_state.current_project_id = new_project_id
            st.rerun()

    # Manage Projects Button
    if st.button("➕ Manage Projects"):
        st.session_state.show_project_modal = True

    st.markdown("---")

    # Custom Navigation Menu (Styled by CSS)
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

# --- Project Management Modal ---
if st.session_state.get('show_project_modal', False):
    @st.dialog("Manage Projects")
    def manage_projects_modal():
        # Create
        st.subheader("Create Project")
        new_name = st.text_input("New Project Name", key="new_proj_name")
        if st.button("Create", key="btn_create"):
            if new_name:
                pm.create_project(new_name)
                st.session_state.show_project_modal = False
                st.rerun()
        
        st.divider()
        
        # List / Manage
        st.subheader("Existing Projects")
        for p in projects:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.text(p['name'])
            
            # Rename Popover
            with c2.popover("✏️"):
                rename_val = st.text_input("New Name", value=p['name'], key=f"ren_input_{p['id']}")
                if st.button("Save", key=f"ren_save_{p['id']}"):
                    if rename_val and rename_val != p['name']:
                        pm.rename_project(p['id'], rename_val)
                        st.rerun()

            # Delete Popover
            if len(projects) > 1: 
                with c3.popover("🗑️"):
                    st.write(f"Delete?")
                    if st.button("Confirm", key=f"del_confirm_{p['id']}", type="primary"):
                        pm.delete_project(p['id'])
                        if p['id'] == st.session_state.current_project_id:
                             st.session_state.current_project_id = None
                        st.rerun()
            
    manage_projects_modal()

# --- Page Routing ---
if st.session_state.current_project_id:
    # Get current paths to pass to UI funcs for saving
    current_paths = pm.get_project_paths(st.session_state.current_project_id)
    
    if st.session_state.page == "dashboard":
        ui.render_dashboard()
    elif st.session_state.page == "configuration":
        ui.render_configuration(current_paths['api_file'], current_paths['env_file'])
    elif st.session_state.page == "comparator":
        ui.render_comparator(current_paths['history_file'])
    elif st.session_state.page == "playground":
        ui.render_debugger()
else:
    st.warning("No project selected. Please create one.")