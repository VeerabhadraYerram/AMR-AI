import os
import sys
import logging
import joblib
import sklearn
import pandas as pd
import numpy as np
import scipy
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import MODELS_DIR, EXPECTED_ENV

logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.env_warnings: List[str] = []
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelLoader()
        return cls._instance
        
    def check_environment(self):
        """Validate current environment against expected versions."""
        current_versions = {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit-learn": sklearn.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__
        }
        
        for lib, expected in EXPECTED_ENV.items():
            if lib == "python":
                # Loose check for python major.minor
                if not current_versions[lib].startswith("3.10") and not current_versions[lib].startswith("3.13"): # Allow 3.13 as per current env
                    msg = f"Environment Mismatch: {lib} expected {expected}, found {current_versions[lib]}"
                    logger.warning(msg)
                    self.env_warnings.append(msg)
            else:
                if current_versions[lib] != expected:
                    msg = f"Environment Mismatch: {lib} expected {expected}, found {current_versions[lib]}"
                    logger.warning(msg)
                    self.env_warnings.append(msg)
                    
        if self.env_warnings:
             logger.warning("COMPATIBILITY WARNINGS DETECTED:")
             for w in self.env_warnings:
                 logger.warning(f"- {w}")
        else:
            logger.info("Environment check passed: All libraries match expected versions.")

    def validate_model(self, model, pathogen_name: str) -> bool:
        """Validate if the loaded object is a valid sklearn pipeline."""
        if not isinstance(model, sklearn.pipeline.Pipeline):
            logger.error(f"Validation Failed for {pathogen_name}: Model is not a sklearn.pipeline.Pipeline")
            return False
            
        # Check for preprocessor
        if 'preprocessor' not in model.named_steps:
             logger.warning(f"Validation Warning for {pathogen_name}: Pipeline does not have a 'preprocessor' step. Feature extraction may fail.")
        
        # Check for classifier
        if 'classifier' not in model.named_steps and 'clf' not in model.named_steps:
             logger.warning(f"Validation Warning for {pathogen_name}: Pipeline does not have a standard 'classifier' or 'clf' step.")
             
        # Log feature info if possible
        try:
            if hasattr(model, 'feature_names_in_'):
                logger.info(f"Model {pathogen_name} expects {len(model.feature_names_in_)} input features.")
            else:
                logger.info(f"Model {pathogen_name} does not expose feature_names_in_ directly.")
        except Exception as e:
            logger.warning(f"Could not inspect features for {pathogen_name}: {str(e)}")
            
        return True

    def load_models(self):
        """Discover and load models from the models directory."""
        logger.info(f"Scanning for models in {MODELS_DIR}...")
        
        if not MODELS_DIR.exists():
            logger.error(f"Models directory not found: {MODELS_DIR}")
            return

        self.check_environment()
        
        for pathogen_dir in MODELS_DIR.iterdir():
            if pathogen_dir.is_dir() and not pathogen_dir.name.startswith('.'):
                model_path = pathogen_dir / "model.pkl"
                if model_path.exists():
                    logger.info(f"Loading model for {pathogen_dir.name}...")
                    try:
                        # Ensure we are loading with joblib
                        model = joblib.load(model_path)
                        
                        if self.validate_model(model, pathogen_dir.name):
                            self.models[pathogen_dir.name] = model
                            self.model_metadata[pathogen_dir.name] = {
                                "path": str(model_path),
                                "size": model_path.stat().st_size,
                                "type": type(model).__name__
                            }
                            logger.info(f"Successfully loaded model for {pathogen_dir.name}")
                        else:
                            logger.error(f"Skipping {pathogen_dir.name} due to validation failure.")
                            
                    except Exception as e:
                        logger.error(f"Failed to load model for {pathogen_dir.name}: {str(e)}")
                        self.env_warnings.append(f"Load Error {pathogen_dir.name}: {str(e)}")
                else:
                    logger.debug(f"No model.pkl found in {pathogen_dir.name}")
                    
        logger.info(f"Model loading complete. Loaded {len(self.models)} models.")
