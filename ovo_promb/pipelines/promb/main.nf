nextflow.enable.dsl = 2

workflow {
    // Check required arguments
    [
        'input_pdb',
        'chains',
        'db',
        'peptide_length',
    ].each { param ->
        params[param] = null
        if (!params[param]) {
            throw new IllegalArgumentException("Argument --${param} is required!")
        }
    }

    // Reusable logic to create PDB folder batches
    def fileList = getFileList()
    createInputFolders(fileList)
    indexes = Channel.of(1..(1000000.intdiv(params.batch_size)))
    batches = createInputFolders.out.pdb_dir.merge(indexes, { pdb_dir, idx -> ["contig1_batch${idx}", pdb_dir] })

    // Run process with provided params
    runPromb(
        batches,
        chains=params.chains.split(','),
        db=params.db,
        peptide_length=params.peptide_length,
    )
}

process runPromb {
  // docker container name
  def containerName = "promb"
  conda { params.getSharedEnv("ovo_promb.${containerName}", workflow.profile) }
  container "${ (workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container)
    ? params.ovo_container_dir + '/ovo-' + containerName
    : params.docker_repository + 'ovo-' + containerName }"
  // label enables customizing configuration for specific jobs using nextflow config files
  label "promb"
  // default compute resources
  cpus 1
  memory { params.max_memory ?: "8 GB"}
  // GPU
  // accelerator 1, type: "nvidia-tesla-t4"

  publishDir { params.publish_dir }
  input:
    tuple val(batch_dir), path(pdb_dir)
    val chains
    val db
    val peptide_length
  output:
    path "${batch_dir}/*", emit: output_csv
  script:
  """
  set -euxo pipefail

  mkdir "${batch_dir}"

  promb nearest ${pdb_dir} \
    --chain ${chains.join(",")} \
    -l ${peptide_length} \
    -d ${db} \
    -o "${batch_dir}"/nearest.csv

  python <<EOF
import pandas as pd
import json
peptides = pd.read_csv("${batch_dir}/nearest.csv")
mutations = peptides.groupby("File")["Mutations"].mean()
nearest_peptide = peptides.groupby("File").apply(lambda rows: json.dumps({
  str(row.ID) + str(row.Position): row.Nearest for i, row in rows.iterrows()
}))
result = pd.DataFrame({
    "mutations": mutations,
    "nearest_peptide": nearest_peptide,
})
result.index.name = "id"
result.to_csv("${batch_dir}/promb.csv")
EOF
  """
}

def getFileList() {
    def pdbPaths
    if (params.input_pdb.endsWith('.txt')) {
        pdbPaths = Channel.fromList(file(params.input_pdb).readLines())
    } else if (params.input_pdb.endsWith('.pdb')) {
        pdbPaths = Channel.fromPath(params.input_pdb)
    } else if (params.input_pdb.endsWith('/')) {
        pdbPaths = Channel.fromPath(params.input_pdb + '*.pdb')
    } else {
        throw new IllegalArgumentException("Input file must be a .pdb file, a .txt file with a list of .pdb files, or a directory ending with /, got: ${params.input_pdb}")
    }
    return pdbPaths.collate(params.batch_size)
}

process createInputFolders {
    executor 'local'
    input:
        path inputs
    output:
        path pdb_dir, emit: pdb_dir
    script:
    """
        mkdir pdb_dir
        cp ${inputs} pdb_dir
    """
}
