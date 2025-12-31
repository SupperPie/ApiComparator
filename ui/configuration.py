import streamlit as st
import pandas as pd
import json
import uuid
import time
from logic import save_json_file, parse_openapi_spec, parse_apifox_project

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
                     if 'uploader_key' not in st.session_state: st.session_state.uploader_key = str(uuid.uuid4())
                     u_file = st.file_uploader("JSON", type=["json"], key=st.session_state.uploader_key)
                     if u_file:
                         try:
                            imported_data = json.load(u_file)
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
             if 'save_timestamp' not in st.session_state:
                 st.session_state.save_timestamp = time.time()
             
             if time.time() - st.session_state.save_timestamp < 3:
                 msg_placeholder.success("✅ Changes Saved")
             else:
                 st.session_state.autosave_success = False
                 msg_placeholder.empty()
        
        if 'autosave_error' in st.session_state and st.session_state.autosave_error:
             msg_placeholder.error(f"❌ Save Failed: {st.session_state.autosave_error}")

        # --- Data Table ---
        api_df = pd.DataFrame(st.session_state.api_templates)
        
        # Ensure Columns
        cols = ["name", "relative_path", "method", "headers", "params", "json_body", "extract", "id"]
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

        # Add Select Column for Deletion
        if "Select" not in api_df.columns:
            api_df.insert(0, "Select", False)
        else:
            api_df["Select"] = api_df["Select"].fillna(False).astype(bool)

        # Data Editor (Force Reload with key)
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
            num_rows="dynamic",
            key=f"config_api_editor_{len(api_df)}"
        )
        
        # LOGIC: AUTO-SAVE
        def clean_for_diff(df):
            d = df.drop(columns=["Select"], errors="ignore").copy()
            for col in d.columns:
                 d[col] = d[col].astype(str).replace("None", "").replace("nan", "").str.strip()
            return d.fillna("")

        has_changes = False
        if not clean_for_diff(api_df).equals(clean_for_diff(edited_api_df)):
             has_changes = True
        
        if has_changes:
            try:
                # Convert back to list of dicts
                cleaned_data = json.loads(edited_api_df.to_json(orient="records"))
                
                filtered_data = []
                for row in cleaned_data:
                    if not row.get('relative_path') and not row.get('name'):
                         continue

                    if 'Select' in row: del row['Select']
                    if not row.get('id'): row['id'] = str(uuid.uuid4())
                    row['order'] = int(row.get('order', 0) or 0)

                    for field in ['params', 'json_body', 'headers', 'extract']:
                        val = row.get(field)
                        if isinstance(val, str):
                            try:
                                row[field] = json.loads(val) if val.strip() else (None if field != 'extract' else [])
                                if field == 'extract' and not isinstance(row[field], list):
                                     row[field] = []
                            except:
                                row[field] = {} if field != 'extract' else []
                        if field == 'headers' and (not isinstance(row.get('headers'), dict)): row['headers'] = {}
                        if field == 'extract' and (not isinstance(row.get('extract'), list)): row['extract'] = []

                    filtered_data.append(row)

                filtered_data.sort(key=lambda x: (x.get('order', 0), x.get('name', '')))

                st.session_state.api_templates = filtered_data
                save_json_file(api_template_file, st.session_state.api_templates)
                st.session_state.autosave_success = True
                st.session_state.save_timestamp = time.time()
                st.session_state.autosave_error = None
                st.rerun()
            except Exception as e:
                st.session_state.autosave_error = str(e)
                st.error(f"Save failed: {e}")

        # LOGIC: DELETE
        if delete_selected_clicked:
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
        # Environments Tab
        env_list = st.session_state.environments
        for e in env_list:
            if "variables" not in e: e["variables"] = []
            if isinstance(e["variables"], str):
                 try: e["variables"] = json.loads(e["variables"]) 
                 except: e["variables"] = []
            if isinstance(e["variables"], dict):
                 e["variables"] = [{"key": k, "value": v, "description": ""} for k,v in e["variables"].items()]
            
            if "auth_token" not in e: e["auth_token"] = ""
            if "headers" not in e: e["headers"] = {}

            # Migration: Move Auth/Headers to Variables
            existing_keys = set()
            for v in e["variables"]:
                if isinstance(v, dict) and 'key' in v:
                    existing_keys.add(v['key'])
            
            if e.get("auth_token") and "auth_token" not in existing_keys:
                e["variables"].append({
                    "key": "auth_token", 
                    "value": e["auth_token"], 
                    "description": "Migrated from Auth Token field"
                })
                e["auth_token"] = "" 
                
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
                e["headers"] = {} 

        env_df = pd.DataFrame(env_list)
        if env_df.empty:
             env_df = pd.DataFrame(columns=["name", "base_url", "auth_token", "variables", "headers"])
        
        col_list, col_detail = st.columns([2, 3])
        
        with col_list:
            st.markdown("#### Environment List")
            if not env_list:
                st.info("No environments. Create one below.")
                selected_env_id = None
            else:
                env_map = {e['id']: e for e in env_list}
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
                )
            
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
                st.session_state.selected_env_id = new_id 
                save_json_file(env_config_file, st.session_state.environments)

            def delete_env():
                current = st.session_state.selected_env_id
                if current:
                     st.session_state.environments = [e for e in st.session_state.environments if e['id'] != current]
                     if st.session_state.environments:
                         st.session_state.selected_env_id = st.session_state.environments[0]['id']
                     else:
                         st.session_state.selected_env_id = None
                     save_json_file(env_config_file, st.session_state.environments)

            c_add, c_del = st.columns(2)
            c_add.button("➕ New", use_container_width=True, on_click=add_env)
            with c_del.popover("🗑️ Delete", use_container_width=True):
                st.markdown("Are you sure you want to delete this environment?")
                st.button("Confirm Delete", type="primary", on_click=delete_env)

        with col_detail:
            st.markdown("#### Configure Details")
            target_env = next((e for e in st.session_state.environments if e['id'] == selected_env_id), None)
            
            if not target_env:
                st.info("Select or create an environment to configure.")
            else:
                with st.container():
                     c_name, c_url = st.columns([1, 2])
                     new_name = c_name.text_input("Name", value=target_env.get('name', ''))
                     new_url = c_url.text_input("Base URL", value=target_env.get('base_url', ''))
                     
                     if new_name != target_env.get('name') or new_url != target_env.get('base_url'):
                         target_env['name'] = new_name
                         target_env['base_url'] = new_url
                         save_json_file(env_config_file, st.session_state.environments)
                         st.rerun()

                st.caption(f"Variables for: **{target_env.get('name')}**")
                st.info("💡 Tip: Add 'auth_token' or 'headers' (JSON) as variables to configure authentication and default headers.")

                var_list = target_env.get('variables', [])
                if not isinstance(var_list, list): var_list = []
                
                var_df = pd.DataFrame(var_list)
                if var_df.empty:
                    var_df = pd.DataFrame(columns=["key", "value", "description"])
                
                edited_vars = st.data_editor(
                    var_df,
                    num_rows="dynamic",
                    column_config={
                        "key": st.column_config.TextColumn("Variable", required=True),
                        "value": st.column_config.TextColumn("Value", width="medium"),
                        "description": st.column_config.TextColumn("Description", width="large"),
                    },
                    column_order=["key", "value", "description"],
                    use_container_width=True,
                    key=f"var_editor_{target_env['id']}"
                )
                    
                if st.button("💾 Save Configuration", key="save_env_vars"):
                    new_vars_list = json.loads(edited_vars.to_json(orient="records"))
                    new_vars_list = [v for v in new_vars_list if v.get('key')]
                    target_env['variables'] = new_vars_list
                    save_json_file(env_config_file, st.session_state.environments)
                    st.success(f"Saved configuration for {target_env.get('name')}")
