import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.core.loader import ModelLoader
from app.core.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# ── Biological Knowledge Layer ──────────────────────────────────────
# Maps gene families to the antibiotic *classes* they confer resistance to.
# Sources: CARD, ResFinder, CLSI M100, WHO AWaRe.
GENE_ANTIBIOTIC_RELEVANCE: Dict[str, List[str]] = {
    # Beta-lactamases
    "blaNDM":    ["carbapenems", "cephalosporins", "penicillins"],
    "blaOXA_48": ["carbapenems"],
    "blaKPC":    ["carbapenems", "cephalosporins", "penicillins"],
    "blaCTX_M":  ["cephalosporins", "penicillins"],      # ESBL — NOT carbapenems
    "blaSHV":    ["cephalosporins", "penicillins"],
    "blaZ":      ["penicillins"],                         # S. aureus penicillinase — NOT cephems
    "mecA":      ["penicillins", "cephalosporins", "carbapenems"],  # PBP2a — all beta-lactams
    # Quinolone resistance
    "qnrS":      ["fluoroquinolones"],
    "qnrB":      ["fluoroquinolones"],
    "qepA":      ["fluoroquinolones"],
    "gyrA":      ["fluoroquinolones"],
    "gyrA_D87N": ["fluoroquinolones"],
    "aac6Ib_cr": ["aminoglycosides", "fluoroquinolones"],  # Dual activity
    # Aminoglycoside resistance
    "aac6Ib":    ["aminoglycosides"],
    "aac6_aph2": ["aminoglycosides"],
    "aadA":      ["aminoglycosides"],
    "aph":       ["aminoglycosides"],
    "ant":       ["aminoglycosides"],
    # Tetracycline resistance
    "tetA": ["tetracyclines"], "tetB": ["tetracyclines"],
    "tetC": ["tetracyclines"], "tetD": ["tetracyclines"],
    "tetM": ["tetracyclines"], "tet":  ["tetracyclines"],
    # Chloramphenicol / phenicol
    "catA": ["phenicols"], "cmlA": ["phenicols"], "floR": ["phenicols"],
    # Sulfonamide / trimethoprim
    "sul1": ["sulfonamides"], "sul2": ["sulfonamides"],
    # Fosfomycin
    "fosA": ["fosfomycin"], "fosB": ["fosfomycin"],
    # Polymyxin
    "mcr_1": ["polymyxins"],
    # Glycopeptide
    "vanA": ["glycopeptides"],
    # Macrolide / MLS
    "erm": ["macrolides"],
    # Efflux
    "oqxA": ["fluoroquinolones"], "oqxB": ["fluoroquinolones"],
}

# Antibiotic → class mapping (lowercase keys)
ANTIBIOTIC_CLASSES: Dict[str, str] = {
    # Carbapenems
    "meropenem": "carbapenems", "imipenem": "carbapenems", "ertapenem": "carbapenems",
    # Cephalosporins
    "ceftriaxone": "cephalosporins", "cefotaxime": "cephalosporins",
    "ceftazidime": "cephalosporins", "cefepime": "cephalosporins",
    "cefoxitin": "cephalosporins", "cefuroxime": "cephalosporins",
    "cefalothin": "cephalosporins", "cefazolin": "cephalosporins",
    "ceftiofur": "cephalosporins",
    # Penicillins
    "ampicillin": "penicillins", "amoxicillin": "penicillins",
    "ampicillin/sulbactam": "penicillins",
    "amoxicillin/clavulanic acid": "penicillins",
    "piperacillin/tazobactam": "penicillins",
    # Fluoroquinolones
    "ciprofloxacin": "fluoroquinolones", "levofloxacin": "fluoroquinolones",
    "norfloxacin": "fluoroquinolones", "nalidixic acid": "fluoroquinolones",
    # Aminoglycosides
    "gentamicin": "aminoglycosides", "tobramycin": "aminoglycosides",
    "amikacin": "aminoglycosides", "streptomycin": "aminoglycosides",
    # Tetracyclines
    "tetracycline": "tetracyclines", "doxycycline": "tetracyclines",
    # Phenicols
    "chloramphenicol": "phenicols",
    # Sulfonamides
    "sulfamethoxazole": "sulfonamides",
    "trimethoprim/sulfamethoxazole": "sulfonamides",
    "trimethoprim": "sulfonamides",
    # Other
    "aztreonam": "monobactams",
    "fosfomycin": "fosfomycin",
}

