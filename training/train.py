"""
Retraining pipeline for cement compressive strength prediction models.

Usage
-----
# Fetch fresh data from PI (last 18 months) and retrain:
    python -m training.train --source pi --start t-540d

# Retrain from existing CSV files:
    python -m training.train --source csv --csv-dir C:/AI_RESISTANCE/PRODUCAO/CSV_PI

Both modes train all configured (tipo, horizon) combinations, print a
metrics table, and save fitted models to models/.
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# ── repo root on sys.path so relative imports work when run as __main__ ──────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import MODELS_DIR
from src.pipeline import PIPELINE, _MODEL_SUFFIX

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Training run definitions
# (tipo, day): which combinations to train and what the target column is
# ---------------------------------------------------------------------------
TARGET_COL: dict[tuple[str, int], str] = {
    ("cpiif",    3):  "compressive_strength_3d",
    ("cpiif",    7):  "compressive_strength_7d",
    ("cpiif",    28): "compressive_strength_28d",
    ("cpiii",    7):  "resistance_7d",
    ("cpiii",    28): "resistance_28d",
    ("cpvari",   3):  "resistance_3d",
    ("cpvari",   7):  "resistance_7d",
    ("cpiv",     3):  "resistance_3d",
    ("cpiv",     7):  "resistance_7d",
    ("cpiv",     28): "resistance_28d",
    ("cpiiipec", 3):  "compressive_strength_3d",
    ("cpiiipec", 7):  "compressive_strength_7d",
    ("cpiiipec", 28): "compressive_strength_28d",
}

# PI tag configs per tipo (mirrors main.py, extended with all strength tags)
_TAGS: dict[str, dict] = {
    "cpiif": {
        "TAGS": [
            "QXR_RaioX.CIM_EXP_CPIIF.Na2O",  "QXR_RaioX.CIM_EXP_CPIIF.Fe2O3",
            "QXR_RaioX.CIM_EXP_CPIIF.CaO",   "QXR_RaioX.CIM_EXP_CPIIF.SO3",
            "QXR_CIM_EXP_CPIIF.BLAINE",       "QXR_RaioX.CIM_EXP_CPIIF.SiO2",
            "QXR_CIM_EXP_CPIIF.PF",           "QXR_CIM_EXP_CPIIF.#325",
            "QXR_CIM_EXP_CPIIF.R.I",          "QXR_RaioX.CIM_EXP_CPIIF.MgO",
            "QXR_CIM_EXP_CPIIF.R1D",          "QXR_CIM_EXP_CPIIF.R3D",
            "QXR_CIM_EXP_CPIIF.R7D",          "QXR_CIM_EXP_CPIIF.R28D",
        ],
        "NAMES": [
            "Na2O", "Fe2O3", "CAO", "SO3", "BLAINE", "SiO2", "PF", "#400", "R.I", "MgO",
            "Compressive_Strength_1d", "Compressive_Strength_3d",
            "Compressive_Strength_7d", "Compressive_Strength_28d",
        ],
    },
    "cpiii": {
        "TAGS": [
            "QXR_RaioX.CIM_EXP_CPIII.SiO2",  "QXR_RaioX.CIM_EXP_CPIII.Al2O3",
            "QXR_RaioX.CIM_EXP_CPIII.Fe2O3", "QXR_RaioX.CIM_EXP_CPIII.CaO",
            "QXR_RaioX.CIM_EXP_CPIII.MgO",   "QXR_RaioX.CIM_EXP_CPIII.SO3",
            "QXR_RaioX.CIM_EXP_CPIII.Na2O",  "QXR_RaioX.CIM_EXP_CPIII.K2O",
            "QXR_CIM_EXP_CPIII.R.I",         "QXR_CIM_EXP_CPIII.PF",
            "QXR_CIM_EXP_CPIII.BLAINE",      "QXR_CIM_EXP_CPIII.#400",
            "QXR_CIM_EXP_CPIII.R3D",         "QXR_CIM_EXP_CPIII.R7D",
            "QXR_CIM_EXP_CPIII.R28D",
        ],
        "NAMES": [
            "SiO2", "Al2O3", "Fe2O3", "CAO", "MgO", "SO3", "Na2O", "K2O",
            "R.I", "PF", "BLAINE", "#400",
            "Resistance 3d", "Resistance 7d", "Resistance 28d",
        ],
    },
    "cpvari": {
        "TAGS": [
            "QXR_RaioX.CIM_EXP_CPVARI.SiO2",  "QXR_RaioX.CIM_EXP_CPVARI.Al2O3",
            "QXR_RaioX.CIM_EXP_CPVARI.Fe2O3", "QXR_RaioX.CIM_EXP_CPVARI.CaO",
            "QXR_RaioX.CIM_EXP_CPVARI.MgO",   "QXR_RaioX.CIM_EXP_CPVARI.SO3",
            "QXR_RaioX.CIM_EXP_CPVARI.Na2O",  "QXR_RaioX.CIM_EXP_CPVARI.K2O",
            "QXR_CIM_EXP_CPVARI.R.I",         "QXR_CIM_EXP_CPVARI.PF",
            "QXR_CIM_EXP_CPVARI.BLAINE",      "QXR_CIM_EXP_CPVARI.#400",
            "QXR_CIM_EXP_CPVARI.R1D",         "QXR_CIM_EXP_CPVARI.R3D",
            "QXR_CIM_EXP_CPVARI.R7D",
        ],
        "NAMES": [
            "SiO2", "Al2O3", "Fe2O3", "CAO", "MgO", "SO3", "Na2O", "K2O",
            "R.I", "PF", "BLAINE", "#400",
            "Resistance 1d", "Resistance 3d", "Resistance 7d",
        ],
    },
    "cpiv": {
        "TAGS": [
            "PEC_RaioX.CIM_EXP_CPIV.SiO2",  "PEC_RaioX.CIM_EXP_CPIV.Al2O3",
            "PEC_RaioX.CIM_EXP_CPIV.Fe2O3", "PEC_RaioX.CIM_EXP_CPIV.CaO",
            "PEC_RaioX.CIM_EXP_CPIV.MgO",   "PEC_RaioX.CIM_EXP_CPIV.SO3",
            "PEC_RaioX.CIM_EXP_CPIV.Na2O",  "PEC_RaioX.CIM_EXP_CPIV.K2O",
            "PEC_CIM_EXP_CPIV.R.I",         "PEC_CIM_EXP_CPIV.PF",
            "PEC_CIM_EXP_CPIV.BLAINE",      "PEC_CIM_EXP_CPIV.#325",
            "PEC_CIM_EXP_CPIV.R3D",         "PEC_CIM_EXP_CPIV.R7D",
            "PEC_CIM_EXP_CPIV.R28D",
        ],
        "NAMES": [
            "SiO2", "Al2O3", "Fe2O3", "CAO", "MgO", "SO3", "Na2O", "K2O",
            "R.I", "PF", "BLAINE", "#325",
            "Resistance 3d", "Resistance 7d", "Resistance 28d",
        ],
    },
    "cpiiipec": {
        "TAGS": [
            "PEC_RaioX.CIM_EXP_CPIII.Na2O",  "PEC_RaioX.CIM_EXP_CPIII.Fe2O3",
            "PEC_RaioX.CIM_EXP_CPIII.CaO",   "PEC_RaioX.CIM_EXP_CPIII.SO3",
            "PEC_CIM_EXP_CPIII.BLAINE",       "PEC_RaioX.CIM_EXP_CPIII.SiO2",
            "PEC_CIM_EXP_CPIII.PF",           "PEC_CIM_EXP_CPIII.#400",
            "PEC_CIM_EXP_CPIII.R.I",          "PEC_RaioX.CIM_EXP_CPIII.MgO",
            "PEC_CIM_EXP_CPIII.R1D",          "PEC_CIM_EXP_CPIII.R3D",
            "PEC_CIM_EXP_CPIII.R7D",          "PEC_CIM_EXP_CPIII.R28D",
        ],
        "NAMES": [
            "Na2O", "Fe2O3", "CAO", "SO3", "BLAINE", "SiO2", "PF", "#400", "R.I", "MgO",
            "Compressive_Strength_1d", "Compressive_Strength_3d",
            "Compressive_Strength_7d", "Compressive_Strength_28d",
        ],
    },
}

# CSV prefix per tipo (matches filenames in PRODUCAO/CSV_PI/)
_CSV_PREFIX: dict[str, str] = {
    "cpiif":    "cpii",
    "cpiii":    "cpiii",
    "cpvari":   "cpv_ari",
    "cpiv":     "cpiv",
    "cpiiipec": "cpiiipec",
}

# Rename map for raw CSV exports (PI tag label → clean column name)
_RENAME_MAP = {
    "Resistance 1d": "resistance_1d", "Resistance 3d": "resistance_3d",
    "Resistance 7d": "resistance_7d", "Resistance 28d": "resistance_28d",
    "Compressive Strength 1d": "compressive_strength_1d",
    "Compressive Strength 3d": "compressive_strength_3d",
    "Compressive Strength 7d": "compressive_strength_7d",
    "Compressive Strength 28d": "compressive_strength_28d",
    "Compressive_Strength_1d": "compressive_strength_1d",
    "Compressive_Strength_3d": "compressive_strength_3d",
    "Compressive_Strength_7d": "compressive_strength_7d",
    "Compressive_Strength_28d": "compressive_strength_28d",
    "Na2O": "na2o", "CAO": "cao", "CaO": "cao",
    "Fe2O3": "fe2o3", "SiO2": "sio2", "SO3": "so3",
    "K2O": "k2o", "Al2O3": "al2o3", "MgO": "mgo",
    "BLAINE": "blaine", "PF": "pf", "R.I": "r.i",
    "#325": "#400",
}

# GBM hyper-parameter search space (kept small for reasonable runtime)
_GBM_GRID = {
    "gradientboostingregressor__n_estimators":     [300, 500],
    "gradientboostingregressor__max_depth":        [3, 4],
    "gradientboostingregressor__learning_rate":    [0.05, 0.1],
    "gradientboostingregressor__subsample":        [0.8],
    "gradientboostingregressor__min_samples_leaf": [3],
}

CV_OUTER = KFold(n_splits=5, shuffle=True, random_state=42)
CV_INNER = KFold(n_splits=3, shuffle=True, random_state=42)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace(r"[\n\r]+", " ", regex=True)
        .str.strip()
    )
    df = df.rename(columns=_RENAME_MAP)
    df.columns = df.columns.str.lower().str.replace(" ", "_", regex=False)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    for col in df.columns:
        if col != "timestamp":
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )
    if "timestamp" in df.columns:
        df = df.drop_duplicates(subset="timestamp").reset_index(drop=True)
    return df


def load_from_csv(csv_dir: Path, tipo: str) -> pd.DataFrame:
    prefix = _CSV_PREFIX[tipo]
    files = sorted(csv_dir.glob(f"{prefix}*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSVs matching '{prefix}*.csv' in {csv_dir}")
    parts = [pd.read_csv(f) for f in files]
    logger.info("%s: loaded %d CSV(s) → %d rows", tipo, len(files), sum(len(p) for p in parts))
    return _clean_df(pd.concat(parts, ignore_index=True))


def fetch_from_pi(tipo: str, start: str, end: str) -> pd.DataFrame:
    from src.pipeline import fetch_data
    cfg = _TAGS[tipo]
    logger.info("%s: fetching from PI [%s → %s]", tipo, start, end)
    return fetch_data(cfg["TAGS"], cfg["NAMES"], start)


# ---------------------------------------------------------------------------
# Feature engineering for training (keeps target column)
# ---------------------------------------------------------------------------
def prepare_training_data(
    df: pd.DataFrame, tipo: str, day: int
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    cfg    = PIPELINE[(tipo, day)]
    target = TARGET_COL[(tipo, day)]

    need = ["timestamp"] + list(dict.fromkeys(cfg.raw_cols + [target]))
    available = [c for c in need if c in df.columns]
    missing   = set(need) - set(available)
    if missing:
        raise KeyError(f"{tipo} {day}d: missing columns {missing}")

    data = df[available].copy()

    if cfg.filter_col and cfg.filter_col in data.columns:
        data = data[data[cfg.filter_col].notna()]

    for col_a, col_b, out in cfg.growth_ops:
        data = data.assign(**{out: data[col_b] - data[col_a]})

    keep = list(dict.fromkeys(cfg.model_cols + [target]))
    data = data[keep].ffill().dropna()

    X = data[cfg.model_cols].to_numpy(dtype=float)
    y = data[target].to_numpy(dtype=float)
    return X, y, cfg.model_cols


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------
def fit_model(X: np.ndarray, y: np.ndarray) -> GridSearchCV:
    pipe = make_pipeline(StandardScaler(), GradientBoostingRegressor(random_state=42))
    gs   = GridSearchCV(pipe, _GBM_GRID, cv=CV_INNER, scoring="r2", n_jobs=-1, refit=True)
    gs.fit(X, y)
    return gs


def evaluate_cv(model, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
    cv_res = cross_validate(
        model, X, y, cv=CV_OUTER, n_jobs=-1,
        scoring={"r2": "r2", "mae": "neg_mean_absolute_error",
                 "rmse": "neg_mean_squared_error"},
    )
    return {
        "r2":   float(cv_res["test_r2"].mean()),
        "r2_std": float(cv_res["test_r2"].std()),
        "mae":  float(-cv_res["test_mae"].mean()),
        "rmse": float(np.sqrt(-cv_res["test_rmse"].mean())),
        "n":    len(y),
    }


def save_model(model, tipo: str, day: int) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = _MODEL_SUFFIX[tipo]
    path   = MODELS_DIR / f"model_resistance_{day}d_{suffix}.joblib"
    joblib.dump(model.best_estimator_, path)
    return path


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------
def train_all(source: str, start: str, end: str, csv_dir: Path | None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    rows = []
    datasets: dict[str, pd.DataFrame] = {}

    for tipo in _TAGS:
        try:
            if source == "csv":
                datasets[tipo] = load_from_csv(csv_dir, tipo)
            else:
                datasets[tipo] = fetch_from_pi(tipo, start, end)
        except Exception as exc:
            logger.warning("Skipping %s — data load failed: %s", tipo, exc)

    print(f"\n{'Tipo':<12} {'Horizon':<8} {'N':>5} {'R²':>6} {'±':>5} {'MAE':>7} {'RMSE':>7}  Model")
    print("─" * 75)

    for (tipo, day), target in TARGET_COL.items():
        if tipo not in datasets:
            continue
        df = datasets[tipo]
        try:
            X, y, feat_names = prepare_training_data(df, tipo, day)
        except (KeyError, ValueError) as exc:
            logger.warning("  %s %dd: skipped — %s", tipo, day, exc)
            continue

        if len(y) < 20:
            logger.warning("  %s %dd: only %d rows, skipping", tipo, day, len(y))
            continue

        logger.info("  %s %dd: %d samples, %d features → fitting…", tipo, day, len(y), X.shape[1])
        gs      = fit_model(X, y)
        metrics = evaluate_cv(gs, X, y)
        path    = save_model(gs, tipo, day)

        print(
            f"{tipo:<12} {day}d      {metrics['n']:>5}  "
            f"{metrics['r2']:>6.3f} {metrics['r2_std']:>5.3f} "
            f"{metrics['mae']:>7.3f} {metrics['rmse']:>7.3f}  {path.name}"
        )
        rows.append({"tipo": tipo, "day": day, **metrics, "model": path.name})

    print(f"\n{len(rows)} model(s) saved to {MODELS_DIR}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=["pi", "csv"], default="pi",
                   help="Data source: PI Web API (default) or local CSVs")
    p.add_argument("--start",   default="t-540d",
                   help="PI start time (default: t-540d, i.e. ~18 months)")
    p.add_argument("--end",     default="*",
                   help="PI end time (default: now)")
    p.add_argument("--csv-dir", type=Path, default=None,
                   help="Directory with CSV files (required when --source csv)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.source == "csv" and args.csv_dir is None:
        print("Error: --csv-dir is required when --source csv", file=sys.stderr)
        sys.exit(1)
    train_all(args.source, args.start, args.end, args.csv_dir)
