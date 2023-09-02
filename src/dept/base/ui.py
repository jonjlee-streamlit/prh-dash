import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .configs import DeptConfig
from . import data, figs
from ... import util, static_data


def show_settings(config: DeptConfig) -> dict:
    """
    Render the sidebar and return the dict with configuration options set by the user.
    """
    with st.sidebar:
        util.st_sidebar_prh_logo()

        if len(config.wd_ids) > 1:
            dept = st.selectbox(
                "Department",
                options=["All"] + config.wd_ids,
                format_func=lambda n: n if n == "All" else static_data.WDID_TO_DEPT_NAME.get(n) or f"Unknown Department {n}",
            )
        else:
            dept = config.wd_ids[0]

        month = st.selectbox(
            "Month",
            options=_prev_months(24),
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%b %Y"),
        )

    return {"dept": dept, "month": month}


def _prev_months(n_months):
    """
    Return the last n_months in a format like ["2022-12", "2022-11", ...]
    """
    ret = [datetime.now() - relativedelta(months=i+1) for i in range(n_months)]
    ret = [m.strftime("%Y-%m") for m in ret]
    return ret
