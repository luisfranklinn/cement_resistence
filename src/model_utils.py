"""
Model training, evaluation, and visualization utilities.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, GridSearchCV, cross_val_score, cross_val_predict, cross_validate
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


CV_OUTER = KFold(n_splits=5, shuffle=True, random_state=42)
CV_INNER = KFold(n_splits=3, shuffle=True, random_state=42)

GBM_PARAM_GRID = {
    "gradientboostingregressor__n_estimators":  [300, 500],
    "gradientboostingregressor__max_depth":     [3, 4],
    "gradientboostingregressor__learning_rate": [0.05, 0.1],
    "gradientboostingregressor__subsample":     [0.8],
    "gradientboostingregressor__min_samples_leaf": [3],
}


def make_gbm_pipeline() -> GridSearchCV:
    """GBM + StandardScaler with nested GridSearchCV."""
    pipe = make_pipeline(
        StandardScaler(),
        GradientBoostingRegressor(random_state=42),
    )
    return GridSearchCV(
        pipe, GBM_PARAM_GRID,
        cv=CV_INNER, scoring="r2", n_jobs=-1, refit=True,
    )


def make_baseline_pipeline() -> GridSearchCV:
    """Ridge regression baseline (standardized linear model)."""
    pipe = make_pipeline(StandardScaler(), Ridge())
    return GridSearchCV(
        pipe, {"ridge__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
        cv=CV_INNER, scoring="r2", n_jobs=-1, refit=True,
    )


def evaluate(pipeline, X: np.ndarray, y: np.ndarray) -> dict:
    """Nested cross-validation evaluation — returns dict with R², MAE, RMSE."""
    cv_res = cross_validate(
        pipeline, X, y, cv=CV_OUTER, n_jobs=-1,
        scoring={"r2": "r2", "mae": "neg_mean_absolute_error", "rmse": "neg_mean_squared_error"},
    )
    return {
        "r2":   cv_res["test_r2"],
        "mae":  -cv_res["test_mae"],
        "rmse": np.sqrt(-cv_res["test_rmse"]),
    }


def train_and_evaluate(X: np.ndarray, y: np.ndarray, baseline: bool = False) -> dict:
    """Train GBM (and optionally a Ridge baseline), return metrics + fitted model."""
    gs = make_gbm_pipeline()
    metrics = evaluate(gs, X, y)
    gs.fit(X, y)
    result = {
        "model": gs.best_estimator_,
        "params": gs.best_params_,
        **{k: v for k, v in metrics.items()},
    }
    if baseline:
        bl = make_baseline_pipeline()
        bl_metrics = evaluate(bl, X, y)
        result["baseline"] = bl_metrics
    return result


def plot_diagnostics(
    results: dict[str, dict],
    derived_features: list[str],
    title: str = "CP II-F",
    save_path: str | None = None,
) -> plt.Figure:
    """
    3-column diagnostic figure for each horizon:
      col 0 — Predicted vs Actual
      col 1 — Residuals
      col 2 — Feature Importance
    """
    horizons = list(results.keys())
    n = len(horizons)
    fig = plt.figure(figsize=(18, 5 * n))
    fig.suptitle(f"Model Diagnostics — {title}", fontsize=14, fontweight="bold")
    gs = gridspec.GridSpec(n, 3, figure=fig, hspace=0.45, wspace=0.35)

    derived_set = set(derived_features)

    for row, h in enumerate(horizons):
        r      = results[h]
        feat   = r["feat"]
        y_true = r["y"]
        y_pred = cross_val_predict(r["model"], r["X"], y_true, cv=CV_OUTER)
        r2_m   = r["r2"].mean()
        mae_m  = r["mae"].mean()

        # Predicted vs Actual
        ax1 = fig.add_subplot(gs[row, 0])
        vmin = min(y_true.min(), y_pred.min())
        vmax = max(y_true.max(), y_pred.max())
        ax1.scatter(y_true, y_pred, alpha=0.4, s=20, color="#2196F3", edgecolors="none")
        ax1.plot([vmin, vmax], [vmin, vmax], "r--", lw=1.5, label="Ideal")
        ax1.set_xlabel(f"Measured $f_c$ {h} (MPa)")
        ax1.set_ylabel(f"Predicted $f_c$ {h} (MPa)")
        ax1.set_title(f"Predicted vs Measured — {h}\n$R^2$={r2_m:.3f}  MAE={mae_m:.3f} MPa")
        ax1.legend(fontsize=8)

        # Residuals
        ax2 = fig.add_subplot(gs[row, 1])
        res = y_true - y_pred
        ax2.scatter(y_pred, res, alpha=0.4, s=20, color="#FF9800", edgecolors="none")
        ax2.axhline(0,           color="red",  lw=1.5, ls="--")
        ax2.axhline( res.std(),  color="gray", lw=1.0, ls=":")
        ax2.axhline(-res.std(),  color="gray", lw=1.0, ls=":")
        ax2.set_xlabel(f"Predicted $f_c$ {h} (MPa)")
        ax2.set_ylabel("Residual (MPa)")
        ax2.set_title(
            f"Residuals — {h}\n$\\sigma$={res.std():.3f}  bias={res.mean():.3f} MPa"
        )

        # Feature Importance
        ax3 = fig.add_subplot(gs[row, 2])
        imp    = r["model"][-1].feature_importances_
        idx    = np.argsort(imp)
        colors = ["#FF5722" if f in derived_set else "#2196F3"
                  for f in np.array(feat)[idx]]
        ax3.barh(np.array(feat)[idx], imp[idx], color=colors)
        ax3.set_xlabel("Importance")
        ax3.set_title(f"Feature Importance — {h}\n(orange = Bogue-derived)")
        ax3.tick_params(axis="y", labelsize=8)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def performance_table(all_results: dict) -> None:
    """Print a formatted performance table across all cement types and horizons."""
    header = f"{'Cement':<12} {'Horizon':<8} {'R²':>6} {'±':>5} {'MAE (MPa)':>10} {'RMSE (MPa)':>11}"
    print(header)
    print("-" * len(header))
    for ct, data in all_results.items():
        for h, r in data["results"].items():
            print(
                f"{ct:<12} {h:<8} "
                f"{r['r2'].mean():>6.3f} {r['r2'].std():>5.3f} "
                f"{r['mae'].mean():>10.3f} "
                f"{r['rmse'].mean():>11.3f}"
            )
