from fastapi import APIRouter
from app.api.models import MapResponse
import logging
import pandas as pd
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Data Paths
ROUTES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ROUTES_DIR, "..", "..", "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KLEB_PATH = os.path.join(DATA_DIR, "FINAL_AMR_KLEBSIELLA (2).csv")
ECOLI_PATH = os.path.join(DATA_DIR, "E_Coli_Final_ML_Dataset_v1.csv")
SAUREUS_PATH = os.path.join(DATA_DIR, "S_aureus.csv")
SYNTHETIC_CSV_PATH = os.path.join(PROJECT_ROOT, "mams_hospital_synthetic_data.csv")

# Note: Regions and mappings are now discovered dynamically from the synthetic dataset.

def load_and_aggregate_data():
    """
    Loads synthetic AMR surveillance data from CSV if available, or generates it.
    Returns DataFrame with columns: [state, antibiotic_name, phenotype_label, year, pathogen]
    """
    if os.path.exists(SYNTHETIC_CSV_PATH):
        try:
            df = pd.read_csv(SYNTHETIC_CSV_PATH)
            logger.info(f"Loaded synthetic Hyderabad data from CSV: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading synthetic CSV: {e}. Falling back to generation.")

    np.random.seed(42) # For reproducibility
    
    total_isolates = 2500
    
    # Distribution centered around Bachupally
    regions = ["Bachupally", "Nizampet", "Kukatpally", "Miyapur", "Gachibowli", 
               "Kondapur", "Ameerpet", "Banjara Hills", "Secunderabad", "Uppal"]
    probs = [0.35, 0.20, 0.15, 0.10, 0.08, 0.06, 0.03, 0.02, 0.005, 0.005]
    
    pathogens = ["K. pneumoniae", "E. coli", "S. aureus"]
    pathogen_probs = [0.40, 0.45, 0.15]
    
    antibiotics = {
        "K. pneumoniae": ["Meropenem", "Ceftriaxone", "Ciprofloxacin", "Amikacin", "Colistin"],
        "E. coli": ["Meropenem", "Ceftriaxone", "Ciprofloxacin", "Amikacin", "Nitrofurantoin"],
        "S. aureus": ["Methicillin", "Vancomycin", "Linezolid", "Clindamycin"]
    }
    
    # Base resistance probabilties per drug (adjust to make realistic)
    base_res_probs = {
        "Meropenem": 0.25,
        "Ceftriaxone": 0.60,
        "Ciprofloxacin": 0.55,
        "Amikacin": 0.15,
        "Colistin": 0.02,
        "Nitrofurantoin": 0.10,
        "Methicillin": 0.40,
        "Vancomycin": 0.01,
        "Linezolid": 0.01,
        "Clindamycin": 0.35,
        "Piperacillin": 0.30
    }
    
    years = [2021, 2022, 2023, 2024]
    year_probs = [0.15, 0.25, 0.30, 0.30]

    data = []
    
    # Generate random data
    selected_regions = np.random.choice(regions, size=total_isolates, p=probs)
    selected_pathogens = np.random.choice(pathogens, size=total_isolates, p=pathogen_probs)
    selected_years = np.random.choice(years, size=total_isolates, p=year_probs)
    
    for i in range(total_isolates):
        r = selected_regions[i]
        p = selected_pathogens[i]
        y = selected_years[i]
        
        # Pick a random antibiotic tested for this pathogen
        ab = np.random.choice(antibiotics[p])
        
        # Calculate resistance probability based on drug base rate + some noise + slight regional variation
        base_rate = base_res_probs.get(ab, 0.3)
        
        # (e.g. Bachupally hospital might see slightly worse cases?)
        reg_mod = 1.1 if r == "Bachupally" else 1.0
        
        # (e.g. trend going up slightly over years)
        yr_mod = 1.0 + (y - 2021) * 0.05
        
        final_prob = min(0.99, base_rate * reg_mod * yr_mod)
        
        is_resistant = np.random.binomial(1, final_prob)
        
        data.append({
            "state": r,           # Using 'state' instead of 'locality' to reuse existing map logic
            "region": "Hyderabad", 
            "antibiotic_name": ab,
            "phenotype_label": int(is_resistant),
            "year": str(y),
            "pathogen": p
        })

    df = pd.DataFrame(data)
    
    # Save for future use
    try:
        df.to_csv(SYNTHETIC_CSV_PATH, index=False)
        logger.info(f"Saved generated synthetic data to {SYNTHETIC_CSV_PATH}")
    except Exception as e:
        logger.error(f"Could not save synthetic CSV: {e}")

    logger.info(f"Generated synthetic Hyderabad data: {len(df)} rows")
    return df


