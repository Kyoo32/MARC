from __future__ import annotations

import importlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


EDGE_COLUMNS = [
    "unit", "algorithm", "tau_max", "repeat", "source", "target", "lag",
    "orientation", "p_value", "q_value", "effect", "abs_effect",
]


def _orientation(mark: str, lag: int) -> str:
    if lag > 0:
        return "directed"
    return {
        "-->": "directed",
        "<--": "directed_reverse",
        "<->": "bidirected",
        "x-x": "ambiguous",
        "o-o": "partial",
        "o->": "partial_directed",
        "<-o": "partial_directed_reverse",
    }.get(str(mark), "unresolved")


def _extract(results: dict, names: list[str], metadata: dict) -> pd.DataFrame:
    graph = results["graph"]
    values = results.get("val_matrix")
    pvalues = results.get("p_matrix")
    qvalues = results.get("q_matrix", pvalues)
    rows = []
    for source in range(len(names)):
        for target in range(len(names)):
            for lag in range(graph.shape[2]):
                mark = str(graph[source, target, lag])
                if not mark:
                    continue
                effect = float(values[source, target, lag]) if values is not None else np.nan
                rows.append({
                    **metadata,
                    "source": names[source],
                    "target": names[target],
                    "lag": lag,
                    "orientation": _orientation(mark, lag),
                    "p_value": float(pvalues[source, target, lag]) if pvalues is not None else np.nan,
                    "q_value": float(qvalues[source, target, lag]) if qvalues is not None else np.nan,
                    "effect": effect,
                    "abs_effect": abs(effect),
                })
    return pd.DataFrame(rows, columns=EDGE_COLUMNS)


@dataclass
class TigramiteEngine:
    name: str
    kind: str
    params: dict

    def run(self, frame: pd.DataFrame, tau_max: int, repeat: int, unit: str) -> pd.DataFrame:
        from tigramite import data_processing as pp
        from tigramite.independence_tests.parcorr import ParCorr

        names = list(frame.columns)
        dataframe = pp.DataFrame(frame.to_numpy(dtype=float), var_names=names)
        test = ParCorr(significance=self.params.get("significance", "analytic"))
        metadata = {
            "unit": unit,
            "algorithm": self.name,
            "tau_max": int(tau_max),
            "repeat": int(repeat),
        }
        pc_alpha = float(self.params.get("pc_alpha", 0.05))

        if self.kind == "pcmciplus":
            from tigramite.pcmci import PCMCI

            model = PCMCI(dataframe=dataframe, cond_ind_test=test, verbosity=0)
            results = model.run_pcmciplus(
                tau_min=int(self.params.get("tau_min", 0)),
                tau_max=int(tau_max),
                pc_alpha=pc_alpha,
                fdr_method=self.params.get("fdr_method", "none"),
            )
            if results.get("p_matrix") is not None and results.get("q_matrix") is None:
                results["q_matrix"] = model.get_corrected_pvalues(
                    p_matrix=results["p_matrix"],
                    fdr_method=self.params.get("edge_fdr_method", "fdr_bh"),
                )
            return _extract(results, names, metadata)

        if self.kind == "lpcmci":
            from tigramite.lpcmci import LPCMCI

            model = LPCMCI(dataframe=dataframe, cond_ind_test=test, verbosity=0)
            results = model.run_lpcmci(
                tau_min=int(self.params.get("tau_min", 0)),
                tau_max=int(tau_max),
                pc_alpha=pc_alpha,
            )
            return _extract(results, names, metadata)
        raise ValueError(f"Unsupported Tigramite algorithm: {self.kind}")


def build_engines(specs: list[dict]) -> list:
    engines = []
    for spec in specs:
        engine_type = spec.get("engine", spec["name"])
        if engine_type in {"pcmciplus", "lpcmci"}:
            engines.append(TigramiteEngine(spec["name"], engine_type, spec.get("params", {})))
            continue
        if ":" not in engine_type:
            raise ValueError(
                f"Custom engine must use 'module.path:factory', received {engine_type!r}"
            )
        module_name, factory_name = engine_type.split(":", 1)
        factory = getattr(importlib.import_module(module_name), factory_name)
        engines.append(factory(spec))
    return engines
