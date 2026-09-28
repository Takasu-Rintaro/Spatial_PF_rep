#!/bin/bash
#SBATCH --job-name=spatial-pf-45
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --mem=400G
#SBATCH --time=7-00:00:00

set -euo pipefail

cd /srv/takasu/arm_tensorflow/Spatial_PF_rep

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export TF_NUM_INTRAOP_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export TF_NUM_INTEROP_THREADS="${SLURM_CPUS_PER_TASK:-1}"

.venv/bin/snakemake \
  --snakefile svi_run_build-full-g-xenium-unify-dmax.smk \
  --config sample_limit=0 \
  --cores "${SLURM_CPUS_PER_TASK:-1}" \
  --resources gpus=1 \
  --rerun-incomplete \
  --printshellcmds \
  --latency-wait 60
