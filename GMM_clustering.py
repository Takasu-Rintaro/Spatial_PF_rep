import argparse
from pathlib import Path

import numpy as np
import torch


class GMM:
    """Gaussian mixture model trained with GPU-backed PyTorch EM."""

    def __init__(
        self,
        n_components=12,
        max_iter=200,
        tol=1e-4,
        reg_covar=1e-6,
        seed=42,
        batch_size=65536,
    ):
        self.n_components = n_components
        self.max_iter = max_iter
        self.tol = tol
        self.reg_covar = reg_covar
        self.seed = seed
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _batches(self, data):
        for start in range(0, data.shape[0], self.batch_size):
            end = min(start + self.batch_size, data.shape[0])
            yield torch.as_tensor(data[start:end], dtype=torch.float32, device=self.device)

    def _kmeans_plus_plus(self, x):
        generator = torch.Generator(device=self.device).manual_seed(self.seed)
        centers = [
            torch.randint(x.shape[0], (1,), generator=generator, device=self.device).item()
        ]
        distances = ((x - x[centers[0]]) ** 2).sum(dim=1)
        for _ in range(1, self.n_components):
            probabilities = distances / distances.sum().clamp_min(1e-12)
            index = torch.multinomial(probabilities, 1, generator=generator).item()
            centers.append(index)
            distances = torch.minimum(distances, ((x - x[index]) ** 2).sum(dim=1))
        return x[centers].clone()

    @torch.no_grad()
    def fit(self, data):
        if data.ndim == 1:
            data = data[:, None]
        if data.ndim != 2 or data.shape[0] < self.n_components:
            raise ValueError(
                f"入力は (サンプル数, 特徴量数) の配列で、"
                f"サンプル数は{self.n_components}以上必要です"
            )
        if not np.issubdtype(data.dtype, np.number):
            raise ValueError("入力データは数値配列である必要があります")

        n_samples, n_features = data.shape
        sample_size = min(n_samples, max(10000, self.n_components * 1000))
        sample_indices = np.linspace(0, n_samples - 1, sample_size, dtype=np.int64)
        sample = torch.as_tensor(data[sample_indices], dtype=torch.float32, device=self.device)
        if not torch.isfinite(sample).all():
            raise ValueError("入力データに NaN または無限大が含まれています")

        means = self._kmeans_plus_plus(sample)
        eye = torch.eye(n_features, device=self.device)
        sum_x = torch.zeros(n_features, device=self.device)
        sum_xx = torch.zeros((n_features, n_features), device=self.device)
        for batch in self._batches(data):
            sum_x += batch.sum(dim=0)
            sum_xx += batch.T @ batch
        covariance = (sum_xx - torch.outer(sum_x, sum_x) / n_samples) / max(n_samples - 1, 1)
        covariance = covariance + self.reg_covar * eye
        covariances = covariance.expand(self.n_components, -1, -1).clone()
        weights = torch.full(
            (self.n_components,), 1 / self.n_components, device=self.device
        )
        previous = None

        for _ in range(self.max_iter):
            distribution = torch.distributions.MultivariateNormal(
                means, covariance_matrix=covariances
            )
            counts = torch.zeros(self.n_components, device=self.device)
            weighted_x = torch.zeros((self.n_components, n_features), device=self.device)
            weighted_xx = torch.zeros(
                (self.n_components, n_features, n_features), device=self.device
            )
            likelihood_sum = torch.zeros((), device=self.device)
            for batch in self._batches(data):
                log_prob = distribution.log_prob(batch[:, None, :]) + weights.log()
                likelihood_sum += torch.logsumexp(log_prob, dim=1).sum()
                responsibilities = log_prob.softmax(dim=1)
                counts += responsibilities.sum(dim=0)
                weighted_x += responsibilities.T @ batch
                weighted_xx += torch.einsum("nk,ni,nj->kij", responsibilities, batch, batch)

            likelihood = likelihood_sum / n_samples
            counts = counts.clamp_min(1e-8)
            weights = counts / n_samples
            means = weighted_x / counts[:, None]
            covariances = (
                weighted_xx / counts[:, None, None]
                - torch.einsum("ki,kj->kij", means, means)
                + self.reg_covar * eye
            )
            if previous is not None and (likelihood - previous).abs() < self.tol:
                break
            previous = likelihood

        self.means_, self.covariances_, self.weights_ = means, covariances, weights
        self.labels_ = self.predict(data).cpu().numpy()
        return self

    @torch.no_grad()
    def predict(self, data):
        if data.ndim == 1:
            data = data[:, None]
        distribution = torch.distributions.MultivariateNormal(
            self.means_, covariance_matrix=self.covariances_
        )
        labels = []
        for batch in self._batches(data):
            labels.append(
                (distribution.log_prob(batch[:, None, :]) + self.weights_.log())
                .argmax(dim=1)
                .cpu()
            )
        return torch.cat(labels)


def _input_files(input_path):
    if input_path.is_dir():
        files = sorted(input_path.glob("*.npy"))
        if not files:
            raise FileNotFoundError(f"{input_path} に .npy ファイルがありません")
        return files
    if input_path.suffix != ".npy":
        raise ValueError("入力は .npy ファイルまたは .npy ファイルを含むディレクトリにしてください")
    return [input_path]


def main():
    parser = argparse.ArgumentParser(description="12-cluster GPU GMM for .npy input")
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("clustering_datasets"),
        help="入力 .npy またはディレクトリ（既定: clustering_datasets）",
    )
    parser.add_argument("-o", "--output", type=Path, help="単一入力時の出力 .npy")
    parser.add_argument("--batch-size", type=int, default=65536)
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size は1以上で指定してください")

    files = _input_files(args.input)
    if args.output and len(files) > 1 and args.output.suffix == ".npy":
        parser.error("複数入力では --output に出力ディレクトリを指定してください")
    if args.output and len(files) > 1:
        args.output.mkdir(parents=True, exist_ok=True)

    for input_file in files:
        data = np.load(input_file, mmap_mode="r")
        model = GMM(n_components=12, batch_size=args.batch_size).fit(data)
        if args.output is None:
            output = input_file.with_name(input_file.stem + "_labels.npy")
        elif len(files) == 1:
            output = args.output
        else:
            output = args.output / f"{input_file.stem}_labels.npy"
        np.save(output, model.labels_)
        print(f"device={model.device}, input={input_file}, output={output}")


if __name__ == "__main__":
    main()
