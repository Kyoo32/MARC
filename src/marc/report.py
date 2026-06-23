from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _save(fig, output: Path, stem: str) -> None:
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(output / f"{stem}.{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.12g")


def make_figures(edges: pd.DataFrame, summary: pd.DataFrame, config: dict, output: Path) -> None:
    audit = config["audit"]
    baseline = audit.get("baseline_algorithm", config["algorithms"][0]["name"])
    baseline_tau = int(audit.get("baseline_lag_window", audit["lag_windows"][0]))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    axis_cols = [f"axis{i}_{name}" for i, name in [
        (1, "spatial"), (2, "lag_window"), (3, "algorithm"), (4, "cutoff"), (5, "run")
    ]]
    top = summary.sort_values(axis_cols, ascending=False).head(25)
    matrix = top[axis_cols].to_numpy()
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(5), ["unit", "lag", "algorithm", "cutoff", "run"])
    ax.set_yticks(
        range(len(top)),
        [f"{r.source_key}->{r.target_key} @ {r.lag}" for r in top.itertuples()],
        fontsize=7,
    )
    ax.set_title("MARC five-axis survival profile")
    fig.colorbar(image, ax=ax, label="survival / recurrence")
    _save(fig, output, "figure1_five_axis_profile")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    base_edges = edges[
        edges["algorithm"].eq(baseline)
        & edges["tau_max"].eq(baseline_tau)
        & edges["repeat"].eq(edges["repeat"].min())
    ]
    lags = sorted(base_edges["lag"].unique())
    ax.boxplot(
        [base_edges.loc[base_edges["lag"].eq(lag), "abs_effect"] for lag in lags],
        positions=lags,
    )
    ax.set(xlabel="lag", ylabel="|effect|", title="Effect-size distribution by lag")
    _save(fig, output, "figure2_effect_by_lag")

    cutoff_cols = [column for column in summary if column.startswith("cutoff_")]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    selected = summary.sort_values(cutoff_cols[0], ascending=False).head(25)
    image = ax.imshow(selected[cutoff_cols], vmin=0, vmax=1, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(cutoff_cols)), [column.replace("cutoff_", "") for column in cutoff_cols])
    ax.set_yticks(
        range(len(selected)),
        [f"{r.source_key}->{r.target_key} @ {r.lag}" for r in selected.itertuples()],
        fontsize=7,
    )
    ax.set(xlabel="effect-size cutoff", title="Unit recurrence across cutoffs")
    fig.colorbar(image, ax=ax, label="unit recurrence")
    _save(fig, output, "figure3_cutoff_sensitivity")

    algorithms = [item["name"] for item in config["algorithms"]]
    if len(algorithms) >= 2:
        first, second = algorithms[:2]
        keys = ["unit", "source_key", "target_key", "lag"]
        a = edges[
            edges["algorithm"].eq(first)
            & edges["tau_max"].eq(baseline_tau)
            & edges["repeat"].eq(edges["repeat"].min())
        ][keys + ["effect"]].rename(columns={"effect": first})
        b = edges[
            edges["algorithm"].eq(second)
            & edges["tau_max"].eq(baseline_tau)
            & edges["repeat"].eq(edges["repeat"].min())
        ][keys + ["effect"]].rename(columns={"effect": second})
        compare = a.merge(b, on=keys, how="outer").fillna(0)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(compare[first], compare[second], alpha=0.65, s=25)
        limit = max(0.1, float(compare[[first, second]].abs().max().max()))
        ax.plot([-limit, limit], [-limit, limit], "--", color="#888888")
        ax.axhline(0, color="#bbbbbb", lw=0.7)
        ax.axvline(0, color="#bbbbbb", lw=0.7)
        ax.set(
            xlim=(-limit, limit), ylim=(-limit, limit),
            xlabel=f"{first} effect", ylabel=f"{second} effect",
            title="Algorithm agreement",
        )
        _save(fig, output, "figure4_algorithm_agreement")


def write_outputs(
    edges: pd.DataFrame,
    summary: pd.DataFrame,
    anchors: pd.DataFrame,
    config: dict,
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    ordered_summary = summary.sort_values(
        ["classification", "source_key", "target_key", "lag"]
    ).reset_index(drop=True)
    _write_csv(edges, output / "all_edges.csv")
    _write_csv(ordered_summary, output / "marc_edge_classification.csv")
    _write_csv(anchors, output / "positive_control_audit.csv")
    _write_csv(
        ordered_summary[ordered_summary["classification"].eq("robust_core")],
        output / "robust_core.csv",
    )
    _write_csv(
        ordered_summary[ordered_summary["classification"].eq("design_artifact")],
        output / "design_artifacts.csv",
    )
    make_figures(edges, summary, config, output)

    configured_input = Path(config["input"]["path"])
    input_path = (
        configured_input
        if configured_input.is_absolute()
        else Path(config["_base_dir"]) / configured_input
    )
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest() if input_path.exists() else None
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": config["input"]["path"],
        "input_sha256": digest,
        "config": Path(config["_config_path"]).name,
        "python": sys.version,
        "platform": platform.platform(),
        "n_edges": len(edges),
        "n_robust": int(summary["classification"].eq("robust_core").sum()),
        "n_artifacts": int(summary["classification"].eq("design_artifact").sum()),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
