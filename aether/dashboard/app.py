"""Aether-CyberAgent: Real-time Security Dashboard.

Streamlit-based visualization of the security pipeline including:
- DAG dependency graph visualization
- Code diff viewer (before/after patches)
- Pipeline metrics and state
- Vulnerability timeline
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Aether-CyberAgent Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme styling
st.markdown('''
<style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1d23; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    h1 { color: #00d4ff; }
    h2 { color: #7c3aed; }
</style>
''', unsafe_allow_html=True)

def load_state_log() -> list[dict]:
    """Load the pipeline state log."""
    state_path = Path('.aether/state_log.json')
    if state_path.exists():
        return json.loads(state_path.read_text())
    return []

def load_sarif_reports() -> list[dict]:
    """Load available SARIF reports."""
    reports_dir = Path('.aether/reports')
    reports = []
    if reports_dir.exists():
        for f in reports_dir.glob('sarif_*.json'):
            reports.append(json.loads(f.read_text()))
    return reports

def main():
    # Header
    st.title('🛡️ Aether-CyberAgent Dashboard')
    st.caption('Autonomous Multi-Agent AI Security Platform')
    
    # Sidebar
    with st.sidebar:
        st.header('Navigation')
        page = st.radio('Select View', [
            '📊 Overview',
            '🗺️ Dependency Graph',
            '📝 Code Diffs',
            '📈 Pipeline History',
            '📋 SARIF Reports',
        ])
        
        st.divider()
        if st.button('🔄 Refresh Data'):
            st.rerun()
    
    state_log = load_state_log()
    sarif_reports = load_sarif_reports()
    
    if page == '📊 Overview':
        render_overview(state_log, sarif_reports)
    elif page == '🗺️ Dependency Graph':
        render_dependency_graph()
    elif page == '📝 Code Diffs':
        render_code_diffs(sarif_reports)
    elif page == '📈 Pipeline History':
        render_pipeline_history(state_log)
    elif page == '📋 SARIF Reports':
        render_sarif_reports(sarif_reports)

def render_overview(state_log, sarif_reports):
    """Render the overview metrics page."""
    col1, col2, col3, col4 = st.columns(4)
    
    total_events = len(state_log)
    passed = sum(1 for e in state_log if e.get('event') == 'verification_passed')
    failed = sum(1 for e in state_log if e.get('event') == 'verification_failed')
    
    col1.metric('Total Events', total_events)
    col2.metric('Verified Patches', passed)
    col3.metric('Failed Verifications', failed)
    col4.metric('SARIF Reports', len(sarif_reports))
    
    if state_log:
        st.subheader('Recent Pipeline Activity')
        # Show recent events as a timeline
        for event in reversed(state_log[-20:]):
            icon = {
                'verification_passed': '✅',
                'verification_failed': '❌',
                'yellow_team_error': '⚠️',
            }.get(event.get('event', ''), 'ℹ️')
            
            st.markdown(f"{icon} **{event.get('event', 'unknown')}** "
                       f"| Phase: `{event.get('phase', 'N/A')}` "
                       f"| {event.get('timestamp', 'N/A')}")
    else:
        st.info('No pipeline data yet. Run `aether scan .` to generate data.')

def render_dependency_graph():
    """Render the dependency graph visualization."""
    st.subheader('🗺️ Codebase Dependency Graph')
    
    graph_path = Path('.aether/dependency_graph.json')
    if graph_path.exists():
        graph_data = json.loads(graph_path.read_text())
        # Use streamlit's native graphviz or networkx visualization
        st.json(graph_data)
    else:
        st.info('No dependency graph data. Run a scan first.')

def render_code_diffs(sarif_reports):
    """Render before/after code diffs."""
    st.subheader('📝 Patched Code Diffs')
    
    if not sarif_reports:
        st.info('No SARIF reports with patches available.')
        return
    
    for report in sarif_reports:
        for run in report.get('runs', []):
            for result in run.get('results', []):
                with st.expander(f"{result.get('ruleId', 'Unknown')} - {result.get('message', {}).get('text', '')}"):
                    for fix in result.get('fixes', []):
                        st.code(fix.get('description', {}).get('text', 'No diff available'), language='diff')

def render_pipeline_history(state_log):
    """Render pipeline execution history."""
    st.subheader('📈 Pipeline Execution History')
    
    if not state_log:
        st.info('No pipeline history yet.')
        return
    
    import pandas as pd
    df = pd.DataFrame(state_log)
    st.dataframe(df, use_container_width=True)

def render_sarif_reports(sarif_reports):
    """Render raw SARIF reports."""
    st.subheader('📋 SARIF v2.1.0 Reports')
    
    if not sarif_reports:
        st.info('No SARIF reports generated yet.')
        return
    
    for i, report in enumerate(sarif_reports):
        with st.expander(f'Report {i + 1}'):
            st.json(report)

if __name__ == '__main__':
    main()
