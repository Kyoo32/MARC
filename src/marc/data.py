from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import resolve_path


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def load_units(config: dict) -> tuple[dict[str, pd.DataFrame], list[str]]:
    spec = config["input"]
    path = resolve_path(config, spec["path"])
    frame = _read_table(path)
    time_col = spec["time_column"]
    unit_col = spec.get("unit_column")
    variables = spec.get("variables") or [
        column for column in frame.columns if column not in {time_col, unit_col}
    ]
    missing = [column for column in [time_col, *variables] if column not in frame]
    if missing:
        raise ValueError(f"Input is missing columns: {missing}")

    frame[time_col] = pd.to_datetime(frame[time_col], errors="raise")
    if unit_col is None:
        frame["_marc_unit"] = "unit_1"
        unit_col = "_marc_unit"
    elif unit_col not in frame:
        raise ValueError(f"Input is missing unit column: {unit_col}")

    units = {}
    for unit, group in frame.groupby(unit_col, sort=True):
        values = (
            group.sort_values(time_col)
            .drop_duplicates(time_col, keep="last")
            .set_index(time_col)[variables]
            .apply(pd.to_numeric, errors="coerce")
        )
        method = spec.get("missing", "interpolate")
        if method == "interpolate":
            values = values.interpolate(method="time", limit_direction="both").ffill().bfill()
        elif method == "drop":
            values = values.dropna()
        elif method != "error":
            raise ValueError(f"Unknown missing-data policy: {method}")
        if values.isna().any().any():
            raise ValueError(f"Unit {unit} still contains missing values.")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"Unit {unit} contains non-finite values.")
        if len(values) < int(spec.get("minimum_rows", 50)):
            raise ValueError(f"Unit {unit} has too few rows: {len(values)}")
        units[str(unit)] = values
    return units, variables
