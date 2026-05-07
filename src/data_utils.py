"""
Data loading, cleaning, and feature engineering for CP II-F compressive strength prediction.
Expects CSV files exported from the plant historian with the column naming conventions
described in data/README.md.
"""

import os
import pandas as pd
import numpy as np

RENAME_MAP = {
    "Resistance 1d": "cs_1d", "Compressive_Strength_1d": "cs_1d",
    "Compressive Strength 1d": "cs_1d",
    "Resistance 3d": "cs_3d", "Compressive_Strength_3d": "cs_3d",
    "Compressive Strength 3d": "cs_3d",
    "Resistance 7d": "cs_7d", "Compressive_Strength_7d": "cs_7d",
    "Compressive Strength 7d": "cs_7d",
    "Resistance 28d": "cs_28d", "Compressive_Strength_28d": "cs_28d",
    "Compressive Strength 28d": "cs_28d",
    "Na2O": "na2o", "CAO": "cao", "CaO": "cao", "Fe2O3": "fe2o3",
    "SiO2": "sio2", "SO3": "so3", "K2O": "k2o", "Al2O3": "al2o3",
    "MgO": "mgo", "BLAINE": "blaine", "PF": "pf", "R.I": "r.i",
    "#325": "#400",
}

BASE_FEATURES = ["na2o", "fe2o3", "cao", "so3", "blaine", "sio2", "pf"]
OPT_FEATURES  = ["#400", "r.i", "mgo", "k2o", "al2o3"]


def load_csvs(csv_dir: str, prefix: str = "cpii") -> pd.DataFrame:
    """Load and concatenate historical + recent CSVs for a cement type."""
    suffixes = ["20220101_20251231", "20260101_20260415"]
    parts = []
    for s in suffixes:
        path = os.path.join(csv_dir, f"{prefix}_{s}.csv")
        if os.path.exists(path):
            parts.append(pd.read_csv(path))
    if not parts:
        raise FileNotFoundError(f"No CSVs found for prefix '{prefix}' in {csv_dir}")
    return pd.concat(parts, ignore_index=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, rename, convert to numeric, deduplicate."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace(r"[\n\r]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    df = df.rename(columns=RENAME_MAP)
    df.columns = df.columns.str.lower()
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    cols_num = [c for c in df.columns if c != "timestamp"]
    df = df.assign(**{
        col: pd.to_numeric(
            df[col].astype(str).str.strip().str.replace(",", ".", regex=False),
            errors="coerce",
        )
        for col in cols_num
    })

    if "timestamp" in df.columns:
        df = df.drop_duplicates(subset="timestamp").reset_index(drop=True)
    return df


def add_bogue_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Add Bogue-derived features.
    Uses full formulas when Al2O3 is available, approximate otherwise.
    """
    df = df.copy()
    if "al2o3" in df.columns and df["al2o3"].notna().mean() >= 0.5:
        df = df.assign(
            lsf        = df["cao"] / (2.8 * df["sio2"] + 1.2 * df["al2o3"] + 0.65 * df["fe2o3"]),
            sm         = df["sio2"] / (df["al2o3"] + df["fe2o3"]),
            c3a        = 2.650 * df["al2o3"] - 1.692 * df["fe2o3"],
            blaine_so3 = df["blaine"] * df["so3"],
        )
        return df, ["lsf", "sm", "c3a", "blaine_so3"]
    else:
        df = df.assign(
            lsf        = df["cao"] / (2.8 * df["sio2"] + 0.65 * df["fe2o3"]),
            sm         = df["sio2"] / df["fe2o3"],
            blaine_so3 = df["blaine"] * df["so3"],
        )
        return df, ["lsf", "sm", "blaine_so3"]


def add_growth_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add sequential strength growth features (leakage-free)."""
    df = df.copy()
    for col_a, col_b, name in [
        ("cs_1d", "cs_3d", "growth_1d_3d"),
        ("cs_3d", "cs_7d", "growth_3d_7d"),
        ("cs_7d", "cs_28d", "growth_7d_28d"),
    ]:
        if col_a in df.columns and col_b in df.columns:
            df = df.assign(**{name: df[col_b] - df[col_a]})
    return df


def avail_greedy(
    df: pd.DataFrame,
    candidate_cols: list[str],
    required_cols: list[str] | None = None,
    min_rows: int = 10,
) -> list[str]:
    """
    Greedy feature selection: add a candidate only if it does not reduce
    the usable row count (after dropna) below min_rows.

    This handles the case where two CSVs with complementary column sets are
    merged — a naive notna().sum() > threshold would include mutually-
    exclusive columns, yielding zero rows after dropna.
    """
    working = list(required_cols or [])
    result = []
    for c in candidate_cols:
        if c not in df.columns:
            continue
        if df[working + [c]].dropna().shape[0] >= min_rows:
            working.append(c)
            result.append(c)
    return result


def build_feature_sets(
    df: pd.DataFrame,
    base: list[str],
    opt: list[str],
    derived: list[str],
) -> tuple[dict[str, list[str]], list[str]]:
    """
    Build QUIM and per-horizon feature sets.
    Leakage-free design:
      - 3d: chemistry only (+ cs_1d if available)
      - 7d: chemistry + cs_3d + growth_1d_3d
      - 28d: chemistry + cs_3d + cs_7d + growth_1d_3d + growth_3d_7d
    """
    opt_selected = avail_greedy(df, opt, required_cols=base)
    quim = base + opt_selected + avail_greedy(df, derived, required_cols=base + opt_selected)
    feat = {
        "3d":  quim + avail_greedy(df, ["cs_1d"], required_cols=quim),
        "7d":  quim + avail_greedy(df, ["cs_1d", "cs_3d", "growth_1d_3d"], required_cols=quim),
        "28d": quim + avail_greedy(
            df, ["cs_1d", "cs_3d", "cs_7d", "growth_1d_3d", "growth_3d_7d"],
            required_cols=quim,
        ),
    }
    return feat, quim


def prepare_dataset(csv_dir: str, prefix: str = "cpii") -> tuple[pd.DataFrame, list[str]]:
    """Full pipeline: load → clean → growth → Bogue → feature sets."""
    raw = load_csvs(csv_dir, prefix)
    df  = clean(raw)
    df  = add_growth_features(df)
    df, derived = add_bogue_features(df)
    feat, quim = build_feature_sets(df, BASE_FEATURES, OPT_FEATURES, derived)
    return df, feat, quim, derived
