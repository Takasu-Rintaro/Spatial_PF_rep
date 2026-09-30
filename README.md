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

## Run all 45 samples with Slurm

The current workflow combines all samples during the merge step, so submit it
as one job rather than as 45 independent array jobs. Review the partition,
account, memory, and time settings in
[`run_snakemake_45.sbatch`](run_snakemake_45.sbatch) for your cluster, then
submit:

```bash
sbatch run_snakemake_45.sbatch
```

`sample_limit=0` means that every CSV under `datasets/` is processed. Monitor
the job with:

```bash
squeue --job <JOB_ID>
tail -f slurm-spatial-pf-45-<JOB_ID>.out
```

For the 128 GB node configuration, `run_snakemake_45.sbatch` currently uses
`max_dataset_bytes=1000000000`, excluding CSV files larger than 1 GB to avoid
out-of-memory failures during graph construction.
