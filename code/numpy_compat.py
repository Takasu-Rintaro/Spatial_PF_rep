"""Compatibility shims for StellarGraph 1.2.1 on NumPy 2.x."""

import numpy as np


class _Cast:
    def __getitem__(self, dtype):
        return lambda value: np.asarray(value).astype(dtype, casting="unsafe")


if not hasattr(np, "cast"):
    np.cast = _Cast()
if not hasattr(np, "product"):
    np.product = np.prod
