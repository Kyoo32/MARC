# MARC Agent Guide

This file is a compact operating guide for AI coding agents, CLI assistants, and
human researchers working in this repository. It is intentionally tool-neutral:
Codex, Claude, terminal agents, and ordinary editors can all use the same logic.

## Purpose

MARC (Multi-Axis Robustness Check) is a domain-agnostic protocol for separating
robust time-series causal-discovery signals from artifacts introduced by
analysis design choices.

Do not treat MARC as an air-quality-only workflow. The Seoul case study is one
example application.

## Core workflow

1. Start from a researcher-supplied multivariate time-series dataset.
2. Bind the dataset and study design in a YAML configuration file.
3. Run causal discovery under controlled variation across five audit axes.
4. Compare standardized edges across runs.
5. Classify edges as robust core signals or design-dependent artifacts.
6. Check whether domain-knowledge positive controls are recovered.
7. Write tables, figures, cached runs, and a manifest.

The preferred command is:

```bash
marc run marc_config.yml
```

Fallback:

```bash
python run_marc.py run marc_config.yml
```

## Five audit axes

- Axis 1: Spatial, unit, subject, or replicate recurrence.
- Axis 2: Lag-window sensitivity, such as `tau_max=3` versus `tau_max=6`.
- Axis 3: Algorithm comparison, such as PCMCI+ versus LPCMCI or user adapters.
- Axis 4: Effect-size cutoff sensitivity.
- Axis 5: Run reproducibility across repeated executions.

## Input contract

The repository must not assume a built-in research dataset. A new researcher
must provide their own CSV, Parquet, or Excel file and edit `marc_config.yml`.

Minimum expectations:

- one time column;
- one optional unit column;
- at least two numeric variables;
- enough rows per unit after missing-data handling;
- explicit positive controls if the researcher wants anchor-based validation.

## Output contract

A successful MARC run should produce, at minimum:

- `all_edges.csv`
- `marc_edge_classification.csv`
- `positive_control_audit.csv`
- `robust_core.csv`
- `design_artifacts.csv`
- four standard figures
- `manifest.json`

Generated outputs are local analysis products unless the researcher explicitly
chooses to publish them.

## Agent behavior rules

When helping with this repository:

- Preserve the domain-agnostic framing.
- Do not hard-code private file paths, local machine names, or personal data
  locations.
- Do not commit raw research data unless the user explicitly confirms it is
  redistributable.
- Keep `data/` for researcher-supplied data and respect `.gitignore`.
- Prefer editing `marc_config.yml` or a copy of the template over changing
  package code for ordinary studies.
- If adding a new domain case study, document its data source, input schema,
  preprocessing assumptions, positive controls, and license or terms of use.
- When interpreting results, distinguish robust recurrence from causal truth.
  MARC audits stability under design variation; it does not by itself prove
  causal mechanisms.
- Report failures plainly, including missing packages, empty edge sets,
  positive-control failures, unstable signs, or dataset quality problems.

## Development checks

Before suggesting that a change is ready, run at least a smoke test when the
environment allows it. Use an environment where MARC dependencies are installed
(for example, after `pip install -e .`):

```bash
python examples/make_demo_data.py
python run_marc.py run examples/marc_demo.yml
```

For documentation-only changes, inspect links and confirm that no private paths
or raw data references were introduced.

## Seoul case-study boundary

`case_study_seoul/` is a manuscript-supporting example. It may describe public
Seoul Open Data Plaza sources, but the public repository should not redistribute
raw OA-2275, OA-2220, or OA-1199 files. Researchers should download them from
the official source and build their own local MARC input table.
