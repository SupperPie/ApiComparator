import streamlit as st
import json
from logic import fetch_api_data, save_json_file

def render_debugger():
    st.title("🛠️ Single API Debugger")
    
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
        st.write("")
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
    
    # Post-Process Extraction
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
                rule = {"source": extract_json_path, "target_var": extract_var_name}
                extracted = extract_value_from_response(result, [rule])
                
                if extract_var_name in extracted:
                    new_val = extracted[extract_var_name]
                    
                    # Update Environment Variables
                    var_found = False
                    for v in selected_env['variables']:
                        if v['key'] == extract_var_name:
                            v['value'] = str(new_val)
                            var_found = True
                            break
                    if not var_found:
                        selected_env['variables'].append({
                            "key": extract_var_name,
                            "value": str(new_val),
                            "description": "Extracted from Playground"
                        })
                    
                    save_json_file("environments.json", st.session_state.environments) # Note: path relies on default or needs to be passed in
                    st.toast(f"✅ Updated variable '{extract_var_name}' with value: {new_val}", icon="💾")
                else:
                    st.warning(f"⚠️ Could not find path '{extract_json_path}' in response.")

        # 2. Debug Info (Collapsible)
        if debug_info:
            with st.expander("ℹ️ Request Details"):
                st.json(debug_info)

        # 3. Response Body
        st.json(result)
