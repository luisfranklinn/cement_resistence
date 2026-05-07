# CP II-F Compressive Strength Prediction

> **Paper:** *Gradient Boosting with Bogue-Derived Features for Industrial Prediction of Portland Composite Cement Compressive Strength*

Reproducible code and analysis for the paper on ML-based compressive strength prediction of CP II-F cement using industrial PI System data.

---

## Key Results

| Horizon | R² | MAE (MPa) | RMSE (MPa) |
|---------|-----|-----------|------------|
| 3 days  | 0.427 ± 0.059 | 1.099 ± 0.062 | 1.387 ± 0.073 |
| 7 days  | **0.782 ± 0.043** | **0.693 ± 0.045** | 0.892 ± 0.055 |
| 28 days | **0.785 ± 0.037** | **0.940 ± 0.051** | 1.202 ± 0.067 |

*Nested 5×5 cross-validation. GBM + StandardScaler.*

---

## Repository Structure

```
artigo_cpiif/
├── paper/
│   ├── main.tex          ← LaTeX source (Elsevier format)
│   └── references.bib    ← BibTeX bibliography
├── analysis/
│   ├── 01_eda.ipynb          ← Exploratory data analysis
│   ├── 02_model_training.ipynb   ← Full training pipeline
│   └── 03_results_figures.ipynb  ← Figures for the paper
├── src/
│   ├── data_utils.py     ← Loading, cleaning, feature engineering
│   └── model_utils.py    ← GBM pipeline, evaluation, plotting
├── data/
│   └── README.md         ← Dataset description (data not distributed)
├── figures/              ← Generated figures
├── requirements.txt
└── .gitignore
```

---

## Quickstart

```bash
git clone https://github.com/[author]/cpiif-strength-prediction
cd cpiif-strength-prediction
pip install -r requirements.txt
jupyter lab
```

Open `analysis/02_model_training.ipynb` and set `CSV_DIR` to point to your data folder.

---

## Highlights

### 1. Leakage-Free Feature Construction

Previous industrial models used `growth_7d = cs_7d − cs_3d` as a feature to *predict* `cs_7d` — direct target leakage. This work enforces strict temporal ordering:

| Feature | Valid for horizons |
|---|---|
| `cs_1d` | 3d, 7d, 28d |
| `cs_3d`, `growth_1d_3d` | 7d, 28d |
| `cs_7d`, `growth_3d_7d` | 28d only |

### 2. Bogue-Derived Features

Three physically motivated features added to the raw oxide measurements:

| Feature | Formula | Captures |
|---|---|---|
| LSF | `CaO / (2.8·SiO₂ + 0.65·Fe₂O₃)` | Max C₃S potential |
| SM | `SiO₂ / Fe₂O₃` | Silicate/flux ratio |
| blaine×SO₃ | `blaine × SO₃` | Fineness–sulfate interaction |

These contribute ~17% of feature importance in the 3-day model.

### 3. Greedy Compatibility Feature Selection

When multiple CSVs with complementary column sets are merged, naive `notna().sum() > threshold` selects mutually exclusive features, yielding zero rows after `dropna`. Our greedy algorithm prevents this:

```python
def avail_greedy(df, candidates, required=None, min_rows=10):
    working = list(required or [])
    result  = []
    for c in candidates:
        if c not in df.columns:
            continue
        if df[working + [c]].dropna().shape[0] >= min_rows:
            working.append(c)
            result.append(c)
    return result
```

---

## Data

The original dataset is proprietary (industrial plant, Brazil). A synthetic dataset with equivalent statistical properties is available in `data/` for reproducibility.

Contact: luisfranklin200@gmail.com

---

## Citation

```bibtex
@article{franklin2026cpiif,
  author  = {Franklin, Luis},
  title   = {Gradient Boosting with Bogue-Derived Features for Industrial Prediction
             of Portland Composite Cement Compressive Strength},
  journal = {Construction and Building Materials},
  year    = {2026},
  note    = {Under review}
}
```

---

## License

MIT License — see `LICENSE` for details.
