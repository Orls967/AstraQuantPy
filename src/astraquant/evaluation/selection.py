"""The fixed selection rule (blueprint section 8), applied mechanically."""

from __future__ import annotations

from typing import Any

import pandas as pd


def apply_selection_rule(
    overall: pd.DataFrame, yearly: pd.DataFrame, candidates: list[str], baseline: str
) -> dict[str, Any]:
    """Decide which model is published.

    A candidate replaces the baseline only if its pooled ``R2_oos`` is above
    zero **and** it beats the baseline in more than half of the test years.
    If several candidates qualify, the one with the highest pooled ``R2_oos``
    is chosen. Otherwise the baseline is published.
    """
    n_years = len(yearly)
    checks = []
    for name in candidates:
        r2 = float(overall.loc[overall["model"] == name, "r2_oos"].iloc[0])
        wins = int(yearly[f"beats_{name}"].sum())
        checks.append(
            {
                "model": name,
                "pooled_r2_oos": r2,
                "r2_above_zero": bool(r2 > 0),
                "years_beating_baseline": wins,
                "test_years": n_years,
                "beats_in_more_than_half": bool(wins > n_years / 2),
                "qualifies": bool(r2 > 0 and wins > n_years / 2),
            }
        )
    qualified = [c for c in checks if c["qualifies"]]
    selected = max(qualified, key=lambda c: c["pooled_r2_oos"])["model"] if qualified else baseline
    return {"baseline": baseline, "selected": selected, "checks": checks}
