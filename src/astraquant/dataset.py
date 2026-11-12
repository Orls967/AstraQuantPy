"""Assemble the research datasets from processed bars.

Two tables are built:

- **daily**: one row per asset per trading session, with features known at
  that session's close and the secondary forward targets.
- **quarterly**: one row per asset per calendar quarter, with features at the
  origin (last session of the previous quarter) and the quarter's price return.

No scaler or other fitted transformation is applied here. Anything fitted
belongs inside the walk-forward training window (Milestone 3).
"""

from __future__ import annotations

import pandas as pd

from astraquant import calendars, targets
from astraquant.config import Asset, Settings
from astraquant.features import build_features, feature_columns

ID_COLUMNS = ["symbol", "market", "currency", "date"]


def to_session_grid(bars: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Put bars on the full session grid: one row per session, NaN where no bar.

    Bars on dates outside ``sessions`` are left out; the caller can count them.
    """
    if bars["date"].duplicated().any():
        raise ValueError("duplicate dates in bars")
    return bars.set_index("date").reindex(sessions)


def lagged_on_grid(series: pd.Series, sessions: pd.DatetimeIndex, lag_days: int) -> pd.Series:
    """Value of a weekday series ``lag_days`` business days before each session.

    Exact-date lookup: if that earlier date has no bar the result is NaN, not
    the nearest older value.
    """
    lookup = sessions - pd.tseries.offsets.BDay(lag_days)
    return pd.Series(series.reindex(lookup).to_numpy(), index=sessions)


def _asset_sessions(asset: Asset, bars: pd.DataFrame, settings: Settings) -> pd.DatetimeIndex:
    return calendars.sessions(
        asset.calendar,
        bars["date"].min(),
        bars["date"].max(),
        settings.holidays_for(asset.calendar),
    )


def build_asset_daily(
    asset: Asset, prices: dict[str, pd.DataFrame], settings: Settings
) -> pd.DataFrame:
    """Daily features and forward targets for one target asset."""
    spec = settings.dataset
    context = settings.context[asset.market]
    bars = prices[asset.symbol]
    sessions = _asset_sessions(asset, bars, settings)
    grid = to_session_grid(bars, sessions)
    breaks = settings.breaks_for(asset.symbol)
    index_close = to_session_grid(prices[context["index"]], sessions)["close"]
    fx_close = None
    if "fx" in context:
        fx = prices[context["fx"]].set_index("date")["close"]
        fx_close = lagged_on_grid(fx, sessions, int(context["fx_lag_business_days"]))

    features = build_features(
        grid["close"],
        grid["volume"],
        index_close,
        fx_close,
        settings.features,
        int(spec["annualisation_sessions"]),
        breaks,
    )
    out = pd.DataFrame(index=sessions)
    out["symbol"] = asset.symbol
    out["market"] = asset.market
    out["currency"] = asset.currency
    out["date"] = sessions
    out["close"] = grid["close"]
    out["has_bar"] = grid["close"].notna()
    out["is_id"] = int(asset.market == "ID")
    out = pd.concat([out, features], axis=1)
    for h in spec["return_horizons"]:
        out[f"fwd_ret_{h}"] = targets.forward_return(grid["close"], h, breaks)
    for h in spec["volatility_horizons"]:
        out[f"fwd_vol_{h}"] = targets.forward_realised_vol(
            grid["close"], h, int(spec["annualisation_sessions"]), breaks
        )
    for h in sorted({*spec["return_horizons"], *spec["volatility_horizons"]}):
        out[f"target_end_date_{h}"] = targets.target_end_date(sessions, h)
    return out.reset_index(drop=True)


def build_daily(
    assets: list[Asset], prices: dict[str, pd.DataFrame], settings: Settings
) -> pd.DataFrame:
    """Daily dataset for every target asset, pooled."""
    frames = [build_asset_daily(a, prices, settings) for a in assets if a.role == "target"]
    return pd.concat(frames, ignore_index=True)


def build_quarterly(daily: pd.DataFrame, assets: list[Asset], settings: Settings) -> pd.DataFrame:
    """Quarterly dataset: features at the origin and the quarter's price return.

    A quarter is included once its origin session is inside the asset's data.
    Its ``q_return`` stays NaN until the quarter's last session has a bar.
    """
    names = feature_columns(settings.features)
    frames = []
    for asset in assets:
        if asset.role != "target":
            continue
        own = daily[daily["symbol"] == asset.symbol].set_index("date")
        bounds = targets.quarter_boundaries(
            asset.calendar,
            own.index.min(),
            own.index.max() + pd.Timedelta(days=95),
            settings.holidays_for(asset.calendar),
        )
        bounds = bounds[bounds["target_start_date"].isin(own.index)]
        table = targets.quarterly_returns(own["close"], bounds, settings.breaks_for(asset.symbol))
        table.insert(0, "symbol", asset.symbol)
        table.insert(1, "market", asset.market)
        table.insert(2, "currency", asset.currency)
        table["origin_date"] = table["target_start_date"]
        table["is_id"] = int(asset.market == "ID")
        origin_features = own.loc[table["target_start_date"], names].reset_index(drop=True)
        frames.append(pd.concat([table.reset_index(drop=True), origin_features], axis=1))
    return pd.concat(frames, ignore_index=True)


def data_through(daily: pd.DataFrame) -> dict[str, str]:
    """Last session with data, per market."""
    last = daily[daily["has_bar"]].groupby("market")["date"].max()
    return {market: day.date().isoformat() for market, day in last.items()}
