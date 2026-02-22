import os
from pathlib import Path

# Project structure
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"

# Expected environment versions for validation
EXPECTED_ENV = {
    "python": "3.10.x",
    "numpy": "1.26.4",
    "scipy": "1.12.0",
    "scikit-learn": "1.4.2",
    "pandas": "2.2.1",
    "joblib": "1.4.2"
}
