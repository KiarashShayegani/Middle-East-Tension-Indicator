"""Core tension index calculation for METI."""

from __future__ import annotations

import math
from typing import Any

from meti.config import Settings, get_settings
from meti.data.providers import get_all_asset_data


def normalize(
    raw_value: float,
    baseline: float = 20.0,
    max_positive: float = 5.0,
    max_negative: float = -5.0,
    clamp_min: float = 0.0,
    clamp_max: float = 100.0,
) -> int:
    """
    Map a raw weighted change into a 0-100 tension score.

    - raw ≈ 0  → baseline (default 20)
    - positive → linear rise toward 100
    - negative → logarithmic decay toward 0
    """
    raw = float(raw_value)

    if raw >= 0:
        if max_positive == 0:
            scaled = 0.0
        else:
            scaled = (raw / max_positive) * (clamp_max - baseline)
        score = baseline + scaled
    else:
        # log decay so large negative moves don't instantly hit 0
        denom = math.log1p(abs(max_negative))
        if denom == 0:
            decay = 0.0
        else:
            decay = (math.log1p(abs(raw)) / denom) * baseline
        score = baseline - decay

    score = max(clamp_min, min(clamp_max, score))
    return int(round(score))


def calculate_raw_index(asset_data: dict[str, Any], settings: Settings | None = None) -> float:
    """Weighted sum of each asset's multi-timeframe weighted change."""
    settings = settings or get_settings()
    total = 0.0
    for ticker, info in asset_data.items():
        weight = settings.assets[ticker].weight if ticker in settings.assets else 0.0
        total += info["weighted_change"] * weight
    return float(total)


def get_regime(score: int) -> str:
    """Human-readable regime label."""
    if score < 25:
        return "Calm"
    if score < 50:
        return "Elevated"
    if score < 75:
        return "High"
    return "Critical"


def calculate_tension_index(
    settings: Settings | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Full pipeline: fetch data → calculate → optionally save snapshot.

    Returns a rich dict ready for the UI.
    """
    settings = settings or get_settings()
    asset_data = get_all_asset_data(settings)

    raw = calculate_raw_index(asset_data, settings)
    norm_cfg = settings.normalization
    score = normalize(
        raw,
        baseline=norm_cfg.baseline,
        max_positive=norm_cfg.max_positive,
        max_negative=norm_cfg.max_negative,
        clamp_min=norm_cfg.clamp_min,
        clamp_max=norm_cfg.clamp_max,
    )

    # Contribution of each asset to the raw index
    contributions = {}
    for ticker, info in asset_data.items():
        contributions[ticker] = {
            "name": info["name"],
            "emoji": info["emoji"],
            "weight": info["weight"],
            "weighted_change": info["weighted_change"],
            "contribution": info["weighted_change"] * info["weight"],
            "current_price": info["current_price"],
            "changes": info["changes"],
            "color": info["color"],
        }

    result = {
        "raw_index": round(raw, 4),
        "tension_score": score,
        "regime": get_regime(score),
        "assets": asset_data,
        "contributions": contributions,
        "timestamp": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
    }

    if persist:
        try:
            from meti.data.history import save_snapshot

            asset_changes = {
                t: info["weighted_change"] for t, info in asset_data.items()
            }
            save_snapshot(
                raw_index=raw,
                tension_score=score,
                asset_changes=asset_changes,
            )
        except Exception:
            # History is best-effort; never break the main path
            pass

    return result
