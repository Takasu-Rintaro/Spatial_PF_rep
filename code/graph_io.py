"""Pickle graph I/O compatible with NetworkX 2.x and 3.x."""

import pickle
from typing import Any


def read_gpickle(path: str) -> Any:
    with open(path, "rb") as handle:
        return pickle.load(handle)


def write_gpickle(graph: Any, path: str) -> None:
    with open(path, "wb") as handle:
        pickle.dump(graph, handle, protocol=pickle.HIGHEST_PROTOCOL)
