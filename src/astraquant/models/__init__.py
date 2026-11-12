"""Forecast models: two naive baselines, Ridge and LightGBM."""

from astraquant.models.base import ModelSpec
from astraquant.models.baselines import HistoricalMeanModel, TrailingFeatureModel, ZeroModel
from astraquant.models.lightgbm_model import LightGBMModel
from astraquant.models.ridge import RidgeModel

__all__ = [
    "HistoricalMeanModel",
    "LightGBMModel",
    "ModelSpec",
    "RidgeModel",
    "TrailingFeatureModel",
    "ZeroModel",
]
