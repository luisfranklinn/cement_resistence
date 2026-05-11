import logging
import sys
from datetime import datetime

from src.config import LOGS_DIR
from src.pipeline import fetch_data, validate_and_score
from src.schemas import (
    schema_3d_cpii, schema_7d_cpii, schema_28d_cpii,
    schema_7d_cpiii, schema_28d_cpiii,
    schema_3d_cpv, schema_7d_cpv,
    schema_3d_cpiv, schema_7d_cpiv, schema_28d_cpiv,
    schema_3d_cpiiz32rs, schema_7d_cpiiz32rs, schema_28d_cpiiz32rs,
    schema_3d_cpiii_pec, schema_7d_cpiii_pec, schema_28d_cpiii_pec,
)

# ---------------------------------------------------------------------------
# PI tag configuration per cement type
# TAGS: PI tag paths; NAMES: column names in the DataFrame
# ---------------------------------------------------------------------------
TAGS_CPII = {
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
}

TAGS_CPIII = {
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
}

TAGS_CPV = {
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
}

TAGS_CPIV = {
    "TAGS": [
        "PEC_RaioX.CIM_EXP_CPIV.SiO2",  "PEC_RaioX.CIM_EXP_CPIV.Al2O3",
        "PEC_RaioX.CIM_EXP_CPIV.Fe2O3", "PEC_RaioX.CIM_EXP_CPIV.CaO",
        "PEC_RaioX.CIM_EXP_CPIV.MgO",   "PEC_RaioX.CIM_EXP_CPIV.SO3",
        "PEC_RaioX.CIM_EXP_CPIV.Na2O",  "PEC_RaioX.CIM_EXP_CPIV.K2O",
        "PEC_CIM_EXP_CPIV.R.I",         "PEC_CIM_EXP_CPIV.PF",
        "PEC_CIM_EXP_CPIV.BLAINE",      "PEC_CIM_EXP_CPIV.#325",
        "PEC_CIM_EXP_CPIV.R1D",         "PEC_CIM_EXP_CPIV.R3D",
        "PEC_CIM_EXP_CPIV.R7D",         "PEC_CIM_EXP_CPIV.R28D",
    ],
    "NAMES": [
        "SiO2", "Al2O3", "Fe2O3", "CAO", "MgO", "SO3", "Na2O", "K2O",
        "R.I", "PF", "BLAINE", "#325",
        "Resistance 1d", "Resistance 3d", "Resistance 7d", "Resistance 28d",
    ],
}

TAGS_CPIII_PEC = {
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
}


def _setup_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{datetime.today().strftime('%Y-%m-%d_%H-%M')}.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(levelname)s ===> %(asctime)s ===> %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def run_pipeline() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Pipeline started")

    logger.info("Fetching CPIII-F (QXR)")
    cpii = fetch_data(TAGS_CPII["TAGS"], TAGS_CPII["NAMES"], "t-45d")
    validate_and_score(cpii, schema_3d_cpii,  3, "cpiif")
    validate_and_score(cpii, schema_7d_cpii,  7, "cpiif")
    validate_and_score(cpii, schema_28d_cpii, 28, "cpiif")

    logger.info("Fetching CPIII (QXR)")
    cpiii = fetch_data(TAGS_CPIII["TAGS"], TAGS_CPIII["NAMES"], "t-45d")
    validate_and_score(cpiii, schema_7d_cpiii,  7,  "cpiii")
    validate_and_score(cpiii, schema_28d_cpiii, 28, "cpiii")

    logger.info("Fetching CPV-ARI (QXR)")
    cpv = fetch_data(TAGS_CPV["TAGS"], TAGS_CPV["NAMES"], "t-15d")
    validate_and_score(cpv, schema_3d_cpv, 3, "cpvari")
    validate_and_score(cpv, schema_7d_cpv, 7, "cpvari")

    logger.info("Fetching CPIV (PEC)")
    cpiv = fetch_data(TAGS_CPIV["TAGS"], TAGS_CPIV["NAMES"], "t-45d")
    validate_and_score(cpiv, schema_3d_cpiv,  3,  "cpiv")
    validate_and_score(cpiv, schema_7d_cpiv,  7,  "cpiv")
    validate_and_score(cpiv, schema_28d_cpiv, 28, "cpiv")

    logger.info("Fetching CPIII-PEC (PEC)")
    cpiii_pec = fetch_data(TAGS_CPIII_PEC["TAGS"], TAGS_CPIII_PEC["NAMES"], "t-45d")
    validate_and_score(cpiii_pec, schema_3d_cpiii_pec,  3,  "cpiiipec")
    validate_and_score(cpiii_pec, schema_7d_cpiii_pec,  7,  "cpiiipec")
    validate_and_score(cpiii_pec, schema_28d_cpiii_pec, 28, "cpiiipec")

    logger.info("Pipeline finished")


if __name__ == "__main__":
    run_pipeline()
