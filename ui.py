import streamlit as st
import pandas as pd
import json
import uuid
import difflib
import html
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
    
    tab1, tab2 = st.tabs(["API Templates", "Environments"])
    
    with tab1:
        # --- Header Actions ---
        col_header, col_actions = st.columns([1, 1])
        with col_header:
            st.subheader("Manage API Templates")
            st.caption(f"Total APIs: {len(st.session_state.api_templates)}")
            
        with col_actions:
            c_import, c_clear = st.columns([1, 1])
            with c_import:
                with st.popover("📥 Import APIs", use_container_width=True):
                    if 'uploader_key' not in st.session_state:
                        st.session_state.uploader_key = str(uuid.uuid4())
                    
                    uploaded_file = st.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed", key=st.session_state.uploader_key)
                    
                    if uploaded_file is not None:
                        try:
                            imported_data = json.load(uploaded_file)
                            new_apis = []
                            # 1. Check for Apifox Project (New Format)
                            if isinstance(imported_data, dict) and 'apifoxProject' in imported_data:
                                st.info("Detected Apifox Project format. Extracting cases...")
                                new_apis = parse_apifox_project(imported_data)
                            # 2. Check for OpenAPI / Swagger
                            elif isinstance(imported_data, dict) and ('openapi' in imported_data or 'swagger' in imported_data):
                                st.info("Detected OpenAPI/Swagger format. Parsing...")
                                new_apis = parse_openapi_spec(imported_data)
                            else:
                                # 2. Handle Standard List
                                raw_list = []
                                if isinstance(imported_data, dict):
                                    for key in ["apis", "data", "items", "list"]:
                                        if key in imported_data and isinstance(imported_data[key], list):
                                            raw_list = imported_data[key]; break
                                    if not raw_list and 'relative_path' in imported_data: raw_list = [imported_data]
                                elif isinstance(imported_data, list):
                                    raw_list = imported_data
                                if raw_list: new_apis = raw_list
                                else: st.error("Invalid JSON format.")

                            # 3. Merge
                            if new_apis:
                                current_ids = {t['id'] for t in st.session_state.api_templates if 'id' in t}
                                count = 0
                                for item in reversed(new_apis):
                                    if 'name' in item and 'relative_path' in item:
                                        if 'id' not in item or item['id'] in current_ids: item['id'] = str(uuid.uuid4())
                                        for f in ['headers', 'params', 'json_body']:
                                            if f not in item or item[f] is None: item[f] = {}
                                        st.session_state.api_templates.insert(0, item) # Insert at top
                                        count += 1
                                
                                save_json_file(api_template_file, st.session_state.api_templates)
                                st.success(f"Imported {count} APIs!")
                                st.session_state.uploader_key = str(uuid.uuid4()) # Reset
                                st.rerun()
                                
                        except json.JSONDecodeError as e: st.error(f"Invalid JSON: {e}")
                        except Exception as e: st.error("Import failed"); st.exception(e)

            with c_clear:
                with st.popover("🗑️ Clear All", use_container_width=True):
                    st.write("Are you sure you want to delete all API templates?")
                    if st.button("Confirm Delete", type="primary", use_container_width=True):
                        st.session_state.api_templates = []
                        save_json_file(api_template_file, [])
                        st.rerun()

        # --- Data Table (No Pagination, Native Selection) ---
        
        api_df = pd.DataFrame(st.session_state.api_templates)
        
        # Ensure Columns
        cols = ["name", "relative_path", "method", "headers", "params", "json_body", "id"]
        for c in cols:
            if c not in api_df.columns: api_df[c] = None

        # Helper to stringify JSON for editing
        def to_json_str(x):
            if x is None: return ""
            if isinstance(x, (dict, list)): return json.dumps(x, ensure_ascii=False)
            return str(x) if x else ""

        for json_col in ["headers", "params", "json_body"]:
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
        
        # Action Bar (Save & Delete)
        act_col1, act_col2 = st.columns([1, 4])
        with act_col1:
            save_clicked = st.button("💾 Save", type="primary", use_container_width=True)
            
        with act_col2:
            delete_clicked = st.button("Delete", type="primary", use_container_width=False)

        # Show Editor
        # Data Editor (Force Reload)
        edited_api_df = st.data_editor(
            api_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=True, width="small"),
                "name": "API Name",
                "relative_path": "Path",
                "method": st.column_config.SelectboxColumn("Method", options=["GET", "POST", "PUT", "DELETE"], width="small"),
                "headers": st.column_config.TextColumn("Headers (JSON)", width="medium"),
                "params": st.column_config.TextColumn("Params (JSON)", width="medium"),
                "json_body": st.column_config.TextColumn("Body (JSON)", width="medium"),
                "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
            },
            column_order=["Select", "name", "relative_path", "method", "headers", "params", "json_body"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic"
        )
        
        # LOGIC: SAVE
        if save_clicked:
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
                    
                    for field in ['params', 'json_body', 'headers']:
                        val = row.get(field)
                        if isinstance(val, str):
                            try:
                                row[field] = json.loads(val) if val.strip() else None
                            except:
                                row[field] = {} 
                        if row.get('headers') is None: row['headers'] = {}
                    
                    filtered_data.append(row)

                st.session_state.api_templates = filtered_data
                save_json_file(api_template_file, st.session_state.api_templates)
                st.success("✅ Changes Saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

        # LOGIC: DELETE WITH CHECKBOX
        if delete_clicked:
            # Filter rows where Select is True
            to_delete = edited_api_df[edited_api_df["Select"] == True]
            
            if to_delete.empty:
                st.warning("Please select rows to delete using the 'Select' checkbox column.")
            else:
                ids_to_delete = set(to_delete["id"].dropna().tolist())
                
                if ids_to_delete:
                    # Filter out deleted IDs
                    new_list = [t for t in st.session_state.api_templates if t.get('id') not in ids_to_delete]
                    st.session_state.api_templates = new_list
                    save_json_file(api_template_file, st.session_state.api_templates)
                    st.success(f"Deleted {len(ids_to_delete)} items!")
                    st.rerun()
                    
    with tab2:
        st.subheader("Manage Environments")
        env_df = pd.DataFrame(st.session_state.environments)
        
        # Ensure auth_token column exists
        if "auth_token" not in env_df.columns:
            env_df["auth_token"] = ""
            
        edited_env_df = st.data_editor(
            env_df,
            num_rows="dynamic",
            column_config={
                "id": st.column_config.TextColumn(disabled=True, width="small"),
                "name": "Name",
                "base_url": "Base URL",
                "auth_token": st.column_config.TextColumn("Auth Token", width="medium", help="Bearer ..."),
                "headers": st.column_config.TextColumn("Extra Headers (JSON)", width="large"),
            },
            use_container_width=True,
            key="env_editor"
        )
        
        if st.button("Save Environments"):
            cleaned_data = json.loads(edited_env_df.to_json(orient="records"))
            for row in cleaned_data:
                if not row.get('id'):
                    row['id'] = str(uuid.uuid4())
                if isinstance(row.get('headers'), str):
                    try:
                        row['headers'] = json.loads(row['headers']) if row['headers'].strip() else {}
                    except json.JSONDecodeError:
                        st.warning(f"Invalid JSON in headers for {row.get('name')}.")
                        row['headers'] = {}
                    
            st.session_state.environments = cleaned_data
            save_json_file(env_config_file, st.session_state.environments)
            st.success("Environments Saved!")
def render_comparator(history_file):
    st.title("🚀 Comparator")
    
    # --- Execution Controls ---
    with st.expander("⚙️ Run Configuration", expanded=not st.session_state.current_run_results):
        st.subheader("Select Environments")
        # Horizontal Checkboxes
        cols = st.columns(4)
        selected_env_ids = []
        for i, env in enumerate(st.session_state.environments):
            col = cols[i % 4]
            if col.checkbox(env['name'], key=f"env_select_{env['id']}"):
                selected_env_ids.append(env['id'])
        # Helper to stringify JSON
        def to_json_str(x):
            return json.dumps(x, ensure_ascii=False) if x else ""
            
        st.subheader("Select APIs")
        
        # Move Start Button to Top Right (Header Area)
        # We really want it aligned with "Select APIs" header or similar.
        # But we are in an expander. Let's put it right above the table.
        
        col_header, col_btn = st.columns([6, 1])
        with col_header:
            st.caption(f"Total APIs: {len(st.session_state.api_templates)}")
        with col_btn:
            start_clicked = st.button("▶ Compare", type="primary", use_container_width=True)

        api_display_df = pd.DataFrame([
            {
                "Selected": False, 
                "Name": t['name'], 
                "Path": t['relative_path'], 
                "ID": t['id'],
                "Params": to_json_str(t.get('params')),
                "Body": to_json_str(t.get('json_body'))
            }
            for t in st.session_state.api_templates
        ])
        
        edited_selection = st.data_editor(
            api_display_df,
            column_config={
                "Selected": st.column_config.CheckboxColumn(required=True, width="small"),
                # "ID": "ID", # No hidden support, just exclude from order
                "Name": st.column_config.TextColumn(width="medium"),
                "Path": st.column_config.TextColumn(width="medium"),
                "Params": st.column_config.TextColumn(width="medium", help="JSON Params"),
                "Body": st.column_config.TextColumn(width="medium", help="JSON Body"),
            },
            column_order=["Selected", "Name", "Path", "Params", "Body"], # ID removed from view
            hide_index=True,
            use_container_width=True
        )
        
        selected_api_ids = edited_selection[edited_selection["Selected"]]["ID"].tolist()
        
        if start_clicked:
            if len(selected_env_ids) < 2:
                st.error("Please select at least 2 environments.")
            elif not selected_api_ids:
                st.error("Please select at least 1 API.")
            else:
                # Progress Callback
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, msg):
                    progress_bar.progress(current / total)
                    status_text.text(msg)
                
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
                    with st.expander("🐞 Debug Request Info"):
                        st.json(debug_info)
                
                st.markdown(generate_side_by_side_html(comparison_data), unsafe_allow_html=True)
                
                # Removed Detailed Diff JSON display as per user request

    if st.button("Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def render_debugger():
    st.title("🛠️ Single API Debugger")
    st.markdown("Interactively test an API against a specific environment.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Select Environment
        env_opts = {e['id']: e['name'] for e in st.session_state.environments}
        selected_env_id = st.selectbox(
            "1. Select Environment",
            options=list(env_opts.keys()),
            format_func=lambda x: env_opts[x],
            key="debug_env_select"
        )
        selected_env = next((e for e in st.session_state.environments if e['id'] == selected_env_id), None)

    with col2:
        # Select API Template to pre-fill
        api_opts = {t['id']: t['name'] for t in st.session_state.api_templates}
        # Add a "Custom" option? For now just templates.
        selected_api_id = st.selectbox(
            "2. Select API Template (Pre-fill)",
            options=list(api_opts.keys()),
            format_func=lambda x: api_opts[x],
            key="debug_api_select"
        )
        selected_api = next((t for t in st.session_state.api_templates if t['id'] == selected_api_id), None)

    st.markdown("---")
    st.subheader("Request Details")
    
    # Initialize session state for debug inputs if not present or if API changed
    # Also allow forcing a reset
    if 'debug_api_id' not in st.session_state or st.session_state.debug_api_id != selected_api_id:
        st.session_state.debug_api_id = selected_api_id
        st.session_state.debug_method = selected_api['method']
        st.session_state.debug_path = selected_api['relative_path']
        st.session_state.debug_params = json.dumps(selected_api.get('params'), indent=2, ensure_ascii=False) if selected_api.get('params') else "{}"
        st.session_state.debug_params = json.dumps(selected_api.get('params'), indent=2, ensure_ascii=False) if selected_api.get('params') else "{}"
        st.session_state.debug_body = json.dumps(selected_api.get('json_body'), indent=2, ensure_ascii=False) if selected_api.get('json_body') else "{}"
        
        # Merge Env Headers and API Headers for display
        env_headers = selected_env.get('headers', {}) if selected_env else {}
        if isinstance(env_headers, str):
             try: env_headers = json.loads(env_headers)
             except: env_headers = {}
        if not isinstance(env_headers, dict):
            env_headers = {}
             
        api_headers = selected_api.get('headers', {}) if selected_api else {}
        # If api_headers is string (from older config), parse it
        if isinstance(api_headers, str):
             try: api_headers = json.loads(api_headers)
             except: api_headers = {}
        if not isinstance(api_headers, dict):
            api_headers = {}

        # Combined default
        combined_headers = {**env_headers, **api_headers}
        st.session_state.debug_headers = json.dumps(combined_headers, indent=2, ensure_ascii=False)

    if st.button("🔄 Reset to Defaults"):
        del st.session_state['debug_api_id']
        st.rerun()

    # Editable Fields
    c1, c2 = st.columns([1, 3])
    with c1:
        method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"], index=["GET", "POST", "PUT", "DELETE"].index(st.session_state.debug_method))
    with c2:
        path = st.text_input("Relative Path", value=st.session_state.debug_path)
        
    c3, c4, c5 = st.columns(3)
    with c3:
        headers_str = st.text_area("Headers (JSON)", value=st.session_state.debug_headers, height=200)
    with c4:
        params_str = st.text_area("Params (JSON)", value=st.session_state.debug_params, height=200)
    with c5:
        body_str = st.text_area("Body (JSON)", value=st.session_state.debug_body, height=200)

    if st.button("🚀 Send Request", type="primary"):
        # Construct temporary template
        temp_template = {
            "id": "debug_temp",
            "name": "Debug Request",
            "relative_path": path,
            "method": method,
            "headers": headers_str, # Will be parsed by fetch_api_data logic if we update it, OR we parse here.
            # logic.py fetch_api_data expects 'headers' in env or constructed. 
            # Actually fetch_api_data merges env['headers']. 
            # We should pass these headers as if they are the FINAL headers.
            # But fetch_api_data logic currently merges env headers + auth token.
            # To support custom headers from Playground, we might need to pass them explicitly.
            "params": params_str, 
            "json_body": body_str
        }
        
        # We need to handle headers specially because fetch_api_data merges env headers.
        # If we want to OVERRIDE everything with what's in the text area, we should probably pass it differently.
        # Let's parse it here.
        try:
            custom_headers = json.loads(headers_str) if headers_str.strip() else {}
        except:
            custom_headers = {}
            st.warning("Invalid JSON in Headers. Sending empty headers.")

        with st.spinner("Sending request..."):
            # We pass custom_headers to fetch_api_data. 
            # We need to update fetch_api_data signature or pass it via template?
            # Let's pass it via template['headers'] and update logic.py to respect it.
            temp_template['headers'] = custom_headers
            result = fetch_api_data(selected_env, temp_template, None)
            
        st.markdown("### Response")
        
        # Separate Debug Info
        debug_info = None
        if isinstance(result, dict) and "_debug_request" in result:
            debug_info = result.pop("_debug_request")
            
        if debug_info:
            with st.expander("🐞 Debug Request Info", expanded=True):
                st.json(debug_info)
                
        if isinstance(result, dict) and "error" in result and "status" in result and result["status"] == "failed":
            st.error(f"Request Failed: {result['error']}")
        else:
            st.success("Request Successful")
            st.json(result)
