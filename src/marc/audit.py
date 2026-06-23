from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd


KEYS = ["source_key", "target_key", "lag"]


def canonicalize(edges: pd.DataFrame) -> pd.DataFrame:
    out = edges.copy()
    zero = out["lag"].eq(0)
    out["source_key"] = out["source"]
    out["target_key"] = out["target"]
    out.loc[zero, "source_key"] = [
        min(a, b) for a, b in zip(out.loc[zero, "source"], out.loc[zero, "target"])
    ]
    out.loc[zero, "target_key"] = [
        max(a, b) for a, b in zip(out.loc[zero, "source"], out.loc[zero, "target"])
    ]
    dedup = ["unit", "algorithm", "tau_max", "repeat", *KEYS]
    return out.sort_values(dedup).drop_duplicates(dedup).reset_index(drop=True)


def run_grid(units: dict, engines: list, audit: dict, output: Path) -> pd.DataFrame:
    tau_windows = [int(value) for value in audit["lag_windows"]]
    repeats = int(audit.get("run_repeats", 1))
    cache_dir = output / "runs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames = []

    for unit, engine, tau_max, repeat in itertools.product(
        units, engines, tau_windows, range(repeats)
    ):
        cache = cache_dir / f"{unit}__{engine.name}__tau{tau_max}__run{repeat}.csv"
        if cache.exists() and not audit.get("overwrite", False):
            frame = pd.read_csv(cache)
        else:
            frame = engine.run(units[unit], tau_max, repeat, unit)
            frame.to_csv(cache, index=False)
        frames.append(frame)
    return canonicalize(pd.concat(frames, ignore_index=True))


def _present(frame: pd.DataFrame, q_cutoff: float, effect_cutoff: float) -> pd.Series:
    significant = frame["q_value"].isna() | frame["q_value"].lt(q_cutoff)
    return significant & frame["abs_effect"].ge(effect_cutoff)


def summarize(edges: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    audit = config["audit"]
    algorithms = [item["name"] for item in config["algorithms"]]
    lag_windows = [int(value) for value in audit["lag_windows"]]
    cutoffs = [float(value) for value in audit["effect_cutoffs"]]
    baseline_algorithm = audit.get("baseline_algorithm", algorithms[0])
    baseline_tau = int(audit.get("baseline_lag_window", lag_windows[0]))
    q_cutoff = float(audit.get("q_cutoff", 0.01))
    adopted = float(audit.get("adopted_effect_cutoff", cutoffs[0]))
    units = sorted(edges["unit"].unique())
    repeats = sorted(edges["repeat"].unique())
    all_keys = edges[KEYS].drop_duplicates()
    rows = []

    for key in all_keys.itertuples(index=False):
        subset = edges[
            edges["source_key"].eq(key.source_key)
            & edges["target_key"].eq(key.target_key)
            & edges["lag"].eq(key.lag)
        ]
        baseline = subset[
            subset["algorithm"].eq(baseline_algorithm)
            & subset["tau_max"].eq(baseline_tau)
            & subset["repeat"].eq(repeats[0])
        ]
        spatial = baseline.loc[_present(baseline, q_cutoff, adopted), "unit"].nunique() / len(units)

        lag_pass = []
        for tau in lag_windows:
            part = subset[
                subset["algorithm"].eq(baseline_algorithm)
                & subset["tau_max"].eq(tau)
                & subset["repeat"].eq(repeats[0])
            ]
            lag_pass.append(_present(part, q_cutoff, adopted).any())

        algorithm_pass = []
        algorithm_signs = []
        for algorithm in algorithms:
            part = subset[
                subset["algorithm"].eq(algorithm)
                & subset["tau_max"].eq(baseline_tau)
                & subset["repeat"].eq(repeats[0])
            ]
            detected = part[_present(part, q_cutoff, adopted)]
            algorithm_pass.append(not detected.empty)
            if not detected.empty:
                algorithm_signs.append(int(np.sign(detected["effect"].median())))

        cutoff_rates = {}
        for cutoff in cutoffs:
            detected = baseline[_present(baseline, q_cutoff, cutoff)]
            cutoff_rates[f"cutoff_{cutoff:g}"] = detected["unit"].nunique() / len(units)

        repeat_pass = []
        for repeat in repeats:
            part = subset[
                subset["algorithm"].eq(baseline_algorithm)
                & subset["tau_max"].eq(baseline_tau)
                & subset["repeat"].eq(repeat)
            ]
            repeat_pass.append(_present(part, q_cutoff, adopted).any())

        axis = {
            "axis1_spatial": spatial,
            "axis2_lag_window": float(np.mean(lag_pass)),
            "axis3_algorithm": float(np.mean(algorithm_pass)),
            "axis3_sign_consistent": len(set(algorithm_signs)) <= 1,
            "axis4_cutoff": min(cutoff_rates.values()),
            "axis5_run": float(np.mean(repeat_pass)),
        }
        thresholds = audit.get("pass_thresholds", {})
        robust = (
            axis["axis1_spatial"] >= float(thresholds.get("axis1", 0.8))
            and axis["axis2_lag_window"] >= float(thresholds.get("axis2", 1.0))
            and axis["axis3_algorithm"] >= float(thresholds.get("axis3", 1.0))
            and axis["axis3_sign_consistent"]
            and axis["axis4_cutoff"] >= float(thresholds.get("axis4", 0.8))
            and axis["axis5_run"] >= float(thresholds.get("axis5", 1.0))
        )
        rows.append({
            **dict(zip(KEYS, key)),
            **axis,
            **cutoff_rates,
            "median_effect": float(baseline["effect"].median()) if not baseline.empty else np.nan,
            "classification": "robust_core" if robust else "design_artifact",
        })

    summary = pd.DataFrame(rows)
    anchors = evaluate_anchors(summary, config.get("positive_controls", []))
    return summary, anchors


def evaluate_anchors(summary: pd.DataFrame, controls: list[dict]) -> pd.DataFrame:
    rows = []
    for control in controls:
        source, target = control["source"], control["target"]
        lag = int(control.get("lag", 0))
        if lag == 0:
            source, target = sorted((source, target))
        match = summary[
            summary["source_key"].eq(source)
            & summary["target_key"].eq(target)
            & summary["lag"].eq(lag)
        ]
        expected_sign = control.get("sign", "any")
        sign_ok = True
        if not match.empty and expected_sign != "any":
            wanted = 1 if expected_sign == "positive" else -1
            sign_ok = int(np.sign(match.iloc[0]["median_effect"])) == wanted
        rows.append({
            "name": control.get("name", f"{source}->{target}@{lag}"),
            "source": source,
            "target": target,
            "lag": lag,
            "recovered": not match.empty,
            "classification": match.iloc[0]["classification"] if not match.empty else "missing",
            "sign_ok": bool(sign_ok),
        })
    return pd.DataFrame(rows)
