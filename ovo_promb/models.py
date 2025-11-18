from dataclasses import dataclass, field
from typing import Callable

from ovo import DescriptorWorkflow, WorkflowTypes, Design, DescriptorJob, WorkflowParams
from ovo.core.scheduler import Scheduler


@dataclass
class PrombParams(WorkflowParams):
    db: str = "human-reference"
    peptide_length: int = 9


@WorkflowTypes.register('Promb humanness evaluation')
@dataclass
class PrombDescriptorWorkflow(DescriptorWorkflow):

    promb_params: PrombParams = field(
        default_factory=PrombParams,
        metadata=dict(tool_name="Promb")
    )

    def get_pipeline_name(self) -> str:
        return "ovo_promb.promb"

    def prepare_params(self, workdir: str) -> dict:
        from ovo import db, storage
        # Collect pdb paths and ids in the same order (db.select does not guarantee same order)
        storage_paths = []
        design_ids = []
        for design in db.select(Design, id__in=self.design_ids):
            if not design.structure_path:
                continue
            storage_paths.append(design.structure_path)
            design_ids.append(design.id)
        # Prepare a txt file with workflow input paths, each file renamed to design_id.pdb
        input_path = storage.prepare_workflow_inputs(storage_paths, workdir, names=design_ids)
        # Submit job
        return {
            "input_pdb": input_path,
            "chains": ",".join(self.chains),
            "db": self.promb_params.db,
            "peptide_length": self.promb_params.peptide_length,
        }

    def process_results(self, job: "DescriptorJob", callback: Callable = None):
        """Process results of a successful workflow - download files from workdir, save DesignJob, Pool and Designs"""
        from ovo import db
        from ovo.core.logic.descriptor_logic import read_descriptor_file_values

        descriptor_values = read_descriptor_file_values(
            descriptor_job=job,
            # descriptor key prefix (pipeline|tool_key) -> filename to parse
            filenames={"promb|promb": "promb"},
            # mapping from design.id to ID column in produced file
            design_id_mapping={design_id: design_id + ".pdb" for design_id in self.design_ids},
        )
        db.save_all(descriptor_values + [job])
