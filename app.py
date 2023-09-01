import streamlit as st
from src import auth, route, source_data, dept


def run():
    """Main streamlit app entry point"""
    # Fetch source data - do this before auth to ensure all requests to app cause data refresh
    # Read, parse, and cache (via @st.cache_data) source data
    with st.spinner("Initializing..."):
        src_data = source_data.from_db(source_data.DEFAULT_DB_FILE)

    # Handle routing based on query parameters
    query_params = st.experimental_get_query_params()
    route_id = route.route_by_query(query_params)

    # Check for access to API resources first
    if route_id == route.CLEAR_CACHE:
        return clear_cache()

    # Interactive user authentication for access to dashboard pages
    if not auth.authenticate():
        return st.stop()

    # Render page based on the route
    if src_data is None:
        return st.write("No data available. Please contact administrator.")
    if route_id == route.DEFAULT:
        data = dept.base.process(
            dept.base.DEPT_CONFIG[route.IMAGING],
            {"dept": "ALL", "month": "2023-03", "pay_period": "2023-01"},
            src_data,
        )
        st.write(data.hours)
        st.write(data.hours_for_month)
        st.write(data.hours_ytd)
        st.write(data.volumes)
        st.write(data.income_stmt)
        st.write(
            "Please contact your administrator for a department specific link to access your dashboard."
        )


def clear_cache():
    """
    Clear Streamlit cache so source_data module will reread DB from disk on next request
    """
    st.cache_data.clear()
    return st.markdown(
        'Cache cleared. <a href="/" target="_self">Return to dashboard.</a>',
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="PRH Dashboard", layout="wide", initial_sidebar_state="auto"
)
run()
