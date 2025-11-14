#!/bin/bash

set -ex

# change to script dir
cd "$(dirname "$0")"

WORKFLOW_ROOT=$(realpath "../../")
OVO_MODULE_PATH=$(ovo module)
REFERENCE_FILES_DIR=$(python -c "from ovo import config; print(config.reference_files_dir)")
INPUT_DIR=$(pwd)/test-input
OUTPUT_DIR=$(pwd)/test-results

# change to work dir
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"
# clear previous results
rm -rf contig1_batch1

# PDB file
nextflow run ../../main.nf \
  -process.containerOptions="-v $WORKFLOW_ROOT:$WORKFLOW_ROOT -v \"$REFERENCE_FILES_DIR:$REFERENCE_FILES_DIR\"" \
  --ovo_path "$OVO_MODULE_PATH" \
  --reference_files_dir "$REFERENCE_FILES_DIR" \
  --publish_dir $OUTPUT_DIR \
  --chains A \
  --input_pdb "$INPUT_DIR/" \
  --peptide_length 9 \
  --db human-reference \
  $@

ls -lR contig1_batch1/*

