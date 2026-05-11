from __future__ import annotations

import logging
from typing import NamedTuple

import joblib
import numpy as np
import pandas as pd

from src.config import MODELS_DIR
from src.pi_client import recorded_range, tag_value_at, write_tag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tag → column name mapping (PI tag names differ from model feature names)
# ---------------------------------------------------------------------------
_BASE_CPII  = ["na2o", "fe2o3", "cao", "so3", "blaine", "sio2", "pf", "#400", "r.i", "mgo"]
_BASE_CPIII = ["cao", "fe2o3", "blaine", "so3", "pf", "sio2", "na2o", "r.i", "mgo", "#400"]
_BASE_CPIV  = ["na2o", "fe2o3", "cao", "k2o", "so3", "blaine", "sio2", "al2o3", "pf", "#325"]


# ---------------------------------------------------------------------------
# Pipeline configuration per (cement_type, horizon_days)
# ---------------------------------------------------------------------------
class PipelineCfg(NamedTuple):
    raw_cols:    list[str]                      # columns to initially select
    filter_col:  str | None                     # filter notna on this col before growth
    growth_ops:  list[tuple[str, str, str]]     # (col_a, col_b, output_name)
    model_cols:  list[str]                      # final feature columns (no timestamp)


PIPELINE: dict[tuple[str, int], PipelineCfg] = {
    ("cpiif", 3): PipelineCfg(
        raw_cols   = _BASE_CPII,
        filter_col = None,
        growth_ops = [],
        model_cols = _BASE_CPII,
    ),
    ("cpiif", 7): PipelineCfg(
        raw_cols   = _BASE_CPII + ["compressive_strength_3d", "compressive_strength_7d"],
        filter_col = "compressive_strength_3d",
        growth_ops = [("compressive_strength_3d", "compressive_strength_7d", "growth_7d")],
        model_cols = _BASE_CPII + ["growth_7d", "compressive_strength_3d"],
    ),
    ("cpiif", 28): PipelineCfg(
        raw_cols   = _BASE_CPII + ["compressive_strength_3d", "compressive_strength_7d", "compressive_strength_28d"],
        filter_col = "compressive_strength_3d",
        growth_ops = [
            ("compressive_strength_3d", "compressive_strength_7d", "growth_7d"),
            ("compressive_strength_7d", "compressive_strength_28d", "growth_28d"),
        ],
        model_cols = _BASE_CPII + ["growth_7d", "growth_28d", "compressive_strength_3d", "compressive_strength_7d"],
    ),
    ("cpiii", 7): PipelineCfg(
        raw_cols   = _BASE_CPIII + ["resistance_3d", "resistance_7d"],
        filter_col = "resistance_3d",
        growth_ops = [("resistance_3d", "resistance_7d", "growth_7d")],
        model_cols = _BASE_CPIII + ["resistance_3d", "growth_7d"],
    ),
    ("cpiii", 28): PipelineCfg(
        raw_cols   = _BASE_CPIII + ["resistance_3d", "resistance_7d", "resistance_28d"],
        filter_col = "resistance_7d",
        growth_ops = [("resistance_7d", "resistance_28d", "growth_28d")],
        model_cols = _BASE_CPIII + ["resistance_3d", "resistance_7d", "growth_28d"],
    ),
    ("cpvari", 3): PipelineCfg(
        raw_cols   = _BASE_CPIII + ["resistance_1d", "resistance_3d"],
        filter_col = "resistance_3d",
        growth_ops = [("resistance_1d", "resistance_3d", "growth_3d")],
        model_cols = _BASE_CPIII + ["growth_3d", "resistance_1d"],
    ),
    ("cpvari", 7): PipelineCfg(
        raw_cols   = _BASE_CPIII + ["resistance_1d", "resistance_3d", "resistance_7d"],
        filter_col = "resistance_3d",
        growth_ops = [("resistance_3d", "resistance_7d", "growth_7d")],
        model_cols = _BASE_CPIII + ["growth_7d", "resistance_1d", "resistance_3d"],
    ),
    ("cpiv", 3): PipelineCfg(
        raw_cols   = _BASE_CPIV,
        filter_col = None,
        growth_ops = [],
        model_cols = _BASE_CPIV,
    ),
    ("cpiv", 7): PipelineCfg(
        raw_cols   = _BASE_CPIV + ["resistance_3d", "resistance_7d"],
        filter_col = "resistance_3d",
        growth_ops = [("resistance_3d", "resistance_7d", "growth_7d")],
        model_cols = _BASE_CPIV + ["resistance_3d", "growth_7d"],
    ),
    ("cpiv", 28): PipelineCfg(
        raw_cols   = _BASE_CPIV + ["resistance_3d", "resistance_7d", "resistance_28d"],
        filter_col = "resistance_7d",
        growth_ops = [("resistance_7d", "resistance_28d", "growth_28d")],
        model_cols = _BASE_CPIV + ["resistance_3d", "resistance_7d", "growth_28d"],
    ),
    ("cpiiz32rs", 3): PipelineCfg(
        raw_cols   = _BASE_CPIV,
        filter_col = None,
        growth_ops = [],
        model_cols = _BASE_CPIV,
    ),
    ("cpiiz32rs", 7): PipelineCfg(
        raw_cols   = _BASE_CPIV + ["resistance_3d", "resistance_7d"],
        filter_col = "resistance_3d",
        growth_ops = [("resistance_3d", "resistance_7d", "growth_7d")],
        model_cols = _BASE_CPIV + ["resistance_3d", "growth_7d"],
    ),
    ("cpiiz32rs", 28): PipelineCfg(
        raw_cols   = _BASE_CPIV + ["resistance_3d", "resistance_7d", "resistance_28d"],
        filter_col = "resistance_7d",
        growth_ops = [("resistance_7d", "resistance_28d", "growth_28d")],
        model_cols = _BASE_CPIV + ["resistance_3d", "resistance_7d", "growth_28d"],
    ),
    ("cpiiipec", 3): PipelineCfg(
        raw_cols   = _BASE_CPII + ["compressive_strength_1d", "compressive_strength_3d"],
        filter_col = "compressive_strength_1d",
        growth_ops = [("compressive_strength_1d", "compressive_strength_3d", "growth_3d")],
        model_cols = _BASE_CPII + ["growth_3d", "compressive_strength_1d"],
    ),
    ("cpiiipec", 7): PipelineCfg(
        raw_cols   = _BASE_CPII + ["compressive_strength_3d", "compressive_strength_7d"],
        filter_col = "compressive_strength_3d",
        growth_ops = [("compressive_strength_3d", "compressive_strength_7d", "growth_7d")],
        model_cols = _BASE_CPII + ["growth_7d", "compressive_strength_3d"],
    ),
    ("cpiiipec", 28): PipelineCfg(
        raw_cols   = _BASE_CPII + ["compressive_strength_3d", "compressive_strength_7d", "compressive_strength_28d"],
        filter_col = "compressive_strength_3d",
        growth_ops = [
            ("compressive_strength_3d", "compressive_strength_7d", "growth_7d"),
            ("compressive_strength_7d", "compressive_strength_28d", "growth_28d"),
        ],
        model_cols = _BASE_CPII + ["growth_7d", "growth_28d", "compressive_strength_3d", "compressive_strength_7d"],
    ),
}

