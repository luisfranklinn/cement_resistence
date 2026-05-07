# Dataset

## Description

Industrial dataset from a Brazilian cement plant producing **CP II-F** (Portland Composite Cement).  
Data collected via OSIsoft PI System Web API over the period **January 2022 – April 2026**.

## Variables

| Column | Description | Unit | Source |
|---|---|---|---|
| `timestamp` | Sample collection timestamp | ISO 8601 | PI System |
| `na2o` | Sodium oxide | % | X-ray fluorescence |
| `fe2o3` | Iron(III) oxide | % | X-ray fluorescence |
| `cao` | Calcium oxide | % | X-ray fluorescence |
| `so3` | Sulfur trioxide | % | X-ray fluorescence |
| `blaine` | Blaine fineness | cm²/g | Blaine apparatus |
| `sio2` | Silicon dioxide | % | X-ray fluorescence |
| `pf` | Loss on ignition | % | Gravimetry |
| `#400` | Residue on #400 sieve | % | Sieve analysis |
| `r.i` | Insoluble residue | % | Chemical analysis |
| `mgo` | Magnesium oxide | % | X-ray fluorescence |
| `cs_1d` | Compressive strength at 1 day | MPa | EN 196-1 |
| `cs_3d` | Compressive strength at 3 days | MPa | EN 196-1 |
| `cs_7d` | Compressive strength at 7 days | MPa | EN 196-1 |
| `cs_28d` | Compressive strength at 28 days | MPa | EN 196-1 |

## Derived features (computed in `src/data_utils.py`)

| Feature | Formula | Physical meaning |
|---|---|---|
| `lsf` | `cao / (2.8·sio2 + 0.65·fe2o3)` | Lime Saturation Factor — controls C3S formation |
| `sm` | `sio2 / fe2o3` | Silica Modulus — silicate-to-flux ratio |
| `blaine_so3` | `blaine × so3` | Fineness–sulfate interaction (early hydration rate) |
| `growth_1d_3d` | `cs_3d − cs_1d` | Early strength gain (valid for 7d/28d prediction only) |
| `growth_3d_7d` | `cs_7d − cs_3d` | Mid-range strength gain (valid for 28d prediction only) |

## Availability

The raw data is proprietary and cannot be distributed.  
A **synthetic dataset** with the same statistical properties is provided in `data/synthetic_cpiif.csv` for reproducibility purposes.  
Contact the authors for access to the original industrial data.

## Statistics (original dataset)

| Split | Rows |
|---|---|
| Historical (2022–2025) | 852 |
| Recent (Jan–Apr 2026) | 64 |
| **Total (after dedup)** | **916** |
| Usable for 3d model | 849 |
| Usable for 7d model | 849 |
| Usable for 28d model | 849 |
