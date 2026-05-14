"""models package."""

from .ml_baseline import (
    MLMultiTaskBaseline,
    MLMultiTaskSearchEstimator,
    pack_multitask_targets,
)
from .model_registry import recommend_model, build_clf_pipeline, build_reg_pipeline

try:
    from .dl_multitask import MultiTaskDLModel
    _DL_AVAILABLE = True
except ImportError:  # torch not installed
    MultiTaskDLModel = None  # type: ignore[assignment,misc]
    _DL_AVAILABLE = False

__all__ = [
    "MLMultiTaskBaseline",
    "MLMultiTaskSearchEstimator",
    "MultiTaskDLModel",
    "recommend_model",
    "build_clf_pipeline",
    "build_reg_pipeline",
    "pack_multitask_targets",
]
