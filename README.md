# Spatial_PF_rep

## Run the Xenium workflow

The workflow reads every transcript CSV under `datasets/` directly. Run it
from the repository root:

```bash
snakemake --snakefile svi_run_build-full-g-xenium-unify-dmax.smk --cores 1
```

The input files are discovered from their filename stems, so the GEO
filenames do not need to be renamed. Intermediate graph files are written
under `scratch_ln/`, and embeddings are written under `output/`.