# Genes that are KNOWN to confer resistance — override model if it says "Susceptible"
KNOWN_RESISTANCE_GENES = {
    "blaNDM", "blaOXA_48", "blaKPC", "blaCTX_M", "blaSHV", "blaZ",
    "mecA", "qnrS", "qnrB", "qepA", "gyrA", "gyrA_D87N",
    "aac6Ib", "aac6Ib_cr", "aac6_aph2", "aadA", "aph", "ant",
    "tetA", "tetB", "tetC", "tetD", "tetM", "tet",
    "catA", "cmlA", "floR", "sul1", "sul2",
    "mcr_1", "fosA", "fosB", "vanA", "erm",
}

# User-facing gene aliases → model feature names
GENE_ALIASES: Dict[str, List[str]] = {
    "gyrA_D87N": ["gyrA", "gene_gyrA"],   # Map user's gyrA_D87N to model's gene_gyrA
}


class GAARA:
    def __init__(self):
        self.loader = ModelLoader.get_instance()

    def load_feature_importance(self, pathogen: str) -> Dict[str, float]:
        """Load feature importance from CSV if available."""
        try:
            # Map pathogen name to folder name (e.g. "E. coli" -> "e_coli")
            # Currently loader uses keys like "e_coli", "k_pneumoniae"
            # The pathogen arg comes from loader.models.items() keys, so it should match folder names if loader uses folder names.
            # let's assume pathogen arg is the key from loader.models
            
            csv_path = PROJECT_ROOT / "models" / pathogen / "feature_importance.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                # Filter for genes
                df_genes = df[df["feature_type"] == "gene"]
                if not df_genes.empty:
                    return dict(zip(df_genes["feature"], df_genes["model_importance"]))
            return {}
        except Exception as e:
            logger.warning(f"Could not load feature importance for {pathogen}: {e}")
            return {}

    def get_model_features(self, model, pathogen: str) -> List[str]:
        """Extract feature names from the model."""
        try:
            # Try to get features from the classifier step if available and it has feature_names_in_
            if hasattr(model, "feature_names_in_"):
                return list(model.feature_names_in_)
            
            # If it's a pipeline, check the last step (classifier) or specific names
            if hasattr(model, "named_steps"):
                clf = None
                if "classifier" in model.named_steps: clf = model.named_steps["classifier"]
                elif "clf" in model.named_steps: clf = model.named_steps["clf"]
                else: clf = model.steps[-1][1]
                
                if hasattr(clf, "feature_names_in_"):
                     return list(clf.feature_names_in_)
            
            # Additional check: check if first step is transformer with feature names
            if hasattr(model, "steps"):
                 first_step = model.steps[0][1]
                 if hasattr(first_step, "feature_names_in_"):
                      return list(first_step.feature_names_in_)

            logger.warning(f"Could not directly extract feature names for {pathogen}.")
            return []
        except Exception as e:
            logger.error(f"Error extracting features for {pathogen}: {str(e)}")
            return []

    def get_coefficients_map(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Map feature names to their coefficients/importance.
        
        Handles pipelines with ColumnTransformers by extracting
        transformed feature names when there's a length mismatch.
        """
        coef_map = {}
        try:
            clf = model
            preprocessor = None
            
            if hasattr(model, "named_steps"):
                # Extract classifier and preprocessor from pipeline
                if "classifier" in model.named_steps:
                    clf = model.named_steps["classifier"]
                elif "clf" in model.named_steps:
                    clf = model.named_steps["clf"]
                else:
                    clf = model.steps[-1][1]
                
                if "preprocessor" in model.named_steps:
                    preprocessor = model.named_steps["preprocessor"]
            
            coefs = None
            if hasattr(clf, "coef_"):
                coefs = clf.coef_[0] if clf.coef_.ndim > 1 else clf.coef_
            elif hasattr(clf, "feature_importances_"):
                coefs = clf.feature_importances_
            
            if coefs is None:
                return coef_map
            
            # Try direct match with provided feature names
            if len(coefs) == len(feature_names):
                return dict(zip(feature_names, coefs))
            
            # Length mismatch: try to get transformed feature names from preprocessor
            if preprocessor is not None and hasattr(preprocessor, "get_feature_names_out"):
                try:
                    transformed_names = list(preprocessor.get_feature_names_out())
                    if len(coefs) == len(transformed_names):
                        logger.info(f"Using transformed feature names from preprocessor ({len(transformed_names)} features)")
                        return dict(zip(transformed_names, coefs))
                except Exception as e:
                    logger.warning(f"Could not get transformed feature names: {e}")
            
            logger.warning(f"Coefficient length mismatch: {len(coefs)} coefs vs {len(feature_names)} features")
            
        except Exception as e:
            logger.error(f"Error mapping coefficients: {str(e)}")
        
        return coef_map

    def calculate_coverage_weight(self, expected_features: List[str], gene_presence: Dict[str, int]) -> float:
        """
        Calculate weight based on how many input genes are covered by the model.
        Weight = Base(1.0) + (Scaling(2.0) * CoverageRatio)
        """
        if not expected_features:
            return 1.0
            
        # Filter features that are genes
        model_genes = [f.replace("gene_", "") for f in expected_features if f.startswith("gene_")]
        
        if not model_genes:
            return 1.0
            
        # Count how many of the user's provided genes are known to this model
        # We only care about genes the user actually Has (value=1) or explicitly set to 0.
        # Actually, coverage should be: "Of the genes the user has, how many does this model know about?"
        # If user has blaNDM, and model doesn't know blaNDM, that model is less relevant.
        
        user_genes_present = [g for g, v in gene_presence.items() if v == 1]
        if not user_genes_present:
            return 1.0
            
        covered_count = sum(1 for g in user_genes_present if g in model_genes)
        coverage_ratio = covered_count / len(user_genes_present)
        
        # Base weight 1.0, plus up to 2.0 bonus for full coverage
        return 1.0 + (2.0 * coverage_ratio)

    @staticmethod
    def is_gene_relevant(gene_name: str, antibiotic: str) -> bool:
        """Check if a gene is biologically relevant to the given antibiotic.
        If gene is unknown in our mapping, we allow it through (permissive)."""
        ab_class = ANTIBIOTIC_CLASSES.get(antibiotic.lower())
        if ab_class is None:
            return True  # Unknown antibiotic class → allow all genes
        
        relevance = GENE_ANTIBIOTIC_RELEVANCE.get(gene_name)
        if relevance is None:
            return True  # Unknown gene → allow (permissive fallback)
        
        return ab_class in relevance

    @staticmethod
    def correct_direction(gene_name: str, model_direction: str) -> str:
        """Override model direction with biological truth for known resistance genes."""
        if gene_name in KNOWN_RESISTANCE_GENES and model_direction == "Susceptible":
            logger.info(f"Direction override: {gene_name} forced to Resistant (model said Susceptible)")
            return "Resistant"
        return model_direction

    def decompose_risk(self, risk_score: float, coef_map: Dict[str, float],
                       input_presence: Dict[str, int], antibiotic: str = "") -> Dict[str, Dict[str, Any]]:
        """
        Decompose the risk score into gene contributions.
        Applies biological filtering: only genes relevant to the selected
        antibiotic class are included as drivers, and model directions
        are overridden for known resistance genes.
        
        Returns: {gene_name: {'score': float, 'direction': str}}
        """
        # 1. Identify active gene contributors (features present in input)
        active_features = []
        total_importance = 0.0
        
        for feat, importance in coef_map.items():
            clean_feat = feat.replace("num__", "").replace("cat__", "")
            present = input_presence.get(feat, input_presence.get(clean_feat, 0))
            
            # Only consider real gene features that are present
            is_gene = (
                clean_feat != "gene_any_present" and
                (clean_feat.startswith("gene_") or (
                    not clean_feat.startswith("antibiotic") and 
                    not clean_feat.startswith("Antibiotic") and
                    "_name_" not in clean_feat
                ))
            )
            
            if not (present == 1 and is_gene):
                continue

            # Biological relevance filter
            gene_name = clean_feat.replace("gene_", "") if clean_feat.startswith("gene_") else clean_feat
            if not self.is_gene_relevant(gene_name, antibiotic):
                logger.debug(f"Filtering {gene_name}: not relevant to {antibiotic}")
                continue
                
            active_features.append(feat)
            total_importance += abs(importance)
                
        # 2. Distribute Risk
        contributions = {}
        
        if risk_score > 0 and total_importance > 0:
            for feat in active_features:
                clean_feat = feat.replace("num__", "").replace("cat__", "")
                gene_name = clean_feat.replace("gene_", "") if clean_feat.startswith("gene_") else clean_feat
                
                importance = coef_map[feat]
                share = abs(importance) / total_importance
                attrib_risk = share * risk_score
                raw_direction = "Resistant" if importance > 0 else "Susceptible"
                direction = self.correct_direction(gene_name, raw_direction)
                
                contributions[gene_name] = {
                    "score": attrib_risk,
                    "direction": direction
                }
        elif risk_score > 0 and total_importance == 0:
            # Fallback: model assigns zero importance to genes (e.g. S. aureus RF).
            present_genes = []
            for feat, importance in coef_map.items():
                clean_feat = feat.replace("num__", "").replace("cat__", "")
                is_gene = clean_feat.startswith("gene_") and clean_feat != "gene_any_present"
                present = input_presence.get(feat, input_presence.get(clean_feat, 0))
                gene_name = clean_feat.replace("gene_", "")
                if present == 1 and is_gene and self.is_gene_relevant(gene_name, antibiotic):
                    present_genes.append(clean_feat)
            
            # If coef_map was empty, fallback to raw input_presence keys
            if not present_genes:
                for feat, val in input_presence.items():
                    if val == 1 and feat.startswith("gene_") and feat != "gene_any_present":
                        gene_name = feat.replace("gene_", "")
                        if self.is_gene_relevant(gene_name, antibiotic):
                            present_genes.append(feat)
            
            if present_genes:
                equal_share = risk_score / len(present_genes)
                for feat in present_genes:
                    gene_name = feat.replace("gene_", "")
                    contributions[gene_name] = {
                        "score": equal_share,
                        "direction": "Resistant"
                    }
        
        return contributions

    def predict_risk(self, antibiotic: str, gene_presence: Dict[str, int]) -> Dict[str, Any]:
        """
        Run GAARA aggregation for a given antibiotic and gene profile.
        Steps:
        1. Preprocess & Predict per Pathogen
        2. Calculate Coverage Weights
        3. Decompose Risk into Gene Shares
        4. Aggregate Weighted Risk
        """
        pathogen_results = []
        total_weight = 0.0
        
        # 1. Per-Pathogen Loop
        for pathogen, model in self.loader.models.items():
            try:
                # --- A. Feature Extraction & Input Prep ---
                expected_features = self.get_model_features(model, pathogen)
                
                # Initialize default 0
                input_data = {feat: [0] for feat in expected_features}
                simple_input_map = {feat: 0 for feat in expected_features} # For easier lookup in decomposition
                
                # Set Antibiotic
                # Try various formats including OHE and prefixes
                target_ab = antibiotic.lower()
                
                # Check direct "Antibiotic" or "antibiotic_name" or "cat__Antibiotic"
                for key_variant in ["antibiotic_name", "Antibiotic", "cat__Antibiotic", "cat__antibiotic_name"]:
                    if key_variant in expected_features:
                        input_data[key_variant] = [antibiotic]
                        break
                else:
                    # OHE check
                    # We need to find the column that corresponds to this antibiotic
                    # e.g. "antibiotic_name_meropenem" or "cat__antibiotic_name_meropenem"
                    for feat in expected_features:
                        # Clean feature to check match
                        clean = feat.lower().replace("num__", "").replace("cat__", "")
                        if f"antibiotic_name_{target_ab}" in clean or f"antibiotic_{target_ab}" in clean:
                             input_data[feat] = [1]
                             simple_input_map[feat] = 1

                # Set Genes (with alias expansion)
                any_gene = 0
                expanded_genes = dict(gene_presence)  # copy
                for alias, targets in GENE_ALIASES.items():
                    if alias in expanded_genes and expanded_genes[alias] == 1:
                        for t in targets:
                            clean_t = t.replace("gene_", "")
                            if clean_t not in expanded_genes:
                                expanded_genes[clean_t] = 1
                
                for gene, present in expanded_genes.items():
                    if present: any_gene = 1
                    
                    for feat in expected_features:
                        clean_feat = feat.replace("num__", "").replace("cat__", "")
                        
                        if clean_feat == f"gene_{gene}":
                            input_data[feat] = [present]
                            simple_input_map[feat] = present
                        elif clean_feat.lower() == f"gene_{gene}".lower():
                             input_data[feat] = [present]
                             simple_input_map[feat] = present
                        elif clean_feat == gene:
                             input_data[feat] = [present]
                             simple_input_map[feat] = present

                if "gene_any_present" in input_data:
                    input_data["gene_any_present"] = [any_gene]
                    simple_input_map["gene_any_present"] = any_gene
                
                # Prepare DF
                df_input = pd.DataFrame(input_data)
                # Align columns exactly
                if expected_features:
                    df_input = df_input[expected_features]

                # --- B. Prediction ---
                logger.debug(f"{pathogen} - Expected features: {expected_features[:5]}")
                prob = 0.0
                if hasattr(model, "predict_proba"):
                    try:
                        prob = float(model.predict_proba(df_input)[:, 1][0])
                        logger.debug(f"{pathogen} - Predicted prob: {prob}")
                    except Exception as e:
                        logger.warning(f"Prediction error for {pathogen}: {e}")
                        prob = 0.0
                
                # --- C. Weighting & Decomposition ---
                
                # 1. Coverage Weight
                weight = self.calculate_coverage_weight(expected_features, gene_presence)
                
                # 2. Decomposition
                # Get raw coefficients/importance
                feature_names = expected_features
                if not feature_names and hasattr(model, "feature_names_in_"):
                    feature_names = list(model.feature_names_in_)
                
                # Priority 1: Load from CSV (static, curated)
                coef_map = self.load_feature_importance(pathogen)
                
                # Priority 2: Extract from model (dynamic fallback)
                if not coef_map:
                    coef_map = self.get_coefficients_map(model, feature_names)
                
                # Decompose
                gene_attribs = self.decompose_risk(prob, coef_map, simple_input_map, antibiotic)
                
                # gene_attribs is {gene: {score: float, direction: str}}
                # Convert to "risk_mass" dict for aggregation format
                risk_mass = {g: d["score"] for g, d in gene_attribs.items()}
                directions = {g: d["direction"] for g, d in gene_attribs.items()}
                
                pathogen_results.append({
                    "name": pathogen,
                    "risk": prob,
                    "weight": weight,
                    "risk_mass": risk_mass,
                    "directions": directions
                })
                
                total_weight += weight

            except Exception as e:
                logger.error(f"Error processing {pathogen}: {str(e)}")
                continue

        # --- D. Aggregation ---
        if total_weight == 0:
            return {
                "overall_risk_score": 0.0, 
                "risk_category": "Low", 
                "gene_drivers": {}, 
                "pathogen_breakdown": []
            }
            
        # 1. Weighted Average of Risk
        weighted_risk_sum = sum(res["risk"] * res["weight"] for res in pathogen_results)
        overall_risk = weighted_risk_sum / total_weight
        
        # 2. Aggregate Gene contributions
        # We want the "Global Attribution" of each gene to the final score.
        # GlobalGeneRisk = Sum( (Weight_p / TotalWeight) * GeneRisk_p )
        
        global_gene_risk = {}
        all_genes = set()
        for res in pathogen_results:
            all_genes.update(res["risk_mass"].keys())
            
        for gene in all_genes:
            score = 0.0
            direction_votes = []
            
            for res in pathogen_results:
                if gene in res["risk_mass"]:
                    # Normalized weight for this pathogen
                    norm_w = res["weight"] / total_weight
                    # Contribution from this pathogen
                    contrib = res["risk_mass"][gene] * norm_w
                    score += contrib
                    direction_votes.append(res["directions"][gene])
            
            # Determine direction (majority vote or based on sign of max contrib)
            # Default to Resistant if present
            final_dir = "Resistant" 
            if direction_votes.count("Susceptible") > direction_votes.count("Resistant"):
                final_dir = "Susceptible"
                
            global_gene_risk[gene] = {"score": score, "direction": final_dir}

        # Categories
        if overall_risk < 0.33: risk_cat = "Low"
        elif overall_risk < 0.66: risk_cat = "Moderate"
        else: risk_cat = "High"

        return {
            "overall_risk_score": overall_risk,
            "risk_category": risk_cat,
            "gene_drivers": global_gene_risk,
            "pathogen_breakdown": pathogen_results
        }
