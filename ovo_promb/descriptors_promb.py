from ovo.core.database import NumericGlobalDescriptor, StringResidueDescriptor, Descriptor

PROMB_AVERAGE_MUTATIONS = NumericGlobalDescriptor(
    name='Average non-human mutations',
    description='Average number of non-human mutations per peptide. '
                'Computed by finding the nearest k-mer peptide in the human reference proteome for each overlapping peptide. ',
    tool='Promb',
    key='promb|promb|mutations',
    min_value=0,
    comparison='lower_is_better'
)

PROMB_NEAREST1_PEPTIDE = StringResidueDescriptor(
    name='Nearest human peptide',
    description='Nearest human peptide at each position. '
                'Computed by finding the nearest k-mer peptide in the human reference proteome for each overlapping peptide. ',
    tool='Promb',
    key='promb|promb|nearest_peptide',
)

DESCRIPTORS = [v for v in globals().values() if isinstance(v, Descriptor)]

PRESETS = [
    # {
    #     "label": "Example preset",
    #     "x": X_DESCRIPTOR,
    #     "y": Y_DESCRIPTOR,
    # },
]
