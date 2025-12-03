from io import StringIO
from typing import Optional

from ovo import db, schedulers, Pool, Design, DescriptorValue, DescriptorJob
from ovo.app.components.descriptor_job_components import refresh_descriptors
from ovo.app.utils.cached_db import get_cached_descriptor_values, get_cached_pools, get_cached_design_ids
from ovo.core.logic.descriptor_logic import submit_descriptor_workflow
import streamlit as st

from ovo_promb.descriptors_promb import PROMB_AVERAGE_MUTATIONS, PROMB_NEAREST1_PEPTIDE
from ovo_promb.formatting import chop_seq_peptides, print_nearest
from ovo_promb.models import PrombDescriptorWorkflow, PrombParams
from plotly import express as px


@st.fragment
def promb_fragment(pool_ids: list[str], design_ids: Optional[list[str]] = None):

    if design_ids is None:
        # design_ids not explicitly passed, use all accepted designs in the selected pools
        design_ids = get_cached_design_ids(pool_ids=pool_ids, accepted=True)
        if not design_ids:
            st.write("No accepted designs in the selected " + ("pools" if len(pool_ids) > 1 else "pool") +
                     ". Please mark some designs as accepted in the **Jobs** page.")
            return
    elif not design_ids:
        # Empty list explicitly passed to design_ids
        st.write("No designs selected")
        return

    st.header(f"🧍 Promb Humanness | {len(design_ids):,} {'design' if len(design_ids) == 1 else 'designs'}")

    if st.button(
            "Submit Promb",
                 type='primary',
                 key='submit_btn',
                 help='Submit workflow for all designs',):
        promb_submit_dialog(design_ids=design_ids)

    refresh_descriptors(
        design_ids=design_ids,
        workflow_names=[PrombDescriptorWorkflow.name]
    )

    descriptor = PROMB_AVERAGE_MUTATIONS

    average_mutation_values = get_cached_descriptor_values(descriptor.key, design_ids=design_ids)
    design_ids = average_mutation_values.dropna().index.tolist()

    if not design_ids:
        st.write("No results yet")
        return

    st.info("""
    Note: More human doesn't always mean "good". Peptides like "GGGGGGGGG" or "EKEKEKEKE" are human 
    but you don't necessarily want your protein to contain those. Make sure to check for sequence entropy, 
    AlphaFold2 confidence, or other quality metrics.
    """)

    st.subheader("Results")

    with st.columns(2)[0]:
        fig = px.histogram(
            x=average_mutation_values,
            labels={'x': descriptor.name, "y": "Number of designs"},
            nbins=20,
            height=300,
        )
        st.plotly_chart(fig)

    st.subheader("Table")

    st.dataframe(
        average_mutation_values.sort_values().rename(descriptor.name),
        width="content",
    )

    st.write("Values can be visualized and exported in the Explorer view.")

    design_visualization_fragment(design_ids)


@st.fragment
def design_visualization_fragment(design_ids: list[str]):
    st.header("Designs")

    key = 'selected_design'
    idx = design_ids.index(st.query_params[key]) if key in st.query_params and st.query_params[key] in design_ids else 0
    design_id = st.selectbox(
        'Select a design',
        options=design_ids,
        # format_func=lambda design: f'{design.id}',
        label_visibility='collapsed',
        key=key,
        index=idx,
    )
    st.query_params[key] = design_id

    st.subheader(design_id)

    design = db.get(Design, design_id)

    sequence_fasta = '\n'.join(f'>{chain.type}|{",".join(chain.chain_ids)}\n{chain.sequence}' for chain in design.spec.chains)
    st.code(sequence_fasta)

    # TODO handle displaying by different job settings
    average_mutations = float(db.select(
        DescriptorValue,
        design_id=design_id,
        descriptor_key=PROMB_AVERAGE_MUTATIONS.key,
        limit=1,
    )[0].value)
    st.metric(
        label="Average Non-human Mutations",
        value=f"{average_mutations:.3f}",
    )

    nearest_peptides_value = db.select(
        DescriptorValue,
        design_id=design_id,
        descriptor_key=PROMB_NEAREST1_PEPTIDE.key,
        limit=1,
    )[0]
    descriptor_job = db.get(DescriptorJob, id=nearest_peptides_value.descriptor_job_id)
    peptide_length = descriptor_job.workflow.promb_params.peptide_length
    chains = descriptor_job.workflow.chains
    assert len(chains) == 1, "Visualization of multiple chains is not implemented yet"
    chain = chains[0]
    seq = design.spec.get_chain(chain).sequence
    seq_peptides = chop_seq_peptides(seq, peptide_length)
    nearest_peptides_dict = PROMB_NEAREST1_PEPTIDE.deserialize(nearest_peptides_value.value)
    nearest_peptides = [nearest_peptides_dict[f"{chain}{pos}"] for pos in range(1, len(seq_peptides) + 1)]
    st.markdown("##### Nearest human peptides")
    stream = StringIO()
    print_nearest(seq_peptides, [[p] for p in nearest_peptides], file=stream)
    with st.container(height=400):
        st.code(stream.getvalue())


@st.fragment
@st.dialog("Promb submission", width="large")
def promb_submit_dialog(design_ids: list[str]):
    content = st.empty()
    with content.container():
        chains = st.text_input(
            "Chain(s) to analyze",
            value="A",
            key="proteinqc_chains_input",
        )
        chains = chains.replace(" ", "").replace(",", "")

        db = st.selectbox("Database", options=["human-reference", "human-swissprot", "human-oas"], index=0)
        peptide_length = st.number_input("Peptide length", min_value=3, max_value=20, step=1, value=9)

        scheduler_key = st.selectbox(
            "Scheduler",
            options=list(schedulers.keys()),
            format_func=lambda x: schedulers[x].name,
            key="proteinqc_scheduler_selectbox",
        )
        with st.columns(2)[-1]:
            submit = st.button(
                "Submit",
                key="confirm_btn",
                type="primary",
                width="stretch",
            )

    if submit:
        content.empty()
        st.write(f"Submitting job... 🚀")
        workflow = PrombDescriptorWorkflow(
            chains=list(chains),
            design_ids=design_ids,
            promb_params=PrombParams(
                db=db,
                peptide_length=peptide_length,
            ),
        )
        submit_descriptor_workflow(workflow, scheduler_key, st.session_state.project.id)
        st.rerun()

