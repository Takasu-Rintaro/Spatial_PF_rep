#!/bin/bash
#SBATCH --job-name=spatial-pf-45
#SBATCH --nodelist=aimslab05
#SBATCH --chdir=/shared/users/takasu/arm_tensorflow/Spatial_PF_rep
#SBATCH --output=/shared/users/takasu/slurm-spatial-pf-45-%j.out
#SBATCH --error=/shared/users/takasu/slurm-spatial-pf-45-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --mem=100G
#SBATCH --time=7-00:00:00

set -euo pipefail

cd /shared/users/takasu/arm_tensorflow/Spatial_PF_rep

export HOME=/shared/users/takasu
export XDG_CACHE_HOME="${HOME}/.cache"
mkdir -p "${XDG_CACHE_HOME}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export TF_NUM_INTRAOP_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export TF_NUM_INTEROP_THREADS="${SLURM_CPUS_PER_TASK:-1}"

# Reinstall dependencies on the allocated node: the login host and ARM GPU
# node have different architectures, so shared binary wheels are not safe.
.venv/bin/python -m pip install --force-reinstall --no-cache-dir \
  "numpy>=2,<2.8" \
  "scipy>=1.11,<2" \
  "pandas>=2.0,<4" \
  "matplotlib>=3.7,<4" \
  "tqdm>=4.65,<5" \
  "scikit-learn>=1.3,<2" \
  "networkx>=3.0,<4" \
  "tensorflow[and-cuda]>=2.16,<2.22" \
  "tensorrt>=10,<12" \
  "chardet>=5.0,<6" \
  "snakemake>=9,<10"

.venv/bin/python -m snakemake \
  --snakefile svi_run_build-full-g-xenium-unify-dmax.smk \
  --config sample_limit=1 max_dataset_bytes=1000000000 \
  --cores "${SLURM_CPUS_PER_TASK:-1}" \
  --resources gpus=1 \
  --rerun-incomplete \
  --printshellcmds \
  --latency-wait 60
