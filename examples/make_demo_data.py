from pathlib import Path

import numpy as np
import pandas as pd


rng = np.random.default_rng(20260622)
rows = []
for unit_index, unit in enumerate(["A", "B", "C"]):
    n = 240
    x = np.zeros(n)
    y = np.zeros(n)
    z = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.55 * x[t - 1] + rng.normal(scale=0.8)
        y[t] = 0.65 * x[t - 1] + 0.20 * y[t - 1] + rng.normal(scale=0.8)
        z[t] = 0.35 * z[t - 1] + rng.normal(scale=0.9)
    time = pd.date_range("2025-01-01", periods=n, freq="h")
    rows.append(pd.DataFrame({"time": time, "unit": unit, "X": x, "Y": y, "Z": z}))

path = Path(__file__).with_name("demo_timeseries.csv")
pd.concat(rows, ignore_index=True).to_csv(path, index=False)
print(path)
