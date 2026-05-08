import os
import streamlit as st
import subprocess
import shutil

st.set_page_config(layout="wide", page_title="promb", page_icon="🔥")

is_streamlit_cloud = os.environ.get("HOSTNAME") == "streamlit"

# TODO create function for this in ovo
if is_streamlit_cloud:
    TEMP_HOME_DIR = "/tmp/ovo"
    if not os.path.exists(TEMP_HOME_DIR):
        with st.spinner("Initializing OVO..."):
            # Initialize OVO home dir
            subprocess.run(["ovo", "init", "home", TEMP_HOME_DIR, "-y", "--no-env"])
            assert os.path.exists(os.path.join(TEMP_HOME_DIR, "config.yml")), "OVO init home failed"
            # TODO send max memory through ovo init command
            subprocess.run(["sed", "-i", "s/max_memory: 8GB/max_memory: 3GB/", f"{TEMP_HOME_DIR}/config.yml"])
    os.environ["OVO_HOME"] = TEMP_HOME_DIR

# TODO put this directly to init_nextflow?
if is_streamlit_cloud:
    TEMP_JDK_DIR = "/tmp/jdk"
    TEMP_CONDA_DIR = "/tmp/conda"
    os.environ["PATH"] = os.path.join(TEMP_CONDA_DIR, "bin") + ":" + os.environ["PATH"]
    if not shutil.which("conda"):
        with st.spinner("Installing dependencies..."):
            # Install conda
            subprocess.run(["curl", "-L", "-o", "/tmp/miniforge.sh", "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"])
            subprocess.run(["bash", "/tmp/miniforge.sh", "-b", "-p", TEMP_CONDA_DIR])
            subprocess.run(["conda", "install", "-c", "conda-forge", "-y", "procps-ng", "openjdk"])


st.subheader("Run shell command")
with st.form(key="run_command", border=False):
    shell_command = st.text_area("Enter command:", placeholder="ls -la", key="shell_command", height=80)
    if st.form_submit_button("Run"):
        with st.spinner("Running command..."):
            result = subprocess.run(
                shell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
            )
        st.write("Finished with output:" if result.returncode == 0 else "Finished with error:")
        st.code(result.stdout)

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