# Model file suffix and PI tag metadata per cement type
_MODEL_SUFFIX = {
    "cpiif":     "cpii",
    "cpiii":     "cpiii",
    "cpvari":    "cpv",
    "cpiv":      "cpiv",
    "cpiiz32rs": "cpii",
    "cpiiipec":  "cpiiipec_pec",
}
_PI_UNIT = {
    "cpiif":     "QXR",
    "cpiii":     "QXR",
    "cpvari":    "QXR",
    "cpiv":      "PEC",
    "cpiiz32rs": "PEC",
    "cpiiipec":  "PEC",
}
_PI_TAG_TYPE = {
    "cpiif":     "CPIIF",
    "cpiii":     "CPIII",
    "cpvari":    "CPVARI",
    "cpiv":      "CPIV",
    "cpiiz32rs": "CPIIZ32RS",
    "cpiiipec":  "CPIII",
}


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------
def fetch_data(tags: list[str], names: list[str], time_range: str) -> pd.DataFrame:
    anchor = recorded_range(tags[0], time_range, "*")
    timestamps = [item["Timestamp"] for item in anchor["Items"]]

    rows = []
    for ts in timestamps:
        logger.debug("fetching %d tags at %s", len(tags), ts)
        rows.append([tag_value_at(tag, ts) for tag in tags])

    df = pd.DataFrame(rows, columns=names)
    df.insert(0, "timestamp", timestamps)
    df.columns = df.columns.str.lower().str.replace(" ", "_", regex=False)
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def prepare_features(df: pd.DataFrame, tipo: str, day: int) -> pd.DataFrame:
    cfg = PIPELINE[(tipo, day)]

    data = df[["timestamp"] + cfg.raw_cols].copy()

    if cfg.filter_col:
        data = data[data[cfg.filter_col].notna()]

    for col_a, col_b, out in cfg.growth_ops:
        data = data.assign(**{out: data[col_b] - data[col_a]})

    data = data[["timestamp"] + cfg.model_cols].ffill().dropna()
    logger.info("%s %dd: %d usable rows", tipo, day, len(data))
    return data


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def score_record(record: dict, day: int, tipo: str) -> tuple[float, str]:
    suffix   = _MODEL_SUFFIX[tipo]
    model_path = MODELS_DIR / f"model_resistance_{day}d_{suffix}.joblib"

    model  = joblib.load(model_path)
    cfg    = PIPELINE[(tipo, day)]
    timestamp = record["timestamp"]

    X = pd.DataFrame([{k: record[k] for k in cfg.model_cols}])
    prediction = float(model.predict(X)[0])

    logger.info("scored %s %dd @ %s => %.2f MPa", tipo, day, timestamp, prediction)
    return prediction, timestamp


def write_prediction(tipo: str, day: int, value: float, timestamp: str) -> None:
    unit = _PI_UNIT[tipo]
    tag_type = _PI_TAG_TYPE[tipo]
    tag = f"{unit}_CIM_EXP_{tag_type}.R{day}D_Predict"
    payload = {"Timestamp": timestamp, "Value": round(value, 2)}
    write_tag(tag, payload)
    logger.info("wrote %s = %.2f @ %s", tag, value, timestamp)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def validate_and_score(
    df: pd.DataFrame,
    schema,
    day: int,
    tipo: str,
) -> None:
    data = prepare_features(df, tipo, day)
    records = data.to_dict("records")

    scored = 0
    for record in records:
        if not schema.validate(record):
            logger.warning("validation failed %s %dd: %s", tipo, day, schema.errors)
            continue
        value, timestamp = score_record(record, day, tipo)
        write_prediction(tipo, day, value, timestamp)
        scored += 1

    logger.info("%s %dd: %d/%d records scored", tipo, day, scored, len(records))
