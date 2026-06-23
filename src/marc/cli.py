from __future__ import annotations

import argparse
from pathlib import Path

from .audit import run_grid, summarize
from .config import load_config, resolve_path
from .data import load_units
from .engines import build_engines
from .report import write_outputs


def run(config_path: str) -> Path:
    config = load_config(config_path)
    output = resolve_path(config, config["output"]["directory"])
    output.mkdir(parents=True, exist_ok=True)

    units, variables = load_units(config)
    engines = build_engines(config["algorithms"])
    print(f"[MARC] units={len(units)} variables={len(variables)}")
    print(
        f"[MARC] algorithms={[engine.name for engine in engines]} "
        f"lag_windows={config['audit']['lag_windows']} "
        f"repeats={config['audit'].get('run_repeats', 1)}"
    )

    edges = run_grid(units, engines, config["audit"], output)
    summary, anchors = summarize(edges, config)
    write_outputs(edges, summary, anchors, config, output)
    print(
        f"[MARC] robust_core={summary['classification'].eq('robust_core').sum()} "
        f"design_artifacts={summary['classification'].eq('design_artifact').sum()}"
    )
    print(f"[MARC] output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="marc",
        description="Run the Multi-Axis Robustness Check in one command.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run all five audit axes")
    run_parser.add_argument("config", help="path to MARC YAML configuration")
    args = parser.parse_args()
    if args.command == "run":
        run(args.config)


if __name__ == "__main__":
    main()
