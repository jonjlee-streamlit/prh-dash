import streamlit as st
from src import auth, route, source_data, dept, update


def run():
    """Main streamlit app entry point"""
    # Fetch source data - do this before auth to ensure all requests to app cause data refresh
    # Read, parse, and cache (via @st.cache_data) source data
    with st.spinner("Initializing..."):
        source_data.fetch_source_file_to_disk(
            source_data.DEFAULT_DB_FILE,
            st.secrets.get("data_url"),
            st.secrets.get("data_key"),
        )
        src_data = source_data.from_db(source_data.DEFAULT_DB_FILE)

    # Handle routing based on query parameters
    route_id = route.route_by_query(st.query_params)

    # Check for access to update / API resources first
    if route_id == route.UPDATE:
        return update.show_page()
    elif route_id == route.FETCH:
        return force_fetch_data()
    elif route_id == route.CLEAR_CACHE:
        return clear_cache()

    # Render page based on the route
    if src_data is None:
        return st.write("No data available. Please contact administrator.")
    elif route_id in route.DEPTS:
        # Interactive user authentication for access to dashboard pages
        if not auth.authenticate():
            return st.stop()

        return dept.base.dept_page(src_data, route_id)
    else:
        return show_index()


def clear_cache():
    """
    Clear Streamlit cache so source_data module will reread DB from disk on next request
    """
    st.cache_data.clear()
    return st.markdown(
        'Cache cleared. <a href="/" target="_self">Return to dashboard.</a>',
        unsafe_allow_html=True,
    )


def force_fetch_data():
    """
    Force re-fetch of source data from remote URL
    """
    source_data.fetch_source_file_to_disk(
        source_data.DEFAULT_DB_FILE,
        st.secrets.get("data_url"),
        st.secrets.get("data_key"),
        force=True,
    )
    return st.markdown(
        'Data re-fetched. <a href="/" target="_self">Return to dashboard.</a>',
        unsafe_allow_html=True,
    )


def show_index():
    """
    Show links to the various dashboards
    """
    links = []
    for r in route.DEPTS:
        dept_name = dept.base.configs.DEPT_CONFIG[r].name
        links.append(f'* <a href="/?dept={r}" target="_self">{dept_name}</a>')

    st.header("Dashboards")
    st.markdown("\n".join(links), unsafe_allow_html=True)


st.set_page_config(
    page_title="PRH Dashboard", layout="wide", initial_sidebar_state="auto"
)
run()
