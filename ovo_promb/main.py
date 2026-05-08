import shutil
import os
import streamlit as st
import subprocess

st.set_page_config(layout="wide", page_title="promb", page_icon="🔥")

is_streamlit_cloud = os.environ.get("HOSTNAME") == "streamlit"

TEST_HOME_DIR = "/tmp/ovo"
if not os.path.exists(TEST_HOME_DIR):
    with st.spinner("Initializing OVO..."):
        # Initialize OVO config.yml in test-results directory
        subprocess.run(["ovo", "init", "home", TEST_HOME_DIR, "-y", "--no-env"])
        assert os.path.exists(os.path.join(TEST_HOME_DIR, "config.yml")), "OVO init home failed"

        if is_streamlit_cloud:
            subprocess.run(["curl", "-L", "-o", "/tmp/openjdk.tar.gz",
                            "https://download.java.net/java/GA/jdk21/fd2272bbf8e04c3dbaee13770090416c/35/GPL/openjdk-21_linux-x64_bin.tar.gz"])
            subprocess.run(["tar", "-xzf", "-C", "/tmp", "/tmp/openjdk.tar.gz"])

if is_streamlit_cloud:
    os.environ["PATH"] = "/tmp/jdk-21:" + os.environ["PATH"]

os.environ["OVO_HOME"] = TEST_HOME_DIR

# st.subheader("Run shell command")
# with st.form(key="run_command", border=False):
#     shell_command = st.text_area("Enter command:", placeholder="ls -la", key="shell_command", height=80)
#     if st.form_submit_button("Run"):
#         with st.spinner("Running command..."):
#             result = subprocess.run(
#                 shell_command,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.STDOUT,
#                 text=True,
#                 shell=True,
#             )
#         st.write("Finished with output:" if result.returncode == 0 else "Finished with error:")
#         st.code(result.stdout)

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
