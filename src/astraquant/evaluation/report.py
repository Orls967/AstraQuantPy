"""Markdown report for one walk-forward evaluation run."""

from __future__ import annotations

from typing import Any

import pandas as pd

SHARE_COLUMNS = {"directional_accuracy", "coverage"}


def _cell(column: str, value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if pd.isna(value):
            return "n/a"
        return f"{value:.1%}" if column in SHARE_COLUMNS else f"{value:.4f}"
    return str(value)


def table(frame: pd.DataFrame) -> str:
    """A Markdown table with four-decimal numbers and percentage shares."""
    if frame.empty:
        return "_None._\n"
    columns = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in frame.astype(object).itertuples(index=False):
        cells = [_cell(c, v) for c, v in zip(columns, row, strict=True)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _selection_text(selection: dict[str, Any]) -> str:
    chosen, baseline = selection["selected"], selection["baseline"]
    if chosen == baseline:
        return f"**No model beats the baseline. Selected: `{baseline}` (the baseline).**"
    return f"**Selected: `{chosen}`, replacing the baseline `{baseline}`.**"


def _target_section(name: str, result: dict[str, Any], primary: bool, level: float) -> list[str]:
    selection = result["selection"]
    role = "primary target, decides the published model" if primary else "secondary, information"
    folds = result["folds"]
    fold_columns = [c for c in folds.columns if not c.startswith("params_")]
    lines = [
        f"## `{name}` ({role})",
        "",
        f"Test rows: {len(result['predictions'])}; test years: {len(folds)}; "
        f"`R2_oos` is measured against `{selection['baseline']}`.",
        "",
        _selection_text(selection),
        "",
        "Selection rule checks:",
        "",
        table(pd.DataFrame(selection["checks"])),
        "Pooled metrics:",
        "",
        table(result["overall"].drop(columns="group")),
        "By test year (sum of squared errors; `beats` = lower than the baseline):",
        "",
        table(result["yearly"]),
        "By market:",
        "",
        table(result["by_market"]),
    ]
    if primary:
        lines += ["By ticker:", "", table(result["by_symbol"])]
    lines += [
        f"{level:.0%} prediction intervals (quantiles of earlier test years' residuals, "
        "per market; coverage is out of sample):",
        "",
        table(result["interval_by_market"]),
        "Folds:",
        "",
        table(folds[fold_columns]),
    ]
    params = [c for c in folds.columns if c.startswith("params_")]
    if params:
        lines += ["Hyperparameters chosen inside each training window:", ""]
        lines += [table(folds[["test_year", *params]])]
    return lines


def render_evaluation_report(
    results: dict[str, dict[str, Any]], manifest: dict[str, Any], primary: str
) -> str:
    """Markdown report covering every evaluated target."""
    level = float(manifest["evaluation_spec"]["interval"]["level"])
    dirty = " (tracked files had uncommitted changes)" if manifest["git_dirty"] else ""
    through = ", ".join(f"{m} {d}" for m, d in manifest["data_through"].items())
    chosen = results[primary]["selection"]
    lines = [
        "# Walk-forward evaluation",
        "",
        f"- Run {manifest['run_at_utc']} on dataset build {manifest['dataset_built_at_utc']} "
        f"(feature set `{manifest['feature_set_version']}`).",
        f"- Source: {manifest['source']}. **Unofficial data, prototyping only.**",
        f"- Git commit: `{manifest['git_commit']}`{dirty}",
        f"- Config digest: `{manifest['config_digest']}`; seed {manifest['seed']}.",
        f"- Data through: {through}",
        "- Protocol: expanding window, yearly test blocks, training labels fully realised "
        "before the test block, scaling and tuning inside the training window only "
        "(blueprint section 8; details in `docs/DECISIONS.md` section 8).",
        "",
        "## Result on the primary target",
        "",
        _selection_text(chosen),
        "",
        "The rule: a model replaces the baseline only if pooled `R2_oos > 0` and it beats "
        "the baseline in more than half of the test years. It was fixed before any model "
        "was run and applied here without adjustment.",
        "",
        "## Limitations",
        "",
        "- The 11 names were chosen with hindsight; results carry selection bias and do not "
        "generalise to stocks in general.",
        "- The sample is small: about four quarterly observations per stock per year, and "
        "the names are highly correlated. Yearly comparisons rest on a handful of rows.",
        "- Prices come from Yahoo Finance through yfinance, an unofficial source. Yahoo "
        "applies unrecorded adjustments at Indonesian rights-issue dates "
        "(`docs/DECISIONS.md` 6.3).",
        "- Six targets are evaluated. Only the quarterly target decides the published "
        "model; a good result on one secondary target may be chance.",
        "- These are prediction intervals from past forecast errors. They assume future "
        "errors resemble past ones.",
        "",
    ]
    for name, result in results.items():
        lines += _target_section(name, result, name == primary, level)
    return "\n".join(lines)


def results_table(results: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """One row per target and model: pooled metrics plus the selection outcome."""
    frames = []
    for name, result in results.items():
        frame = result["overall"].drop(columns="group")
        frame.insert(0, "target", name)
        frame["baseline"] = result["selection"]["baseline"]
        frame["selected"] = frame["model"] == result["selection"]["selected"]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
