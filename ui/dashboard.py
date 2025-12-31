import streamlit as st

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
