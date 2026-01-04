import streamlit as st
import pandas as pd
import json
import difflib
import time
import uuid
from logic import execute_comparison_run, save_json_file
from .common import generate_side_by_side_html
from report_utils import generate_pdf_report, generate_word_report

def render_comparator(history_file, env_config_file, api_template_file):
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

        # Build DataFrame for Display/Edit
        if not st.session_state.api_templates:
            api_df = pd.DataFrame(columns=["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract", "id"])
        else:
            api_df = pd.DataFrame(st.session_state.api_templates)
        
        # Fill missing columns
        for c in ["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract", "id"]:
             if c not in api_df.columns:
                 api_df[c] = None
        
        # Stringify JSON fields for editing
        for json_col in ["headers", "params", "json_body", "extract"]:
            if json_col in api_df.columns:
                api_df[json_col] = api_df[json_col].apply(lambda x: to_json_str(x) if isinstance(x, (dict, list)) else (x if x else ""))
        
        # Select column init
        if "Select" in api_df.columns:
            api_df["Select"] = api_df["Select"].fillna(False).astype(bool)
        else:
            api_df.insert(0, "Select", False)

        # Placeholder for validation/error messages
        comp_msg_placeholder = st.empty()
        
        # Success message for auto-save (Optional, but good for feedback)
        if 'comparator_autosave_success' in st.session_state and st.session_state.comparator_autosave_success:
             if 'save_timestamp_comp' not in st.session_state: st.session_state.save_timestamp_comp = time.time()
             if time.time() - st.session_state.save_timestamp_comp < 3:
                 comp_msg_placeholder.success("✅ Changes Saved")
             else:
                 st.session_state.comparator_autosave_success = False
                 comp_msg_placeholder.empty()

        edited_selection = st.data_editor(
            api_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=True, width="small"),
                "id": st.column_config.TextColumn(disabled=True, width="small"),
                "order": st.column_config.NumberColumn("Order", width="small", disabled=False),
                "name": st.column_config.TextColumn("Name", width="medium"),
                "relative_path": st.column_config.TextColumn("Path", width="medium"),
                "method": st.column_config.SelectboxColumn("Method", options=["GET", "POST", "PUT", "DELETE", "PATCH"], width="small", required=True),
                "headers": st.column_config.TextColumn("Headers (JSON)", width="medium"),
                "json_body": st.column_config.TextColumn("Body (JSON)", width="medium"),
                "extract": st.column_config.TextColumn("Post Action", width="medium"),
            },
            column_order=["Select", "order", "name", "relative_path", "method", "headers", "json_body", "extract"], 
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key=f"comparator_api_editor_{len(api_df)}"
        )
        
        # LOGIC: AUTO-SAVE Changes in Comparator
        def clean_for_diff(df):
            d = df.drop(columns=["Select"], errors="ignore").copy()
            for col in d.columns:
                 d[col] = d[col].astype(str).replace("None", "").replace("nan", "").str.strip()
            return d.fillna("")
            
        has_changes = False
        if not clean_for_diff(api_df).equals(clean_for_diff(edited_selection)):
             has_changes = True

        if has_changes:
            try:
                cleaned_data = json.loads(edited_selection.to_json(orient="records"))
                filtered_data = []
                for row in cleaned_data:
                    # Skip empty rows (from dynamic addition if unused)
                    if not row.get('relative_path') and not row.get('name'): continue
                    
                    if 'Select' in row: del row['Select']
                    if not row.get('id'): row['id'] = str(uuid.uuid4())
                    row['order'] = int(row.get('order', 0) or 0)
                    
                    for field in ['params', 'json_body', 'headers', 'extract']:
                        val = row.get(field)
                        if isinstance(val, str):
                            try:
                                row[field] = json.loads(val) if val.strip() else (None if field != 'extract' else [])
                                if field == 'extract' and not isinstance(row[field], list): row[field] = []
                            except:
                                row[field] = {} if field != 'extract' else []
                        if field == 'headers' and (not isinstance(row.get('headers'), dict)): row['headers'] = {}
                        if field == 'extract' and (not isinstance(row.get('extract'), list)): row['extract'] = []

                    filtered_data.append(row)
                
                filtered_data.sort(key=lambda x: (x.get('order', 0), x.get('name', '')))
                
                st.session_state.api_templates = filtered_data
                save_json_file(api_template_file, st.session_state.api_templates)
                st.session_state.comparator_autosave_success = True
                st.session_state.save_timestamp_comp = time.time()
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

        # Robust Selection mapping
        try:
            # We filter the *edited* dataframe for selection
            selected_rows = edited_selection[edited_selection["Select"] == True]
            selected_api_ids = selected_rows["id"].dropna().tolist()
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
                with st.spinner("🚀 Comparing APIs across environments..."):
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
                
                # Save Environments (extraction might have updated them)
                save_json_file(env_config_file, st.session_state.environments)
                
                st.success("Comparison completed!")
                st.rerun()

    # --- Analysis / Results View ---
    if st.session_state.current_run_results:
        st.markdown("---")
        res = st.session_state.current_run_results
        
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

        # Pre-calculate similarity scores for all APIs for report export
        for api_id, api_data in res['api_results'].items():
            similarity_score = 100
            if (api_data['overall_status'] == "Inconsistent" or api_data['overall_status'] == "Error") and 'comparisons' in api_data:
                try:
                    env_keys = list(api_data['data_by_env'].keys())
                    if len(env_keys) >= 2:
                        ref_content = json.dumps({k:v for k,v in api_data['data_by_env'][env_keys[0]]['data'].items() if not k.startswith('_')}, sort_keys=True)
                        target_content = json.dumps({k:v for k,v in api_data['data_by_env'][env_keys[1]]['data'].items() if not k.startswith('_')}, sort_keys=True)
                        similarity_score = int(difflib.SequenceMatcher(None, ref_content, target_content).ratio() * 100)
                except:
                    similarity_score = 0
            api_data['similarity'] = similarity_score

        exp_col1, exp_col2, _ = st.columns([1, 1, 4])
        with exp_col1:
            try:
                pdf_data = generate_pdf_report(res)
                st.download_button(
                    label="⬇️ Export PDF",
                    data=pdf_data,
                    file_name=f"Comparison_Report_{res['timestamp'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF Error: {str(e)[:50]}...")
        with exp_col2:
            try:
                word_data = generate_word_report(res)
                st.download_button(
                    label="⬇️ Export Word",
                    data=word_data,
                    file_name=f"Comparison_Report_{res['timestamp'].replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Word Error: {str(e)[:50]}...")
        
        f_col1, f_col2 = st.columns([1, 4])
        with f_col1:
            filter_status = st.selectbox("Show:", ["All", "Same", "Different", "Error"], index=0)
        
        for api_id, api_data in res['api_results'].items():
            if filter_status == "Different" and api_data['overall_status'] == "Consistent": continue
            if filter_status == "Same" and api_data['overall_status'] != "Consistent": continue
            if filter_status == "Error" and api_data['overall_status'] != "Error": continue
                
            similarity_score = api_data.get('similarity', 100)
            
            icon = "🟢" if api_data['overall_status'] == "Consistent" else "🔴"
            title_text = f"{icon} [{similarity_score}%] {api_data['name']}"
            
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
                    if st.checkbox("🐞 Show Debug Info", key=f"debug_{api_id}_{res['timestamp']}"):
                        st.json(debug_info)
                
                st.markdown(generate_side_by_side_html(comparison_data), unsafe_allow_html=True)
