import streamlit as st
from logic import execute_comparison_run, save_json_file

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
    h1, h2, h3, h4, h5 = st.columns([2, 3, 1.5, 1.5, 2])
    h1.markdown("**Time**")
    h2.markdown("**Environments**")
    h3.markdown("**APIs**")
    h4.markdown("**Result**")
    h5.markdown("**Action**")
    st.markdown("---")

    for run in st.session_state.comparison_history:
        c1, c2, c3, c4, c5 = st.columns([2, 3, 1.5, 1.5, 2])
        c1.write(run['timestamp'])
        c2.write(", ".join(run['envs']))
        c3.write(f"{run['api_count']} APIs")
        c4.write(f"✅ {run['consistent_count']}  ❌ {run['inconsistent_count']}")
        
        c5_1, c5_2 = c5.columns(2)
        if c5_1.button("View", key=f"view_{run['run_id']}"):
            st.session_state.current_run_results = run
            st.session_state.page = "comparator"
            st.rerun()
        
        if c5_2.button("Rerun", key=f"rerun_{run['run_id']}"):
            with st.spinner("Rerunning comparison..."):
                # 1. Identify configs from run
                # The run record contains 'envs' (names) and 'api_results' (dict with api_ids as keys)
                # We need to map env names back to IDs
                env_name_to_id = {e['name']: e['id'] for e in st.session_state.environments}
                run_env_ids = [env_name_to_id[name] for name in run['envs'] if name in env_name_to_id]
                run_api_ids = list(run['api_results'].keys())
                
                if len(run_env_ids) < 2:
                    st.error("Cannot rerun: Environments not found or insufficient.")
                elif not run_api_ids:
                    st.error("Cannot rerun: No APIs found in history record.")
                else:
                    # 2. Execute
                    new_results = execute_comparison_run(
                        run_api_ids,
                        run_env_ids,
                        st.session_state.environments,
                        st.session_state.api_templates
                    )
                    
                    # 3. Save & Update
                    st.session_state.comparison_history.insert(0, new_results)
                    # Get paths from session_state if possible, or we might need to pass them
                    # In app.py, project_manager handles paths.
                    # pm is in session_state
                    pm = st.session_state.project_manager
                    paths = pm.get_project_paths(st.session_state.current_project_id)
                    save_json_file(paths['history_file'], st.session_state.comparison_history)
                    
                    st.session_state.current_run_results = new_results
                    st.success("Rerun completed!")
                    st.rerun()

        st.markdown("<hr style='margin: 5px 0; opacity: 0.5;'>", unsafe_allow_html=True)
