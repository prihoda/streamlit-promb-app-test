import shutil
import os
import streamlit as st
import subprocess

st.set_page_config(layout="wide", page_title="promb", page_icon="🔥")

TEST_HOME_DIR = "/tmp/ovo"
if not os.path.exists(TEST_HOME_DIR):
    with st.spinner("Initializing OVO..."):
        # Initialize OVO config.yml in test-results directory
        subprocess.run(["ovo", "init", "home", TEST_HOME_DIR, "-y", "--no-env"])
        assert os.path.exists(os.path.join(TEST_HOME_DIR, "config.yml")), "OVO init home failed"

os.environ["OVO_HOME"] = TEST_HOME_DIR

from ovo import db
from ovo.core.utils.tests import create_test_project_data
from ovo_promb.design_views import promb_fragment

# FIXME: from ovo.app.utils.page_init import initialize_session
# initialize_session()

# FIXME avoid recreating on page refresh
if "project" not in st.session_state:
    project, project_round, custom_pool = create_test_project_data()
    st.session_state.project = project
    st.session_state.pool = custom_pool

pool_ids = [st.session_state.pool.id]
design_ids = None

promb_fragment(pool_ids, design_ids=design_ids)
