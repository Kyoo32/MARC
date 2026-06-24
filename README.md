# MARC

MARC (Multi-Axis Robustness Check) separates robust causal-discovery signal
from analysis-design artifacts in observational multivariate time series.

MARC is domain-agnostic. Variable names, units, positive controls, algorithms,
lag windows, and thresholds are supplied through one YAML file.

English | [한국어](README.ko.md)

## One-command use

Clone the repository, create an environment, and install the package:

```bash
conda create -n marc python=3.11 -y
conda activate marc
pip install -e .
```

Prepare a study:

```bash
cp marc_config_template.yml marc_config.yml
```

Then:

1. place the research dataset in `data/`;
2. edit `marc_config.yml`;
3. run the complete protocol:

```bash
marc run marc_config.yml
```

Without installing the command-line entry point:

```bash
python run_marc.py run marc_config.yml
```

The command performs the complete protocol:

1. loads and validates unit-level multivariate time series;
2. reruns causal discovery across units, lag windows, algorithms, and repeats;
3. recalculates recurrence across effect-size cutoffs;
4. audits domain-knowledge positive controls;
5. classifies edges into `robust_core` and `design_artifact`;
6. writes standard tables, four figures, cached runs, and a manifest.

## Input format

Researchers supply their own wide CSV, Parquet, or Excel table. No research
dataset is bundled or selected automatically.

```text
time,unit,X,Y,Z
2025-01-01 00:00,A,...
2025-01-01 01:00,A,...
2025-01-01 00:00,B,...
```

`unit_column` is optional. Without it, MARC treats the full table as one unit.

## Code structure

```text
src/marc/
  data.py       input and validation
  engines.py    causal-discovery adapters
  audit.py      five controlled-variation axes and classification
  report.py     tables, figures, and provenance
  cli.py        one-command orchestration
```

## Algorithms

Built in:

- Tigramite PCMCI+ with `ParCorr`
- Tigramite LPCMCI with `ParCorr`

Custom algorithms use an adapter factory:

```yaml
algorithms:
  - name: MyAlgorithm
    engine: my_package.my_adapter:create_engine
```

The returned engine must implement:

```python
run(frame, tau_max, repeat, unit) -> pandas.DataFrame
```

MARC only requires standardized edges with source, target, lag, orientation,
effect size, and optional p/q values.

## Demo

```bash
python examples/make_demo_data.py
python run_marc.py run examples/marc_demo.yml
```

The Jupyter notebook is deliberately thin: edit the YAML path and run its
single command cell.

## Seoul case study

The Seoul air-quality directory is an example application of MARC, not a default
input pipeline. It contains manuscript figures and summary tables, while raw
public datasets must be obtained by researchers from the official Seoul Open
Data Plaza sources described in [case_study_seoul/README.md](case_study_seoul/README.md).

## Repository layout

```text
data/                       researcher-supplied datasets (ignored by Git)
src/marc/                   reusable MARC implementation
examples/                   synthetic demonstration only
case_study_seoul/           manuscript case-study figures and summary tables
MARC_one_command.ipynb      optional notebook front end
marc_config_template.yml    study configuration template
SKILL.md                    short guide for AI coding agents and CLI assistants
```

Generated outputs and local configuration files are ignored by Git. The
repository therefore does not publish user paths, raw research data, or local
run caches.

## Agent guide

This repository includes [SKILL.md](SKILL.md), a tool-neutral guide for AI coding
agents and CLI assistants. It summarizes the MARC workflow, input and output
contracts, safe editing rules, and smoke-test expectations so that Codex,
Claude, terminal agents, and human collaborators can work from the same project
logic.

## License and data terms

MARC source code is released under the MIT License. The license covers the code
and documentation in this repository. It does not relicense external research
data, including public datasets downloaded from Seoul Open Data Plaza or any
other provider. Users are responsible for following the terms of their data
source.
