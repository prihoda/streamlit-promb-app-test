import pytest

from ovo import db
from ovo.core.database import Design
from ovo_promb.models import PrombDescriptorWorkflow
from ovo.core.logic import descriptor_logic
from ovo.core.utils.tests import TEST_SCHEDULER_KEY


def test_full(project_data):
    project, project_round, custom_pool = project_data

    designs = db.select(Design, pool_id=custom_pool.id)
    design_ids = [d.id for d in designs]

    workflow = PrombDescriptorWorkflow(chains=["A"], design_ids=design_ids)
    workflow.validate()
    descriptor_job = descriptor_logic.submit_descriptor_workflow(
        workflow=workflow, scheduler_key=TEST_SCHEDULER_KEY, round_id=project_round.id
    )
    descriptor_logic.process_results(descriptor_job)
    values = descriptor_logic.get_wide_descriptor_table(design_ids=design_ids)
    print(values.to_dict(orient="records"))
    first_row = values.iloc[0]
    assert first_row["Average non-human mutations"] == 0
    assert first_row["Nearest human peptide"].startswith('{"A1": "NTTVFQGVA", "A2": "TTVFQGVAG", "A3": "TVFQGVAGQ"')
