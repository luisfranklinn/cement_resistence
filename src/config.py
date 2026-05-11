from pathlib import Path
from os import getenv
from dotenv import load_dotenv

load_dotenv()

BASE_DIR   = Path(getenv("APP_BASE_DIR", r"C:\AI_RESISTANCE\PRODUCAO"))
MODELS_DIR = BASE_DIR / "Models"
LOGS_DIR   = BASE_DIR / "LOGS"

PI_HOST = getenv("PI_HOST", "")
PI_USER = getenv("PI_USER", "")
PI_PASS = getenv("PI_PASS", "")
