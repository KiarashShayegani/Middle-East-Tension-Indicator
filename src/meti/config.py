"""Configuration loader for METI."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AssetConfig(BaseModel):
    name: str
    weight: float
    direction: int = 1
    emoji: str = ""
    color: str = "#3b82f6"
    description: str = ""


class TimeframeConfig(BaseModel):
    label: str
    weight: float
    period: str
    interval: str
    lookback_bars: int


class NormalizationConfig(BaseModel):
    baseline: float = 20.0
    max_positive: float = 5.0
    max_negative: float = -5.0
    clamp_min: float = 0.0
    clamp_max: float = 100.0


class GaugeStep(BaseModel):
    range: list[float]
    color: str
    label: str = ""


class GaugeConfig(BaseModel):
    steps: list[GaugeStep] = Field(default_factory=list)


class HistoryConfig(BaseModel):
    db_path: str = "data/meti_history.db"
    snapshot_interval_minutes: int = 15
    keep_days: int = 90


class AppConfig(BaseModel):
    title: str = "Middle-East Tension Indicator"
    short_name: str = "METI"
    version: str = "1.0.0"
    description: str = ""
    refresh_seconds: int = 180
    cache_ttl_seconds: int = 120


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    assets: dict[str, AssetConfig] = Field(default_factory=dict)
    timeframes: dict[str, TimeframeConfig] = Field(default_factory=dict)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    gauge: GaugeConfig = Field(default_factory=GaugeConfig)
    history: HistoryConfig = Field(default_factory=HistoryConfig)

    @property
    def asset_weights(self) -> dict[str, float]:
        return {k: v.weight for k, v in self.assets.items()}

    @property
    def timeframe_weights(self) -> dict[str, float]:
        return {k: v.weight for k, v in self.timeframes.items()}


def _find_config_path() -> Path:
    """Locate default.yaml relative to this package or project root."""
    candidates = [
        Path(__file__).resolve().parents[2] / "config" / "default.yaml",  # src/meti -> project
        Path.cwd() / "config" / "default.yaml",
        Path(__file__).resolve().parents[3] / "config" / "default.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find config/default.yaml")


@lru_cache(maxsize=1)
def get_settings(config_path: str | None = None) -> Settings:
    """Load and cache settings from YAML."""
    path = Path(config_path) if config_path else _find_config_path()
    with open(path, "r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    # Allow simple env overrides later if needed
    return Settings(**raw)
