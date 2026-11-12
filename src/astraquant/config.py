"""Load the asset universe and settings from ``configs/``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"


@dataclass(frozen=True)
class Asset:
    """One tradable or context series."""

    symbol: str
    name: str
    market: str
    role: str  # "target" or "context"
    calendar: str | None
    currency: str
    timezone: str

    @property
    def file_stem(self) -> str:
        """Filesystem-safe name derived from the symbol."""
        return re.sub(r"[^A-Za-z0-9._-]", "_", self.symbol)


@dataclass(frozen=True)
class SplitCheck:
    """A known split used to verify price-return semantics."""

    symbol: str
    date: date
    ratio: float


@dataclass(frozen=True)
class Settings:
    """Project settings needed by the data milestone."""

    seed: int
    provider: str
    start_date: date
    raw_dir: Path
    processed_dir: Path
    report_path: Path
    request_pause_seconds: float
    max_retries: int
    max_abs_daily_return: float
    split_checks: tuple[SplitCheck, ...]
    extra_holidays: dict[str, tuple[date, ...]]
    targets: dict[str, dict[str, dict[str, Any]]]
    exclusions: dict[str, tuple[date, ...]]
    price_breaks: dict[str, tuple[date, ...]]
    evaluation: dict[str, Any]
    forecast: dict[str, Any]
    dataset: dict[str, Any]
    features: dict[str, Any]
    context: dict[str, dict[str, Any]]
    dataset_dir: Path
    dataset_report_path: Path

    def excluded_dates(self, symbol: str) -> tuple[date, ...]:
        """Bar dates removed in cleaning for this symbol."""
        return self.exclusions.get(symbol, ())

    def breaks_for(self, symbol: str) -> tuple[date, ...]:
        """Sessions whose close-to-close return is not trustworthy for this symbol."""
        return self.price_breaks.get(symbol, ())

    def holidays_for(self, calendar: str | None) -> tuple[date, ...]:
        """Official extra holidays configured for a calendar code."""
        return self.extra_holidays.get(calendar or "", ())


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_assets(path: Path | None = None) -> list[Asset]:
    """Read ``assets.yaml`` and return the configured assets in file order."""
    raw = _read_yaml(path or CONFIG_DIR / "assets.yaml")
    markets = raw["markets"]
    assets: list[Asset] = []
    for item in raw["assets"]:
        if item["role"] not in {"target", "context"}:
            raise ValueError(f"{item['symbol']}: unknown role {item['role']!r}")
        market = markets[item["market"]]
        assets.append(
            Asset(
                symbol=item["symbol"],
                name=item["name"],
                market=item["market"],
                role=item["role"],
                calendar=market["calendar"],
                currency=market["currency"],
                timezone=market["timezone"],
            )
        )
    symbols = [a.symbol for a in assets]
    if len(symbols) != len(set(symbols)):
        raise ValueError("assets.yaml contains duplicate symbols")
    return assets


def load_settings(path: Path | None = None, root: Path | None = None) -> Settings:
    """Read ``settings.yaml``. Relative paths are resolved against ``root``."""
    raw = _read_yaml(path or CONFIG_DIR / "settings.yaml")
    base = root or REPO_ROOT
    data = raw["data"]
    exclusions: dict[str, list[date]] = {}
    for item in raw.get("exclusions", []):
        exclusions.setdefault(item["symbol"], []).append(item["date"])
    dataset = raw.get("dataset", {})
    price_breaks: dict[str, list[date]] = {}
    for item in raw.get("price_breaks", []):
        price_breaks.setdefault(item["symbol"], []).append(item["date"])
    return Settings(
        seed=int(raw["seed"]),
        provider=data["provider"],
        start_date=data["start_date"],
        raw_dir=base / data["raw_dir"],
        processed_dir=base / data["processed_dir"],
        report_path=base / data["report_path"],
        request_pause_seconds=float(data["request_pause_seconds"]),
        max_retries=int(data["max_retries"]),
        max_abs_daily_return=float(raw["validation"]["max_abs_daily_return"]),
        split_checks=tuple(SplitCheck(**item) for item in raw.get("split_checks", [])),
        extra_holidays={
            code: tuple(days)
            for code, days in raw.get("calendars", {}).get("extra_holidays", {}).items()
        },
        targets=raw.get("targets", {}),
        exclusions={symbol: tuple(days) for symbol, days in exclusions.items()},
        price_breaks={symbol: tuple(days) for symbol, days in price_breaks.items()},
        evaluation=raw.get("evaluation", {}),
        forecast=raw.get("forecast", {}),
        dataset=dataset,
        features=raw.get("features", {}),
        context=raw.get("context", {}),
        dataset_dir=base / dataset.get("dataset_dir", "data/processed/dataset"),
        dataset_report_path=base / dataset.get("report_path", "reports/dataset_summary.md"),
    )
