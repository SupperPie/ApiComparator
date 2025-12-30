import streamlit as st
import pandas as pd
import json
import uuid
import difflib
import html
import time
from logic import save_json_file, execute_comparison_run, fetch_api_data, parse_openapi_spec, parse_apifox_project

# --- CSS & Styling ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Font & Colors */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --primary-color: #6366f1; /* Indigo */
            --primary-light: #e0e7ff;
            --secondary-color: #ec4899; /* Pink */
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }

        .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.025em;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid var(--border-color);
            box-shadow: 1px 0 4px rgba(0,0,0,0.02);
        }
        
        /* Buttons - Modern & Premium */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
        }
        
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        /* Primary Action Buttons */
        div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white !important;
            border: none;
            font-weight: 600;
        }
        
        /* Cards */
        .stContainer, div[data-testid="stExpander"] {
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }
        
        /* Metrics */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Data Editor */
        div[data-testid="stDataEditor"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        /* Diff View Styling */
        .diff-container { 
            display: flex; 
            gap: 12px; 
            width: 100%; 
            /* Shared Scrollbar Logic: Parent scrolls vertically */
            max-height: 700px;
            overflow-y: auto;
            overflow-x: auto;
            padding-bottom: 8px; 
            position: relative;
        }
        .diff-column {
            flex: 1;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: white;
            min-width: 350px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            /* Allow full height for shared scrolling */
            height: fit-content;
        }
        .diff-header {
            padding: 12px;
            background: #f1f5f9;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            color: var(--text-main);
            /* Sticky Header */
            position: sticky; 
            top: 0;
            z-index: 100;
            text-align: center;
        }
        .diff-content {
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            /* Remove individual scroll */
            overflow: visible;
            color: #334155;
        }
        .diff-line { display: block; padding: 0 4px; min-height: 1.5em; }
        .diff-add { background-color: #dcfce7; color: #15803d; } /* Green for Add (though typically add/del depends on perspective) */
        .diff-del { background-color: #fee2e2; color: #b91c1c; } /* Red for Del */
        .diff-change { background-color: #fee2e2; color: #b91c1c; } /* Red for Change (Requested: different = red) */
        .diff-same { background-color: #dcfce7; color: #15803d; } /* Green for Same (Requested: same = green) */
        .diff-details { background-color: #f8fafc; border: 1px dashed #cbd5e1; margin: 4px 0; border-radius: 4px; }
        .diff-summary { cursor: pointer; color: #64748b; font-size: 11px; padding: 4px; font-style: italic; }

        /* Sidebar Navigation Styling */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid var(--border-color);
        }

        /* Sidebar Header */
        section[data-testid="stSidebar"] h1 {
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.8rem;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        /* Sidebar Styling Refined */
        /* Target the generic class for robustness */
        div.stRadio [role="radiogroup"] {
            gap: 8px;
        }

        /* The Label (The clickable tap area) */
        div.stRadio [role="radiogroup"] label {
             background-color: transparent !important;
             border: 1px solid transparent;
             padding: 12px 16px !important;
             border-radius: 8px !important;
             margin-bottom: 4px !important;
             width: 100%;
             transition: all 0.2s ease;
             cursor: pointer;
             display: flex !important; 
             align-items: center;
        }
        
        div.stRadio [role="radiogroup"] label:hover {
             background-color: #f1f5f9 !important;
        }

        /* Selected State */
        div.stRadio [role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            color: white !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: none;
        }
        
        div.stRadio [role="radiogroup"] label:has(input:checked) * {
            color: white !important;
        }

        /* Hide the Radio Circle and Input */
        div.stRadio [role="radiogroup"] input {
             position: absolute;
             opacity: 0;
             width: 0;
             height: 0;
        }
        
        /* The circle is usually the first <div> child of the label, or inside it */
        div.stRadio [role="radiogroup"] label > div:first-child {
            display: none !important;
        }
        
        /* Ensure the text has no weird margins */
        div.stRadio [role="radiogroup"] label > div[data-testid="stMarkdownContainer"] {
            margin: 0 !important;
        }

    </style>
    """, unsafe_allow_html=True)

# --- Visual Diff Helper ---
def generate_side_by_side_html(data_list):
    """
    Generates HTML for side-by-side comparison with Unified Folding.
    data_list: List of dicts [{'name': 'Env Name', 'content': json_obj}]
    """
    json_strs = []
    for item in data_list:
        s = json.dumps(item['content'], indent=2, ensure_ascii=False, sort_keys=True)
        json_strs.append(s.splitlines())
        
    cols_html = ""
    ref_lines = json_strs[0]
    
    # 1. Calculate Global Safe-to-Fold Mask on Reference
    # A line in Ref is safe to fold if it is identical in ALL targets.
    # We use difflib to find 'equal' blocks for each target.
    # Initialize mask as True (Safe)
    safe_mask = [True] * len(ref_lines)
    
    for i in range(1, len(json_strs)):
        target_lines = json_strs[i]
        matcher = difflib.SequenceMatcher(None, ref_lines, target_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                # Mark these Ref lines as Unsafe (changed in this target)
                for k in range(i1, i2):
                    safe_mask[k] = False
                    
    # Helper to render a block of lines
    def render_block(lines, is_safe):
        html_out = ""
        # User Request: Same content -> Green Highlight
        base_class = "diff-line diff-same" if is_safe else "diff-line"
        
        if is_safe and len(lines) > 6:
            head = lines[:2]
            middle = lines[2:-2]
            tail = lines[-2:]
            
            for line in head:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
            
            # For the folded part, we still wrap lines but maybe the summary itself is neutral
            middle_html = ''.join([f'<div class="{base_class}">{html.escape(line)}</div>' for line in middle])
            html_out += f'<div class="diff-details"><details><summary class="diff-summary">... {len(middle)} same lines ...</summary>{middle_html}</details></div>'
            
            for line in tail:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
        else:
            for line in lines:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
        return html_out

    # 2. Render Columns
    for i, item in enumerate(data_list):
        lines_html = ""
        current_lines = json_strs[i]
        
        if i == 0:
            # Render Reference using the Safe Mask
            # We need to group Ref lines by consecutive Safe/Unsafe status
            idx = 0
            while idx < len(ref_lines):
                start = idx
                current_status = safe_mask[idx]
                while idx < len(ref_lines) and safe_mask[idx] == current_status:
                    idx += 1
                end = idx
                
                segment = ref_lines[start:end]
                lines_html += render_block(segment, current_status)
        else:
            # Render Target using Opcodes, but respecting Safe Mask for 'equal' blocks
            matcher = difflib.SequenceMatcher(None, ref_lines, current_lines)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # This block matches Ref [i1:i2].
                    # We must check if this Ref block is GLOBALLY safe.
                    # It might be 'equal' here, but 'unsafe' in another target.
                    # If it's unsafe in another target, Ref will show it. So we must show it too to align.
                    # We need to split this block based on safe_mask[i1:i2]
                    
                    sub_idx = i1
                    target_sub_idx = j1
                    while sub_idx < i2:
                        sub_start = sub_idx
                        sub_status = safe_mask[sub_idx]
                        while sub_idx < i2 and safe_mask[sub_idx] == sub_status:
                            sub_idx += 1
                        sub_end = sub_idx
                        
                        # Calculate corresponding length in Target (it's equal, so same length)
                        length = sub_end - sub_start
                        target_sub_end = target_sub_idx + length
                        
                        segment = current_lines[target_sub_idx:target_sub_end]
                        lines_html += render_block(segment, sub_status)
                        
                        target_sub_idx = target_sub_end
                        
                elif tag == 'replace':
                    for line in current_lines[j1:j2]:
                        lines_html += f'<div class="diff-line diff-change">{html.escape(line)}</div>'
                elif tag == 'delete':
                    pass 
                elif tag == 'insert':
                    for line in current_lines[j1:j2]:
                        lines_html += f'<div class="diff-line diff-add">{html.escape(line)}</div>'
                        
        cols_html += f'<div class="diff-column"><div class="diff-header">{html.escape(item["name"])}</div><div class="diff-content">{lines_html}</div></div>'
        
    return f'<div class="diff-container">{cols_html}</div>'

# --- Page Renderers ---

def render_dashboard():
    st.title("📊 Dashboard")
    
    total_runs = len(st.session_state.comparison_history)
    last_run = st.session_state.comparison_history[0] if total_runs > 0 else None
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Runs", total_runs)
    if last_run:
        col2.metric("Last Run Status", f"{last_run['consistent_count']} / {last_run['api_count']} Same")
        col3.metric("Last Run Time", last_run['timestamp'].split(' ')[0])
        
    st.markdown("### Recent History")
    if not st.session_state.comparison_history:
        st.info("No history available. Go to 'Comparator' to run a comparison.")
        return

    # Header
    h1, h2, h3, h4, h5 = st.columns([2, 3, 2, 2, 1])
    h1.markdown("**Time**")
    h2.markdown("**Environments**")
    h3.markdown("**APIs**")
    h4.markdown("**Result**")
    h5.markdown("**Action**")
    st.markdown("---")

    for run in st.session_state.comparison_history:
        c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
        c1.write(run['timestamp'])
        c2.write(", ".join(run['envs']))
        c3.write(f"{run['api_count']} APIs")
        c4.write(f"✅ {run['consistent_count']}  ❌ {run['inconsistent_count']}")
        
        if c5.button("View", key=f"view_{run['run_id']}"):
            st.session_state.current_run_results = run
            st.session_state.page = "comparator"
            st.rerun()
        st.markdown("<hr style='margin: 5px 0; opacity: 0.5;'>", unsafe_allow_html=True)

def render_configuration(api_template_file, env_config_file):
    st.title("⚙️ Configuration")
    
    tab1, tab2 = st.tabs(["API Collections", "Environments"])
    
    with tab1:

        msg_placeholder = st.empty()
        
        col_header, col_tools = st.columns([2, 3])
        with col_header:
            st.subheader("Manage API Collections")
            st.caption(f"Total APIs: {len(st.session_state.api_templates)}")

        with col_tools:
            # Import | Clear | Delete
            b1, b2, b3 = st.columns([1, 1, 1.2])
            
            # Import
            with b1:
                 with st.popover("📥 Import", use_container_width=True):
                     # ... Import Logic Wrapper ...
                     if 'uploader_key' not in st.session_state: st.session_state.uploader_key = str(uuid.uuid4())
                     u_file = st.file_uploader("JSON", type=["json"], key=st.session_state.uploader_key)
                     if u_file:
                         try:
                            imported_data = json.load(u_file)
                            # ... Calls to parse ...
                            if isinstance(imported_data, dict) and 'apifoxProject' in imported_data:
                                new_apis = parse_apifox_project(imported_data)
                            elif isinstance(imported_data, dict) and ('openapi' in imported_data or 'swagger' in imported_data):
                                new_apis = parse_openapi_spec(imported_data)
                            else:
                                 # List logic
                                 raw_list = []
                                 if isinstance(imported_data, dict):
                                     for k in ["apis", "data", "items", "list"]:
                                         if k in imported_data and isinstance(imported_data[k], list): raw_list = imported_data[k]; break
                                     if not raw_list and 'relative_path' in imported_data: raw_list = [imported_data]
                                 elif isinstance(imported_data, list): raw_list = imported_data
                                 new_apis = raw_list if raw_list else []
                            
                            if new_apis:
                                 # Merge logic
                                 c_ids = {t['id'] for t in st.session_state.api_templates if 'id' in t}
                                 cnt = 0
                                 for item in reversed(new_apis):
                                     if 'name' in item:
                                         if 'id' not in item or item['id'] in c_ids: item['id'] = str(uuid.uuid4())
                                         for f in ['headers','params','json_body']: 
                                             if f not in item or item[f] is None: item[f] = {}
                                         st.session_state.api_templates.insert(0, item)
                                         cnt += 1
                                 save_json_file(api_template_file, st.session_state.api_templates)
                                 msg_placeholder.success(f"Imported {cnt} APIs!")
                                 st.session_state.uploader_key = str(uuid.uuid4())
                                 st.rerun()
                         except Exception as e: st.error(f"Import Error: {e}")

            # Clear
            with b2:
                 with st.popover("🗑️ Clear", use_container_width=True):
                     st.write("Delete ALL?")
                     if st.button("Confirm", type="primary", use_container_width=True):
                         st.session_state.api_templates = []
                         save_json_file(api_template_file, [])
                         st.rerun()
            
            # Delete Selected
            with b3:
                delete_selected_clicked = st.button("Delete Selected", type="primary", use_container_width=True)
            
        # Success Message Area (for Auto-Save)
        if 'autosave_success' in st.session_state and st.session_state.autosave_success:
             # Use a timestamp to control visibility (3 seconds)
             if 'save_timestamp' not in st.session_state:
                 st.session_state.save_timestamp = time.time()
             
             if time.time() - st.session_state.save_timestamp < 3:
                 msg_placeholder.success("✅ Changes Saved")
             else:
                 st.session_state.autosave_success = False
                 msg_placeholder.empty()
        
        if 'autosave_error' in st.session_state and st.session_state.autosave_error:
             msg_placeholder.error(f"❌ Save Failed: {st.session_state.autosave_error}")

        # --- Data Table (No Pagination, Native Selection) ---
        # st.write("DEBUG: Trace - data_editor block reached") # DEBUG
        
        api_df = pd.DataFrame(st.session_state.api_templates)
        # st.write(f"DEBUG: api_templates count: {len(st.session_state.api_templates)}") # DEBUG
        
        # Ensure Columns
        cols = ["name", "relative_path", "method", "headers", "params", "json_body", "id"]
        for c in cols:
            if c not in api_df.columns: api_df[c] = None

        # Helper to stringify JSON for editing
        def to_json_str(x):
            if x is None: return ""
            if isinstance(x, (dict, list)): return json.dumps(x, ensure_ascii=False)
            return str(x) if x else ""

        for json_col in ["headers", "params", "json_body", "extract"]:
            if json_col in api_df.columns:
                api_df[json_col] = api_df[json_col].apply(to_json_str)

        # Add Select Column for Deletion (since selection_mode unavailable)
        if "Select" not in api_df.columns:
            api_df.insert(0, "Select", False)
        else:
            api_df["Select"] = api_df["Select"].fillna(False).astype(bool)

        # Main Editor
        # We use a unique key based on length to force refresh on add/delete
        editor_key = f"main_api_editor_{len(api_df)}" 
        
        # Editor Key Logic (force refresh on struct change)
        editor_key = f"main_api_editor_{len(api_df)}"

        # Show Editor
        # Data Editor (Force Reload)
        edited_api_df = st.data_editor(
            api_df,

            column_config={
                "Select": st.column_config.CheckboxColumn(required=True),
                "id": st.column_config.TextColumn(disabled=True, width="small"),
                "order": st.column_config.NumberColumn(
                    "Order", 
                    help="Execution Sequence (1, 2, 3...). APIs are run in this order. Important for variable extraction & chaining.", 
                    default=0, 
                    width="small"
                ),
                "name": st.column_config.TextColumn("Name", width="medium"),
                "relative_path": st.column_config.TextColumn("Path", width="medium"),
                "method": st.column_config.SelectboxColumn("Method", options=["GET", "POST", "PUT", "DELETE", "PATCH"], width="small", required=True),
                "headers": st.column_config.TextColumn("Headers (JSON)", width="medium"),
                "json_body": st.column_config.TextColumn("Body (JSON)", width="medium"),
                "extract": st.column_config.TextColumn(
                    "Post Action", 
                    width="medium", 
                    help='Define variables to extract from response.\n\nFormat: JSON List of Key-Value pairs.\n\nExample:\n[{"token": "$.result.token"}, {"user_id": "$.result.id"}]'
                ),
            },
            column_order=["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic"
        )
        
        # LOGIC: SAVE
        # LOGIC: AUTO-SAVE
        # Detect changes (ignoring Select column which is for deletion state)
        # We need to ensure we compare comparable types. 
        # api_df comes from st.session_state (list of dicts -> df).
        # edited_api_df comes from editor.
        
        # Helper to process DF for comparison
        # Helper to process DF for comparison
        def clean_for_diff(df):
            d = df.drop(columns=["Select"], errors="ignore").copy()
            # Normalize to string recursively
            for col in d.columns:
                 # Ensure None becomes "" and trim whitespace
                 d[col] = d[col].astype(str).replace("None", "").replace("nan", "").str.strip()
            return d.fillna("")

        has_changes = False
        if not clean_for_diff(api_df).equals(clean_for_diff(edited_api_df)):
             has_changes = True
        
        # st.write(f"DEBUG: has_changes: {has_changes}")
        # if has_changes:
        #     st.write("DEBUG: API DF (Top 1):", clean_for_diff(api_df).head(1).to_dict())
        #     st.write("DEBUG: Edited DF (Top 1):", clean_for_diff(edited_api_df).head(1).to_dict())

        if has_changes:
            try:
                # Convert back to list of dicts
                cleaned_data = json.loads(edited_api_df.to_json(orient="records"))
                
                # Parse JSON fields
                filtered_data = []
                for row in cleaned_data:
                    # Skip if it was just a temp row that is empty (though dynamic handles this mostly)
                    if not row.get('relative_path') and not row.get('name'):
                         continue

                    # Remove 'Select' column before saving
                    if 'Select' in row: del row['Select']

                    if not row.get('id'): row['id'] = str(uuid.uuid4())
                    
                    # Ensure Order is int
                    row['order'] = int(row.get('order', 0) or 0)

                    for field in ['params', 'json_body', 'headers', 'extract']:
                        val = row.get(field)
                        if isinstance(val, str):
                            try:
                                row[field] = json.loads(val) if val.strip() else (None if field != 'extract' else [])
                                # Ensure extract is a list
                                if field == 'extract' and not isinstance(row[field], list):
                                     row[field] = []
                            except:
                                row[field] = {} if field != 'extract' else []
                        if field == 'headers' and (not isinstance(row.get('headers'), dict)): row['headers'] = {}
                        if field == 'extract' and (not isinstance(row.get('extract'), list)): row['extract'] = []

                    filtered_data.append(row)

                # Sort by order then name
                filtered_data.sort(key=lambda x: (x.get('order', 0), x.get('name', '')))

                st.session_state.api_templates = filtered_data
                save_json_file(api_template_file, st.session_state.api_templates)
                st.session_state.autosave_success = True
                st.session_state.save_timestamp = time.time() # Reset timer
                st.session_state.autosave_error = None
                st.rerun()
            except Exception as e:
                st.session_state.autosave_error = str(e)
                st.error(f"Save failed: {e}")

        # LOGIC: DELETE WITH CHECKBOX
        if delete_selected_clicked:
            # We need to access the editor state. 
            # Since auto-save updates st.session_state.api_templates, we rely on api_df (input) having valid Selects?
            # NO. api_df is recreated on every run from st.session_state.api_templates.
            # Edited info is in edited_api_df.
            # We filter edited_api_df.
            
            # Note: edited_api_df comes from st.data_editor which ran AFTER the button click in previous execution order,
            # BUT in Streamlit flow: Button Click -> Rerun -> Button is True -> Data Editor runs.
            # So we have access to edited_api_df from THIS run.
            # Wait, button is at top. script runs Top -> Bottom.
            # line `delete_selected_clicked = ...` runs. True.
            # line `edited_api_df = st.data_editor...` runs.
            # Then we check `if delete_selected_clicked:`.
            # So `edited_api_df` IS available.
            
            to_delete = edited_api_df[edited_api_df["Select"] == True]
            if to_delete.empty:
                msg_placeholder.warning("Please select rows to delete.")
            else:
                ids_to_delete = set(to_delete["id"].dropna().tolist())
                if ids_to_delete:
                    new_list = [t for t in st.session_state.api_templates if t.get('id') not in ids_to_delete]
                    st.session_state.api_templates = new_list
                    save_json_file(api_template_file, st.session_state.api_templates)
                    msg_placeholder.success(f"Deleted {len(ids_to_delete)} items.")
                    st.rerun()
            

                    
    with tab2:
        #st.subheader("Manage Environments")
        
        # 1. Master List (Environments)
        # Load and ensure structure
        env_list = st.session_state.environments
        for e in env_list:
            if "variables" not in e: e["variables"] = []
            if isinstance(e["variables"], str):
                 try: e["variables"] = json.loads(e["variables"]) 
                 except: e["variables"] = []
            if isinstance(e["variables"], dict):
                 # Convert old dict format to list
                 e["variables"] = [{"key": k, "value": v, "description": ""} for k,v in e["variables"].items()]
            
            # Ensure other fields
            if "auth_token" not in e: e["auth_token"] = ""
            if "headers" not in e: e["headers"] = {}

            # --- Migration: Move Auth/Headers to Variables ---
            # We check if they exist independently and are NOT in variables yet.
            existing_keys = set()
            for v in e["variables"]:
                if isinstance(v, dict) and 'key' in v:
                    existing_keys.add(v['key'])
            
            # Migrate Auth Token
            if e.get("auth_token") and "auth_token" not in existing_keys:
                e["variables"].append({
                    "key": "auth_token", 
                    "value": e["auth_token"], 
                    "description": "Migrated from Auth Token field"
                })
                e["auth_token"] = "" # Clear to avoid confusion
                
            # Migrate Headers
            if e.get("headers") and isinstance(e["headers"], dict) and e["headers"]:
                if "headers" not in existing_keys:
                    try:
                        h_val = json.dumps(e["headers"])
                        e["variables"].append({
                            "key": "headers", 
                            "value": h_val, 
                            "description": "Migrated from Headers field"
                        })
                    except: pass
                e["headers"] = {} # Clear

        env_df = pd.DataFrame(env_list)
        if env_df.empty:
             env_df = pd.DataFrame(columns=["name", "base_url", "auth_token", "variables", "headers"])
        
        # We use st.radio for single selection as requested, replacing the complex data_editor
        col_list, col_detail = st.columns([2, 3])
        
        with col_list:
            st.markdown("#### Environment List")
            
            # Prepare options for radio button
            # Map ID to Display Name
            if not env_list:
                st.info("No environments. Create one below.")
                selected_env_id = None
            else:
                # Use a dict for mapping if needed, or just list of IDs and format_func
                # We need a stable identifier.
                env_map = {e['id']: e for e in env_list}
                
                # Verify current selection is valid
                if 'selected_env_id' not in st.session_state:
                    st.session_state.selected_env_id = env_list[0]['id']
                elif st.session_state.selected_env_id not in env_map:
                    if env_list: st.session_state.selected_env_id = env_list[0]['id']
                    else: st.session_state.selected_env_id = None

                selected_env_id = st.radio(
                    "Select Environment",
                    options=[e['id'] for e in env_list],
                    format_func=lambda x: env_map[x].get('name') or "Unnamed",
                    key="selected_env_id",
                    label_visibility="collapsed",
                    # Add on_change to force update of other elements if needed, 
                    # though key binding usually suffices for immediate state update.
                )
                
                if selected_env_id != st.session_state.get('selected_env_id_prev'):
                    st.session_state.selected_env_id_prev = selected_env_id
                    # Force rerun to ensure Detail View updates immediately? 
                    # Usually streamlit handles this, but let's be safe if user reports lag.
                    # st.rerun() 
                    pass
            
            # Callbacks for Add/Delete to handle State safely
            def add_env():
                new_id = str(uuid.uuid4())
                new_env = {
                    "id": new_id,
                    "name": "New Environment",
                    "base_url": "",
                    "auth_token": "",
                    "variables": [],
                    "headers": {}
                }
                st.session_state.environments.append(new_env)
                st.session_state.selected_env_id = new_id # Select new
                save_json_file(env_config_file, st.session_state.environments)

            def delete_env():
                current = st.session_state.selected_env_id
                if current:
                     st.session_state.environments = [e for e in st.session_state.environments if e['id'] != current]
                     # If we deleted the selected one, reset selection to first or None
                     if st.session_state.environments:
                         st.session_state.selected_env_id = st.session_state.environments[0]['id']
                     else:
                         st.session_state.selected_env_id = None
                     
                     save_json_file(env_config_file, st.session_state.environments)

            # Add / Delete Actions
            c_add, c_del = st.columns(2)
            c_add.button("➕ New", use_container_width=True, on_click=add_env)
            with c_del.popover("🗑️ Delete", use_container_width=True):
                st.markdown("Are you sure you want to delete this environment?")
                st.button("Confirm Delete", type="primary", on_click=delete_env)

        # 2. Detail View (Select to Edit)
        with col_detail:
            st.markdown("#### Configure Details")
            
            target_env = next((e for e in st.session_state.environments if e['id'] == selected_env_id), None)
            
            if not target_env:
                st.info("Select or create an environment to configure.")
            else:
                # Basic Details Editor
                with st.container():
                     # Edit Name and Base URL here since we removed them from the validation list editor
                     c_name, c_url = st.columns([1, 2])
                     new_name = c_name.text_input("Name", value=target_env.get('name', ''))
                     new_url = c_url.text_input("Base URL", value=target_env.get('base_url', ''))
                     
                     # Auto-save basic details on change (simpler than explicit save button for these fields)
                     if new_name != target_env.get('name') or new_url != target_env.get('base_url'):
                         target_env['name'] = new_name
                         target_env['base_url'] = new_url
                         save_json_file(env_config_file, st.session_state.environments)
                         # Rerun to update the radio button list label immediately
                         st.rerun()

                st.caption(f"Variables for: **{target_env.get('name')}**")
                    
                st.info("💡 Tip: Add 'auth_token' or 'headers' (JSON) as variables to configure authentication and default headers.")

                # Variables Editor (List)
                var_list = target_env.get('variables', [])
                # Ensure it's a list (fix potential data issues)
                if not isinstance(var_list, list): var_list = []
                
                var_df = pd.DataFrame(var_list)
                if var_df.empty:
                    var_df = pd.DataFrame(columns=["key", "value", "description"])
                
                edited_vars = st.data_editor(
                    var_df,
                    num_rows="dynamic",
                    column_config={
                        "key": st.column_config.TextColumn("Variable", required=True), # Renamed to standard "Variable"
                        "value": st.column_config.TextColumn("Value", width="medium"),
                        "description": st.column_config.TextColumn("Description", width="large"),
                    },
                    column_order=["key", "value", "description"],
                    use_container_width=True,
                    key=f"var_editor_{target_env['id']}"
                )
                    
                if st.button("💾 Save Configuration", key="save_env_vars"):
                    # Update the target_env variables
                    new_vars_list = json.loads(edited_vars.to_json(orient="records"))
                    # Filter empty keys
                    new_vars_list = [v for v in new_vars_list if v.get('key')]
                    
                    target_env['variables'] = new_vars_list
                    
                    # Save entire environments file
                    save_json_file(env_config_file, st.session_state.environments)
                    st.success(f"Saved configuration for {target_env.get('name')}")
def render_comparator(history_file, env_config_file):
    st.title("🚀 Comparator")
    
    # --- Execution Controls ---
    with st.expander("⚙️ Run Configuration", expanded=not st.session_state.current_run_results):

        st.subheader("Select Environments")
        # Horizontal Checkboxes
        cols = st.columns(4)
        selected_env_ids = []
        for i, env in enumerate(st.session_state.environments):
            col = cols[i % 4]
            if col.checkbox(env.get('name') or "Unnamed", key=f"env_select_{env['id']}"):
                selected_env_ids.append(env['id'])
        # Helper to stringify JSON
        def to_json_str(x):
            return json.dumps(x, ensure_ascii=False) if x else ""
            
        st.subheader("Select APIs")
        
        # Header Layout: Info | Progress | Button
        c_info, c_prog, c_btn = st.columns([2, 4, 1.5])
        
        with c_info:
            st.caption(f"Total APIs: {len(st.session_state.api_templates)}")
        
        with c_prog:
            prog_place = st.empty()
            status_place = st.empty()
            
        with c_btn:
            start_clicked = st.button("▶ Compare", type="primary", use_container_width=True)

        if not st.session_state.api_templates:
            api_display_df = pd.DataFrame(columns=["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract", "id"])
        else:
            api_display_df = pd.DataFrame([
                {
                    "Select": False,
                    "order": t.get('order', 0),
                    "name": t['name'], 
                    "relative_path": t['relative_path'], 
                    "method": t.get('method', 'GET'),
                    "headers": to_json_str(t.get('headers')),
                    "json_body": to_json_str(t.get('json_body')),
                    "extract": to_json_str(t.get('extract')),
                    "id": t['id']
                }
                for t in st.session_state.api_templates
            ])
        
        # Placeholder for validation/error messages at the top of the list
        comp_msg_placeholder = st.empty()

        edited_selection = st.data_editor(
            api_display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=True, width="small"),
                "id": st.column_config.TextColumn(disabled=True, width="small"),
                "order": st.column_config.NumberColumn("Order", width="small", disabled=True),
                "name": st.column_config.TextColumn("Name", width="medium", disabled=True),
                "relative_path": st.column_config.TextColumn("Path", width="medium", disabled=True),
                "method": st.column_config.TextColumn("Method", width="small", disabled=True),
                "headers": st.column_config.TextColumn("Headers (JSON)", width="medium", disabled=True),
                "json_body": st.column_config.TextColumn("Body (JSON)", width="medium", disabled=True),
                "extract": st.column_config.TextColumn("Post Action", width="medium", disabled=True),
            },
            column_order=["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract"], 
            hide_index=True,
            use_container_width=True,
            key="comparator_api_selector_v3" # Force reset
        )
        
        # Robust Selection: Use index to find selected rows
        # st.data_editor returns a dataframe with the same index as input
        # We find indices where 'Select' is True
        try:
            selected_indices = edited_selection.index[edited_selection["Select"]].tolist()
            # Map back to original IDs using these indices
            # Note: api_display_df uses default range index 0..N which matches session_state.api_templates
            selected_api_ids = [st.session_state.api_templates[i]['id'] for i in selected_indices if i < len(st.session_state.api_templates)]
        except Exception as e:
            st.error(f"Selection Error: {e}")
            selected_api_ids = []
        
        if start_clicked:
            if len(selected_env_ids) < 2:
                comp_msg_placeholder.error("Please select at least 2 environments.")
            elif not selected_api_ids:
                comp_msg_placeholder.error("Please select at least 1 API.")
            else:
                # Progress Callback
                def update_progress(current, total, msg):
                    prog_place.progress(current / total)
                    status_place.caption(msg)
                
                # Execute Logic
                results = execute_comparison_run(
                    selected_api_ids, 
                    selected_env_ids, 
                    st.session_state.environments, 
                    st.session_state.api_templates, 
                    progress_callback=update_progress
                )
                
                # Update State & Save
                st.session_state.current_run_results = results
                st.session_state.comparison_history.insert(0, results)
                save_json_file(history_file, st.session_state.comparison_history)
                
                # CRITICAL: Save Environments because extraction logic modifies them!
                save_json_file(env_config_file, st.session_state.environments)
                
                st.rerun()

    # --- Analysis / Results View ---
    if st.session_state.current_run_results:
        st.markdown("---")
        res = st.session_state.current_run_results
        
        # Header Info (Big & Optimized)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h2 style="margin: 0;">Comparation Details</h2>
                <p style="color: #666; margin: 0; font-size: 1.1em;">
                    📅 {res['timestamp']} &nbsp;|&nbsp; 🌍 {', '.join(res['envs'])}
                </p>
            </div>
            <div style="text-align: right;">
                <span class="status-badge status-consistent">✅ {res['consistent_count']} Same</span>
                <span class="status-badge status-inconsistent">❌ {res['inconsistent_count']} Different</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Filter UI: Changed to Selectbox as requested
        f_col1, f_col2 = st.columns([1, 4])
        with f_col1:
            filter_status = st.selectbox("Show:", ["All", "Same", "Different", "Error"], index=0)
        
        for api_id, api_data in res['api_results'].items():
            if filter_status == "Different" and api_data['overall_status'] == "Consistent":
                continue
            if filter_status == "Same" and api_data['overall_status'] != "Consistent":
                continue
            if filter_status == "Error" and api_data['overall_status'] != "Error":
                continue
                
            # Calculate Similarity
            # We take the first two environments for a rough similarity score if multiple exist
            # Or average them? Let's just take Ref vs First Target for the score display
            similarity_score = 100
            if api_data['overall_status'] == "Inconsistent" and 'comparisons' in api_data:
                # DeepDiff doesn't give a simple ratio. 
                # We can use difflib ratio on the JSON strings of the first pair
                try:
                    env_keys = list(api_data['data_by_env'].keys())
                    if len(env_keys) >= 2:
                        ref_content = json.dumps(api_data['data_by_env'][env_keys[0]]['data'], sort_keys=True)
                        target_content = json.dumps(api_data['data_by_env'][env_keys[1]]['data'], sort_keys=True)
                        similarity_score = int(difflib.SequenceMatcher(None, ref_content, target_content).ratio() * 100)
                except:
                    similarity_score = 0
            elif api_data['overall_status'] == "Error":
                similarity_score = 0
            
            # Title Styling
            icon = "🟢" if api_data['overall_status'] == "Consistent" else "🔴"
            title_text = f"{icon} [{similarity_score}%] {api_data['name']}"
            
            # Custom Expander
            with st.expander(title_text):
                comparison_data = []
                debug_info = None
                
                for env_id, env_entry in api_data['data_by_env'].items():
                    content_to_show = env_entry['data'].copy()
                    if "_debug_request" in content_to_show:
                        debug_info = content_to_show.pop("_debug_request")
                    
                    comparison_data.append({
                        "name": env_entry['env_name'],
                        "content": content_to_show
                    })
                
                if debug_info:
                    # Nested expanders are not allowed. Use checkbox to toggle.
                    if st.checkbox("🐞 Show Debug Info", key=f"debug_{api_id}_{res['timestamp']}"):
                        st.json(debug_info)
                
                st.markdown(generate_side_by_side_html(comparison_data), unsafe_allow_html=True)
                
                # Removed Detailed Diff JSON display as per user request


def render_debugger():
    st.title("🛠️ Single API Debugger")
    # st.markdown("Interactively test an API against a specific environment.") # Reduced clutter
    
    # --- Layout: Main Page (No Sidebar) ---
    
    # 1. Selection Row
    col_env, col_api, col_reset = st.columns([3, 3, 1])
    
    with col_env:
        env_opts = {e['id']: (e.get('name') or "Unnamed") for e in st.session_state.environments}
        selected_env_id = st.selectbox(
            "Environment",
            options=list(env_opts.keys()),
            format_func=lambda x: env_opts[x],
            key="debug_env_select"
        )
        selected_env = next((e for e in st.session_state.environments if e['id'] == selected_env_id), None)

    with col_api:
        api_opts = {t['id']: (t.get('name') or "Unnamed API") for t in st.session_state.api_templates}
        selected_api_id = st.selectbox(
            "Load Collection Item",
            options=list(api_opts.keys()),
            format_func=lambda x: api_opts[x],
            key="debug_api_select"
        )
        selected_api = next((t for t in st.session_state.api_templates if t['id'] == selected_api_id), None)

    with col_reset:
        st.write("") # Spacer
        st.write("")
        if st.button("🔄 Reset", use_container_width=True):
            if 'debug_api_id' in st.session_state: del st.session_state['debug_api_id']
            st.rerun()

    # Initialize/Update State from Template
    if 'debug_api_id' not in st.session_state or st.session_state.debug_api_id != selected_api_id:
        st.session_state.debug_api_id = selected_api_id
        if selected_api:
            st.session_state.debug_method = selected_api.get('method', 'GET')
            st.session_state.debug_path = selected_api.get('relative_path', '')
            st.session_state.debug_params = json.dumps(selected_api.get('params', {}), indent=2, ensure_ascii=False) if selected_api.get('params') else "{}"
            st.session_state.debug_body = json.dumps(selected_api.get('json_body', {}), indent=2, ensure_ascii=False) if selected_api.get('json_body') else "{}"
            
            # Merge Env Headers and API Headers for display
            env_headers = selected_env.get('headers', {}) if selected_env else {}
            if isinstance(env_headers, str):
                try: env_headers = json.loads(env_headers)
                except: env_headers = {}
            
            api_headers = selected_api.get('headers', {})
            if isinstance(api_headers, str):
                try: api_headers = json.loads(api_headers)
                except: api_headers = {}
                
            combined_headers = {**env_headers, **api_headers}
            st.session_state.debug_headers = json.dumps(combined_headers, indent=2, ensure_ascii=False)
        else:
             st.session_state.debug_method = "GET"
             st.session_state.debug_path = ""
             st.session_state.debug_headers = "{}"
             st.session_state.debug_params = "{}"
             st.session_state.debug_body = "{}"

    st.markdown("---")
    
    # 2. Request Details
    r_col1, r_col2 = st.columns([1, 4])
    with r_col1:
         method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE", "PATCH"], 
                               index=["GET", "POST", "PUT", "DELETE", "PATCH"].index(st.session_state.debug_method) if st.session_state.debug_method in ["GET", "POST", "PUT", "DELETE", "PATCH"] else 0,
                               label_visibility="collapsed")
    with r_col2:
         path = st.text_input("Path", value=st.session_state.debug_path, label_visibility="collapsed", placeholder="/api/endpoint")

    # Tabs for Details
    tab_body, tab_headers, tab_params, tab_extract = st.tabs(["Body", "Headers", "Params", "Post-Process"])
    
    with tab_body:
        body_str = st.text_area("Request Body (JSON)", value=st.session_state.debug_body, height=150)
    with tab_headers:
        headers_str = st.text_area("Request Headers (JSON)", value=st.session_state.debug_headers, height=150)
    with tab_params:
        params_str = st.text_area("Query Params (JSON)", value=st.session_state.debug_params, height=150)
    
    # --- New Feature: Post-Process Extraction ---
    with tab_extract:
        st.info("Extract values from response to update environment variables.")
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            extract_var_name = st.text_input("Target Variable Name", placeholder="e.g. auth_token", help="Variable to update/create in the selected environment")
        with ex_col2:
            extract_json_path = st.text_input("JSON Path", placeholder="e.g. $.result.token", help="Path to value in response JSON")
            
    st.markdown("<br>", unsafe_allow_html=True)
    send_clicked = st.button("🚀 Send Request", type="primary", use_container_width=True)

    # --- Response Area ---
    if send_clicked:
        st.markdown("---")
        st.subheader("Response")
        
        # Construct temporary template
        temp_template = {
            "id": "debug_temp",
            "name": "Debug Request",
            "relative_path": path,
            "method": method,
            "headers": headers_str, 
            "params": params_str, 
            "json_body": body_str
        }
        
        try:
            custom_headers = json.loads(headers_str) if headers_str.strip() else {}
        except:
            custom_headers = {}
            st.warning("Invalid JSON in Headers. Sending empty headers.")

        with st.spinner("Sending request..."):
            temp_template['headers'] = custom_headers
            # Pass empty dict for context if None, logic.py handles it now regardless
            result = fetch_api_data(selected_env, temp_template, {})
            
        # Separate Debug Info
        debug_info = None
        if isinstance(result, dict) and "_debug_request" in result:
            debug_info = result.pop("_debug_request")
            
        # Display Status Code if available
        status_code = result.get("_status_code", "N/A") if isinstance(result, dict) else "N/A"
        if "_status_code" in result: del result["_status_code"]
        
        # 1. Status Bar
        if isinstance(result, dict) and "error" in result and result.get("status") == "failed":
            st.error(f"❌ Failed: {result['error']}")
        else:
            st.success(f"✅ Success (Status: {status_code})")
            
            # --- Logic: Post-Process Extraction ---
            if extract_var_name and extract_json_path:
                from logic import extract_value_from_response
                # Reuse existing extraction logic which takes a list of rules
                # Rule format: {"source": "json_path", "target_var": "var_name"}
                rule = {"source": extract_json_path, "target_var": extract_var_name}
                extracted = extract_value_from_response(result, [rule])
                
                if extract_var_name in extracted:
                    new_val = extracted[extract_var_name]
                    
                    # Update Environment Variables
                    # 1. Check if var exists
                    var_found = False
                    for v in selected_env['variables']:
                        if v['key'] == extract_var_name:
                            v['value'] = str(new_val)
                            var_found = True
                            break
                    
                    # 2. Key does not exist -> Create
                    if not var_found:
                        selected_env['variables'].append({
                            "key": extract_var_name,
                            "value": str(new_val),
                            "description": "Extracted from Playground"
                        })
                        
                    # 3. Save to File
                    save_json_file("environments.json", st.session_state.environments) # HARDCODED PATH mostly safe here as it matches defaults, but ideally passed in
                    st.toast(f"✅ Updated variable '{extract_var_name}' with value: {new_val}", icon="💾")
                else:
                    st.warning(f"⚠️ Could not find path '{extract_json_path}' in response.")

        # 2. Debug Info (Collapsible)
        if debug_info:
            with st.expander("ℹ️ Request Details"):
                st.json(debug_info)

        # 3. Response Body
        st.json(result)
