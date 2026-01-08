import streamlit as st
from logic import execute_comparison_run, save_json_file

def render_dashboard():
    st.title("📊 Dashboard")
    
    @st.dialog("Delete Record")
    def confirm_delete(index, run_id):
        st.warning(f"Are you sure you want to delete this record? (ID: {run_id})")
        c1, c2 = st.columns(2)
        if c1.button("Cancel", use_container_width=True):
            st.rerun()
        if c2.button("Confirm Delete", type="primary", use_container_width=True):
            st.session_state.comparison_history.pop(index)
            pm = st.session_state.project_manager
            paths = pm.get_project_paths(st.session_state.current_project_id)
            save_json_file(paths['history_file'], st.session_state.comparison_history)
            st.session_state['deletion_success'] = True
            st.rerun()

    if st.session_state.get('deletion_success'):
        st.toast("✅ Record deleted successfully!")
        del st.session_state['deletion_success']
    
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
    h_cols = [1.3, 1.8, 1, 1.2, 3.2, 3]
    h1, h2, h3, h4, h5, h6 = st.columns(h_cols)
    h1.markdown("**Time**")
    h2.markdown("**Environments**")
    h3.markdown("**APIs**")
    h4.markdown("**Result**")
    h5.markdown("**Action**")
    h6.markdown("**Comment**")
    st.markdown("---")

    for i, run in enumerate(st.session_state.comparison_history):
        c1, c2, c3, c4, c5, c6 = st.columns(h_cols)
        c1.write(run['timestamp'])
        c2.write(", ".join(run['envs']))
        
        # API List Popover
        with c3.popover(f"🔍 {run['api_count']}"):
            api_list = []
            for uid, details in run.get('api_results', {}).items():
                path = details.get('relative_path')
                if not path: # Fallback for old history
                    path = next((t['relative_path'] for t in st.session_state.api_templates if t['id'] == uid), "N/A")
                api_list.append({
                    "Name": details.get('name', 'Unknown'),
                    "Path": path
                })
            if api_list:
                st.table(api_list)
            else:
                st.caption("No detailed API list available.")

        c4.write(f"✅ {run['consistent_count']}  ❌ {run['inconsistent_count']}")
        
        # Action Column (View, Rerun, Delete)
        v_col, r_col, d_col = c5.columns([1, 1, 0.6])
        if v_col.button("View", key=f"view_{run['run_id']}", use_container_width=True):
            st.session_state.current_run_results = run
            st.session_state.page = "comparator"
            st.rerun()
        
        if r_col.button("Rerun", key=f"rerun_{run['run_id']}", use_container_width=True):
            # ... existing rerun logic ...
            with st.spinner("Rerunning..."):
                env_name_to_id = {e['name']: e['id'] for e in st.session_state.environments}
                run_env_ids = [env_name_to_id[name] for name in run['envs'] if name in env_name_to_id]
                run_api_ids = list(run['api_results'].keys())
                
                if len(run_env_ids) < 2:
                    st.error("Error: Environments missing.")
                elif not run_api_ids:
                    st.error("Error: APIs missing.")
                else:
                    new_results = execute_comparison_run(
                        run_api_ids,
                        run_env_ids,
                        st.session_state.environments,
                        st.session_state.api_templates
                    )
                    st.session_state.comparison_history.insert(0, new_results)
                    pm = st.session_state.project_manager
                    paths = pm.get_project_paths(st.session_state.current_project_id)
                    save_json_file(paths['history_file'], st.session_state.comparison_history)
                    st.session_state.current_run_results = new_results
                    st.success("Rerun done!")
                    st.rerun()

        if d_col.button("🗑️", key=f"btn_del_{run['run_id']}", use_container_width=True):
            confirm_delete(i, run['run_id'])

        # Comment Column (Persistent)
        comment_val = run.get('comment', "")
        new_comment = c6.text_input("Comment", value=comment_val, key=f"cmt_{run['run_id']}", label_visibility="collapsed")
        if new_comment != comment_val:
            run['comment'] = new_comment
            pm = st.session_state.project_manager
            paths = pm.get_project_paths(st.session_state.current_project_id)
            save_json_file(paths['history_file'], st.session_state.comparison_history)
            st.rerun()

        st.markdown("<hr style='margin: 5px 0; opacity: 0.5;'>", unsafe_allow_html=True)

