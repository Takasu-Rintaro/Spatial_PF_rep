# Spatial_PF_rep

## Run the Xenium workflow

The workflow reads every transcript CSV under `datasets/` directly. Install
the dependencies with `pip` in the repository virtual environment:

```bash
uv venv
uv pip install -r requirements.txt
```

Then run it from the repository root:

```bash
.venv/bin/snakemake --snakefile svi_run_build-full-g-xenium-unify-dmax.smk --cores 1
```

For a small GPU test run, select the smallest transcript dataset:

```bash
.venv/bin/snakemake \
  --snakefile svi_run_build-full-g-xenium-unify-dmax.smk \
  --config sample_limit=1 \
  --cores 1 \
  --resources gpus=1
```

The input files are discovered from their filename stems, so the GEO
filenames do not need to be renamed. Intermediate graph files are written
under `scratch_ln/`, and embeddings are written under `output/`.