# ── Load Data Once ──
try:
    print("DEBUG: Loading data...")
    GLOBAL_DF = load_and_aggregate_data()
    print("DEBUG: Data loaded successfully.")
except Exception as e:
    print(f"DEBUG: Error loading data: {e}")
    GLOBAL_DF = pd.DataFrame()


def get_pathogen_counts() -> Dict[str, int]:
    """Return count of isolates per pathogen."""
    if GLOBAL_DF.empty:
        return {}
    return GLOBAL_DF["pathogen"].value_counts().to_dict()


def _build_state_map(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Build per-state resistance data from a DataFrame dynamically.
    """
    state_data = {}

    if df.empty:
        return {}

    # 1. State-level aggregation
    agg = df.groupby("state")["phenotype_label"].agg(["sum", "count"]).reset_index()
    for _, row in agg.iterrows():
        s = row["state"]
        state_data[s] = {"total_r": row["sum"], "total_n": int(row["count"])}

    return state_data


@router.get("/antibiotics")
async def get_antibiotics():
    """Return list of available antibiotics for filtering."""
    if GLOBAL_DF.empty:
        return {"antibiotics": []}
    
    # improved: filter out low-frequency drugs (<50 isolates)
    counts = GLOBAL_DF["antibiotic_name"].value_counts()
    valid_ab = counts[counts >= 50].index.tolist()
    return {"antibiotics": sorted(valid_ab)}


@router.get("/pathogens")
async def get_pathogens():
    """Return list of unique pathogens found in the dataset."""
    if GLOBAL_DF.empty:
        return {"pathogens": []}
    
    pathogens = GLOBAL_DF["pathogen"].unique().tolist()
    return {"pathogens": sorted(pathogens)}


@router.get("/antibiotic_performance", response_model=MapResponse)
async def get_antibiotic_performance(antibiotic: Optional[str] = None):
    """
    Antibiotic resistance rates by Indian state.
    Optional: filter by specific antibiotic name.
    """
    if GLOBAL_DF.empty:
        return {"map_type": "antibiotic_performance", "data": [], "status": "unavailable",
                "message": "No data loaded."}

    df = GLOBAL_DF.copy()
    
    # Filter by antibiotic if provided
    if antibiotic:
        df = df[df["antibiotic_name"].str.lower() == antibiotic.lower().strip()]
        if df.empty:
             return {"map_type": "antibiotic_performance", "data": [], "status": "unavailable",
                    "message": f"No data for {antibiotic}."}

    state_data = _build_state_map(df)

    # Use dynamic regions from GLOBAL_DF or state_data
    all_regions = sorted(GLOBAL_DF["state"].unique())
    map_data = []
    
    for state in all_regions:
        info = state_data.get(state)
        # Threshold: if filtering by specific drug, require at least 5 isolates to show logic
        min_n = 5 if antibiotic else 1
        
        if info and info["total_n"] >= min_n:
            rate = round((info["total_r"] / info["total_n"]) * 100, 1)
            n = info["total_n"]
            
            detail_text = f"Resistance: {rate}%"
            if antibiotic:
                detail_text = f"{antibiotic}: {rate}%"

            map_data.append({
                "region": state,
                "value": rate,
                "metadata": {
                    "detail": detail_text,
                    "isolates": n,
                    "estimated": False,
                }
            })
        else:
            map_data.append({
                "region": state,
                "value": 0,
                "metadata": {"detail": "Insufficient data", "isolates": 0}
            })

    return {
        "map_type": "antibiotic_performance",
        "data": map_data,
        "status": "success",
        "message": f"{antibiotic if antibiotic else 'Overall'} resistance rates by state."
    }


@router.get("/analytics/trends")
async def get_trends(antibiotic: Optional[str] = None, pathogen: Optional[str] = None):
    """
    Get resistance trends over years + Pathogen Distribution.
    Optional filters: antibiotic, pathogen.
    """
    if GLOBAL_DF.empty:
        return {"labels": [], "datasets": [], "pathogen_distribution": []}

    try:
        df = GLOBAL_DF.copy()
        
        # Apply filters
        if antibiotic:
            df = df[df["antibiotic_name"].str.lower() == antibiotic.lower().strip()]
        if pathogen:
            df = df[df["pathogen"].str.lower() == pathogen.lower().strip()]

        # Trend Analysis
        df["year"] = pd.to_numeric(df["year"], errors='coerce')
        trend_df = df.dropna(subset=["year"])
        trend_df = trend_df[(trend_df["year"] > 2010) & (trend_df["year"] <= 2024)] # Focus on relevant range
        
        if trend_df.empty:
             return {"labels": [], "datasets": [], "pathogen_distribution": []}

        trend = trend_df.groupby("year")["phenotype_label"].mean().reset_index().sort_values("year")

        # Pathogen Distribution (for current view)
        path_counts = df["pathogen"].value_counts().reset_index()
        path_counts.columns = ["name", "value"]

        title = "Average Resistance Rate"
        if antibiotic: title = f"{antibiotic} Resistance"
        if pathogen: title += f" ({pathogen})"

        return {
            "labels": trend["year"].astype(int).tolist(),
            "datasets": [{
                "label": title,
                "data": trend["phenotype_label"].tolist(),
                "borderColor": "rgb(255, 99, 132)",
                "backgroundColor": "rgba(255, 99, 132, 0.5)"
            }],
            "pathogen_distribution": path_counts.to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Trend error: {e}")
        return {"labels": [], "datasets": [], "pathogen_distribution": []}


@router.get("/analytics/heatmap")
async def get_heatmap():
    """
    Generate Antibiotic vs Pathogen Resistance Matrix.
    Returns: x_labels (Pathogens), y_labels (Antibiotics), data (2D array of resistance rates)
    """
    if GLOBAL_DF.empty:
        return {"x_labels": [], "y_labels": [], "data": []}

    try:
        # Filter for top drugs (>100 isolates) to keep heatmap readable
        top_drugs = GLOBAL_DF["antibiotic_name"].value_counts()
        top_drugs = top_drugs[top_drugs > 100].index.tolist()
        df = GLOBAL_DF[GLOBAL_DF["antibiotic_name"].isin(top_drugs)].copy()

        # Pivot: Index=Antibiotic, Col=Pathogen, Val=Resistance
        pivot = df.pivot_table(index="antibiotic_name", columns="pathogen", 
                               values="phenotype_label", aggfunc="mean")
        
        # Fill NaN with -1 (to represent "No Data" distinct from 0% resistance)
        pivot = pivot.fillna(-1)
        
        # Sort index and columns
        pivot = pivot.sort_index() 
        
        return {
            "y_labels": pivot.index.tolist(),         # Antibiotics
            "x_labels": pivot.columns.tolist(),       # Pathogens
            "data": pivot.values.tolist()             # 2D array [row][col]
        }
    except Exception as e:
        logger.error(f"Heatmap error: {e}")
        return {"x_labels": [], "y_labels": [], "data": []}


@router.get("/carbapenem_resistance", response_model=MapResponse)
async def get_carbapenem_resistance():
    """
    Carbapenem (last-resort) resistance rates by Indian state.
    Carbapenems: meropenem, imipenem, ertapenem.
    """
    if GLOBAL_DF.empty:
        return {"map_type": "carbapenem_resistance", "data": [], "status": "unavailable",
                "message": "No data loaded."}

    df = GLOBAL_DF.copy()
    df["ab_lower"] = df["antibiotic_name"].str.lower().str.strip()
    carb_df = df[df["ab_lower"].isin(["meropenem", "imipenem", "ertapenem"])]

    if carb_df.empty:
        return {"map_type": "carbapenem_resistance", "data": [], "status": "unavailable",
                "message": "No carbapenem data available."}

    state_data = _build_state_map(carb_df)

    all_regions = sorted(GLOBAL_DF["state"].unique())
    map_data = []

    for state in all_regions:
        info = state_data.get(state)
        if info and info["total_n"] > 0:
            rate = round((info["total_r"] / info["total_n"]) * 100, 1)
            n = info["total_n"]
            map_data.append({
                "region": state,
                "value": rate,
                "metadata": {
                    "detail": f"Carbapenem R: {rate}%",
                    "isolates": n,
                    "info": "Last-resort antibiotic resistance",
                    "estimated": False,
                }
            })
        else:
            map_data.append({
                "region": state,
                "value": 0,
                "metadata": {"detail": "No carbapenem data", "isolates": 0}
            })

    return {
        "map_type": "carbapenem_resistance",
        "data": map_data,
        "status": "success",
        "message": "State-level carbapenem resistance from integrated surveillance data."
    }


@router.get("/gene_distribution", response_model=MapResponse)
async def get_gene_distribution():
    """Gene distribution data — currently unavailable."""
    return {
        "map_type": "gene_distribution",
        "data": [],
        "status": "unavailable",
        "message": "Gene distribution data currently separate from regional surveillance."
    }
