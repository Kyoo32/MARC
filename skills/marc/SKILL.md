---
name: marc
description: Run the MARC (Multi-Axis Robustness Check) protocol on a multivariate time-series dataset to separate robust causal-discovery signal from analysis-design artifacts. Use when the user wants to run MARC, audit causal edges for robustness, reproduce the MARC protocol, check positive controls, or classify edges into robust_core vs design_artifact. Triggers: run MARC, MARC robustness check, MARC 돌려줘, 인과 엣지 강건성 검사, robust core vs design artifact, 5축 audit. Not for: editing MARC package internals or unrelated causal-discovery tools.
argument-hint: "[config yml path, or dataset path to scaffold a config from]"
---

# MARC Skill

MARC (Multi-Axis Robustness Check) is a domain-agnostic protocol that reruns
time-series causal discovery under controlled variation across five audit axes,
then classifies each standardized edge as a `robust_core` signal or a
`design_artifact`.

This skill is intentionally written for multiple agent environments. It can be
used by Claude Code, Codex-style coding agents, terminal assistants, and human
researchers. The Seoul air-quality case study is one example application; do not
treat MARC as air-quality-specific.

## When To Use

Use this skill when the user wants to:

- run MARC on a multivariate time-series dataset;
- audit causal-discovery edges for robustness;
- classify edges into `robust_core` and `design_artifact`;
- check domain-knowledge positive controls;
- reproduce the MARC demo or a configured MARC study.

Do not use this skill for unrelated causal-discovery tools or for changing MARC
package internals unless the user explicitly asks for implementation work.

## Core Workflow

1. Confirm that MARC dependencies are installed. `marc --help` should work after
   `pip install -e .`. MARC dependencies include `joblib`; install or reinstall
   the package if `ModuleNotFoundError: joblib` appears.
2. Resolve the study configuration.
3. Run the protocol with the resolved config path.
4. Verify the required outputs.
5. Summarize robust edges, design artifacts, and positive-control recovery.
6. Report failures plainly.

## Resolve The Config

- If the argument is an existing `*.yml` or `*.yaml`, use that path directly.
- If the argument is a dataset path such as `.csv`, `.parquet`, or `.xlsx`, copy
  `marc_config_template.yml` to a study config, then fill in:
  - `input.path`
  - `input.time_column`
  - optional `input.unit_column`, omitted for a single time series
  - `input.variables`
  - at least one `positive_controls` entry when the study uses anchor checks
- With no argument, ask for the config path or dataset path.
- Never invent a dataset. MARC ships no real research dataset by default.

Confirm newly edited config values with the user before running a real study.

## Run The Protocol

Prefer the console entry point:

```bash
marc run <config_path>
```

Fallback if the console script is unavailable:

```bash
python run_marc.py run <config_path>
```

For the bundled demo:

```bash
python examples/make_demo_data.py
python run_marc.py run examples/marc_demo.yml
```

## Five Audit Axes

- Axis 1: Spatial, unit, subject, or replicate recurrence.
- Axis 2: Lag-window sensitivity, such as `tau_max=3` versus `tau_max=6`.
- Axis 3: Algorithm comparison, such as PCMCI+ versus LPCMCI or user adapters.
- Axis 4: Effect-size cutoff sensitivity.
- Axis 5: Run reproducibility across repeated executions.

## Input Contract

A MARC input table must provide:

- one time column;
- one optional unit column;
- at least two numeric variables;
- enough rows per unit after missing-data handling;
- explicit positive controls if the researcher wants anchor-based validation.

Researchers provide their own CSV, Parquet, or Excel files. Keep raw research
data out of Git unless the user explicitly confirms redistribution is allowed.

## Output Contract

A successful MARC run should produce these files in `output.directory`:

- `all_edges.csv`
- `marc_edge_classification.csv`
- `positive_control_audit.csv`
- `robust_core.csv`
- `design_artifacts.csv`
- four standard figures
- `manifest.json`

Summarize `robust_core` versus `design_artifacts` counts and whether each
positive control was `recovered` with `sign_ok`.

## Guardrails

- Preserve the domain-agnostic framing.
- Prefer editing YAML configuration over changing package code for ordinary
  studies.
- Do not hard-code private paths, machine names, or personal data locations.
- Keep `data/` for researcher-supplied data and respect `.gitignore`.
- Distinguish robust recurrence from causal truth. MARC audits stability under
  design variation; it does not by itself prove causal mechanisms.
- State failures directly: empty edge sets, unrecovered positive controls,
  unstable signs, missing packages, or dataset-quality problems.

## Smoke Test

To verify the install end to end without user data, use an environment where
MARC dependencies are installed, for example after `pip install -e .`:

```bash
python examples/make_demo_data.py
python run_marc.py run examples/marc_demo.yml
```

Expected result: `robust_core >= 1`, and the demo positive control
`X drives Y at lag 1` is recovered with `sign_ok=True`.

## Seoul Case-Study Boundary

`case_study_seoul/` is a manuscript-supporting example. It may describe public
Seoul Open Data Plaza sources, but the public repository should not redistribute
raw OA-2275, OA-2220, or OA-1199 files. Researchers should download data from
the official source and build their own local MARC input table.
