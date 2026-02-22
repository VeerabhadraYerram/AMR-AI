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
DATA_DIR = "/Users/shivaniyerram/Desktop/Projects/AMR-AI-Platform/data"
KLEB_PATH = os.path.join(DATA_DIR, "FINAL_AMR_KLEBSIELLA (2).csv")
ECOLI_PATH = os.path.join(DATA_DIR, "E_Coli_Final_ML_Dataset_v1.csv")
SAUREUS_PATH = os.path.join(DATA_DIR, "S_aureus.csv")

# ─── Geographic Location → Indian State mapping ───
# Longest-match-first lookup: cities, districts, and states
LOCATION_TO_STATE = {
    # Cities → State
    "kolkata": "West Bengal", "kharagpur": "West Bengal",
    "bangalore": "Karnataka", "mysore": "Karnataka", "mysuru": "Karnataka",
    "bellary": "Karnataka", "ballari": "Karnataka", "hassan": "Karnataka",
    "gullenahalli": "Karnataka", "adaguru": "Karnataka", "chattanahalli": "Karnataka",
    "dyapalapura": "Karnataka", "soppinahalli": "Karnataka", "shanthi grama": "Karnataka",
    "chennai": "Tamil Nadu", "vellore": "Tamil Nadu", "madurai": "Tamil Nadu",
    "thanjavur": "Tamil Nadu", "hosur": "Tamil Nadu", "ashok nagar": "Tamil Nadu",
    "vengaivasal": "Tamil Nadu", "vengabakkam": "Tamil Nadu", "madambakkam": "Tamil Nadu",
    "keerapakkam": "Tamil Nadu", "kanchipuram": "Tamil Nadu",
    "cochin": "Kerala", "kochi": "Kerala", "amritapuri": "Kerala",
    "kollam": "Kerala", "alappuzha": "Kerala", "kodungallur": "Kerala",
    "munambam": "Kerala",
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "aurangabad": "Maharashtra", "jawhar": "Maharashtra",
    "hyderabad": "Telangana", "hyderbad": "Telangana",
    "ahmedabad": "Gujarat", "vadodara": "Gujarat", "anand": "Gujarat",
    "banaskantha": "Gujarat", "dantiwada": "Gujarat",
    "guwahati": "Assam", "silagrant": "Assam", "sila grant": "Assam",
    "garoghuli": "Assam", "gorchuk": "Assam", "diparbill": "Assam",
    "north guwahati": "Assam",
    "shillong": "Meghalaya", "tura": "Meghalaya", "mawbri": "Meghalaya",
    "nonglakhiat": "Meghalaya", "iewduh": "Meghalaya", "burabazar": "Meghalaya",
    "agartala": "Tripura",
    "delhi": "Delhi", "new delhi": "Delhi", "bhajanpura": "Delhi",
    "safdarjung": "Delhi",
    "rohtak": "Haryana", "karnal": "Haryana",
    "chandigarh": "Chandigarh",
    "aligarh": "Uttar Pradesh", "lucknow": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh", "allahabad": "Uttar Pradesh",
    "puttaparthi": "Andhra Pradesh", "guntur": "Andhra Pradesh",
    # States (for "India: Gujarat" etc.)
    "tamil nadu": "Tamil Nadu", "tamilnadu": "Tamil Nadu",
    "karnataka": "Karnataka", "kerala": "Kerala",
    "maharashtra": "Maharashtra", "gujarat": "Gujarat",
    "rajasthan": "Rajasthan", "rajsthan": "Rajasthan",
    "meghalaya": "Meghalaya", "assam": "Assam", "tripura": "Tripura",
    "mizoram": "Mizoram", "manipur": "Manipur", "nagaland": "Nagaland",
    "sikkim": "Sikkim", "arunachal pradesh": "Arunachal Pradesh",
    "west bengal": "West Bengal", "bihar": "Bihar", "odisha": "Odisha",
    "jharkhand": "Jharkhand",
    "punjab": "Punjab", "haryana": "Haryana",
    "telangana": "Telangana", "andhra pradesh": "Andhra Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "chattisgarh": "Chhattisgarh", "chhattisgarh": "Chhattisgarh",
    "puducherry": "Puducherry", "goa": "Goa",
    "jammu": "Jammu and Kashmir", "kashmir": "Jammu and Kashmir",
    "himachal": "Himachal Pradesh",
}
# Sort by key length descending for longest-match-first
_SORTED_LOC_KEYS = sorted(LOCATION_TO_STATE.keys(), key=len, reverse=True)

# Zone → States (for fallback when state can't be extracted)
ZONE_TO_STATES = {
    "North": ["Delhi", "Uttar Pradesh", "Punjab", "Haryana", "Chandigarh",
              "Jammu and Kashmir", "Himachal Pradesh", "Uttarakhand"],
    "South": ["Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh",
              "Telangana", "Puducherry"],
    "East": ["West Bengal", "Bihar", "Odisha", "Jharkhand"],
    "North-East": ["Assam", "Sikkim", "Manipur", "Mizoram", "Tripura",
                   "Meghalaya", "Nagaland", "Arunachal Pradesh"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa",
             "Dadra and Nagar Haveli", "Daman and Diu"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
}
ALL_STATES = [s for states in ZONE_TO_STATES.values() for s in states]

# Neighbors for interpolation (used for states with no data)
STATE_NEIGHBORS = {
    "Madhya Pradesh": ["Uttar Pradesh", "Rajasthan", "Gujarat", "Maharashtra", "Chhattisgarh"],
    "Chhattisgarh": ["Madhya Pradesh", "Uttar Pradesh", "Jharkhand", "Odisha", "Maharashtra", "Telangana"],
    "Uttarakhand": ["Uttar Pradesh", "Himachal Pradesh", "Delhi", "Haryana"],
    "Himachal Pradesh": ["Punjab", "Haryana", "Uttarakhand", "Chandigarh"],
    "Jammu and Kashmir": ["Punjab", "Himachal Pradesh"],
    "Sikkim": ["West Bengal", "Assam"],
    "Nagaland": ["Assam", "Manipur"],
    "Arunachal Pradesh": ["Assam"],
    "Goa": ["Maharashtra", "Karnataka"],
    "Dadra and Nagar Haveli": ["Gujarat", "Maharashtra"],
    "Daman and Diu": ["Gujarat"],
    "Puducherry": ["Tamil Nadu"],
    "Lakshadweep": ["Kerala"],
    "Andaman and Nicobar": ["West Bengal"],
}


def extract_state(geo_loc: str) -> str:
    """Extract Indian state name from a Geographic Location string.
    
    Examples:
        'India: Vellore'          → 'Tamil Nadu'
        'India: Kolkata'          → 'West Bengal'
        'India: Chattisgarh, ...' → 'Chhattisgarh'
        'India: Gujarat'          → 'Gujarat'
        'India'                   → None
    """
    if not isinstance(geo_loc, str):
        return None
    loc = re.sub(r'^India\s*:?\s*', '', geo_loc, flags=re.IGNORECASE).strip().lower()
    if not loc or loc == 'india':
        return None
    for key in _SORTED_LOC_KEYS:
        if key in loc:
            return LOCATION_TO_STATE[key]
    return None


def load_and_aggregate_data():
    """
    Loads K. pneumo, E. coli, and S. aureus data.
    Extracts Indian state from Geographic Location for state-level granularity.
    Falls back to zone-level region column when state can't be extracted.
    Returns DataFrame with columns: [state, antibiotic_name, phenotype_label, year, pathogen]
    """
    dfs = []

    # ── 1. Klebsiella ──
    if os.path.exists(KLEB_PATH):
        try:
            df_k = pd.read_csv(KLEB_PATH,
                               usecols=["region", "Geographic Location", "antibiotic_name",
                                        "phenotype_label", "Collection Year"],
                               dtype=str)
            df_k.rename(columns={"Collection Year": "year"}, inplace=True)
            df_k["phenotype_label"] = pd.to_numeric(df_k["phenotype_label"], errors='coerce')
            df_k["state"] = df_k["Geographic Location"].apply(extract_state)
            df_k["pathogen"] = "K. pneumoniae"
            dfs.append(df_k[["state", "region", "antibiotic_name", "phenotype_label", "year", "pathogen"]])
            logger.info(f"Klebsiella loaded: {len(df_k)} rows, {df_k['state'].notna().sum()} state-mapped")
        except Exception as e:
            logger.error(f"Error loading Klebsiella: {e}")

    # ── 2. E. coli ──
    if os.path.exists(ECOLI_PATH):
        try:
            df_e = pd.read_csv(ECOLI_PATH, header=0,
                               usecols=["antibiotic_name", "phenotype_label",
                                        "collection_year", "region", "state_ut"],
                               dtype=str)
            df_e.rename(columns={"collection_year": "year"}, inplace=True)
            df_e["phenotype_label"] = pd.to_numeric(df_e["phenotype_label"], errors='coerce')
            # state_ut contains Geographic Location strings → extract state
            df_e["state"] = df_e["state_ut"].apply(extract_state)
            df_e["pathogen"] = "E. coli"
            dfs.append(df_e[["state", "region", "antibiotic_name", "phenotype_label", "year", "pathogen"]])
            logger.info(f"E. coli loaded: {len(df_e)} rows, {df_e['state'].notna().sum()} state-mapped")
        except Exception as e:
            logger.error(f"Error loading E. Coli: {e}")

    # ── 3. S. aureus ──
    if os.path.exists(SAUREUS_PATH):
        try:
            df_s = pd.read_csv(SAUREUS_PATH,
                               usecols=["Geographic Location", "Antibiotic", "Resistant Phenotype"],
                               dtype=str)
            df_s.rename(columns={
                "Geographic Location": "geo_loc",
                "Antibiotic": "antibiotic_name",
                "Resistant Phenotype": "phenotype_status"
            }, inplace=True)
            df_s["state"] = df_s["geo_loc"].apply(extract_state)
            df_s["phenotype_label"] = df_s["phenotype_status"].apply(
                lambda x: 1 if isinstance(x, str) and x.strip().lower() == "resistant" else 0
            )
            df_s["year"] = "2024"
            df_s["pathogen"] = "S. aureus"
            df_s["region"] = "Other"  # S. aureus has no region column
            dfs.append(df_s[["state", "region", "antibiotic_name", "phenotype_label", "year", "pathogen"]])
            logger.info(f"S. aureus loaded: {len(df_s)} rows, {df_s['state'].notna().sum()} state-mapped")
        except Exception as e:
            logger.error(f"Error loading S. Aureus: {e}")

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Normalize zone-level region column (for fallback)
    df["region"] = df["region"].fillna("Other").replace({
        "east": "East", "west": "West", "north": "North", "south": "South",
        "north-east": "North-East", "North-east": "North-East"
    })

    # Clean Antibiotic Names
    df["antibiotic_name"] = df["antibiotic_name"].str.title().str.strip()

    state_mapped = df["state"].notna().sum()
    logger.info(f"Total: {len(df)} rows, {state_mapped} ({state_mapped/len(df)*100:.0f}%) mapped to states")
    
    # DEBUG: Print pathogen counts
    print("DEBUG: GLOBAL_DF Pathogen Counts:")
    print(df["pathogen"].value_counts())
    print("DEBUG: Sample rows:")
    print(df.head())
    
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
    Build per-state resistance data from a DataFrame.
    
    Strategy:
    1. State-level: group by extracted state, compute mean resistance + count
    2. Zone fallback: for records without a state, use zone→states mapping
    3. Neighbor interpolation: for remaining empty states, average neighbors
    """
    state_data = {}  # state → {"total_r": float, "total_n": int}

    # ── Step 1: Direct state-level aggregation ──
    state_mapped = df[df["state"].notna()].copy()
    if not state_mapped.empty:
        agg = state_mapped.groupby("state")["phenotype_label"].agg(["sum", "count"]).reset_index()
        for _, row in agg.iterrows():
            s = row["state"]
            state_data[s] = {"total_r": row["sum"], "total_n": int(row["count"])}

    # ── Step 2: Zone fallback for unmapped records ──
    zone_unmapped = df[df["state"].isna()].copy()
    if not zone_unmapped.empty:
        zone_agg = zone_unmapped.groupby("region")["phenotype_label"].agg(["sum", "count"]).reset_index()
        for _, row in zone_agg.iterrows():
            zone = row["region"]
            target_states = ZONE_TO_STATES.get(zone, [])
            if not target_states:
                continue
            # Distribute zone data equally among states not yet directly mapped
            unmapped_states = [s for s in target_states if s not in state_data]
            if not unmapped_states:
                # All states already have data; add proportionally
                unmapped_states = target_states
            per_state_r = row["sum"] / len(unmapped_states)
            per_state_n = max(1, int(row["count"] / len(unmapped_states)))
            for s in unmapped_states:
                if s in state_data:
                    state_data[s]["total_r"] += per_state_r
                    state_data[s]["total_n"] += per_state_n
                else:
                    state_data[s] = {"total_r": per_state_r, "total_n": per_state_n}

    # ── Step 3: Neighbor interpolation for remaining empty states ──
    for state in ALL_STATES:
        if state not in state_data:
            neighbors = STATE_NEIGHBORS.get(state, [])
            neighbor_rates = [
                state_data[n]["total_r"] / state_data[n]["total_n"]
                for n in neighbors if n in state_data and state_data[n]["total_n"] > 0
            ]
            if neighbor_rates:
                avg_rate = np.mean(neighbor_rates)
                state_data[state] = {"total_r": avg_rate * 10, "total_n": 10, "interpolated": True}
            else:
                # Last resort: use global mean
                global_mean = df["phenotype_label"].mean()
                state_data[state] = {"total_r": global_mean * 5, "total_n": 5, "interpolated": True}

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

    map_data = []
    for state in ALL_STATES:
        info = state_data.get(state)
        # Threshold: if filtering by specific drug, require at least 5 isolates to show logic
        min_n = 5 if antibiotic else 1
        
        if info and info["total_n"] >= min_n:
            rate = round((info["total_r"] / info["total_n"]) * 100, 1)
            n = info["total_n"]
            is_est = info.get("interpolated", False)
            
            detail_text = f"Resistance: {rate}%"
            if antibiotic:
                detail_text = f"{antibiotic}: {rate}%"
            if is_est:
                detail_text += " (est.)"

            map_data.append({
                "region": state,
                "value": rate,
                "metadata": {
                    "detail": detail_text,
                    "isolates": n,
                    "estimated": is_est,
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

    map_data = []
    for state in ALL_STATES:
        info = state_data.get(state)
        if info and info["total_n"] > 0:
            rate = round((info["total_r"] / info["total_n"]) * 100, 1)
            n = info["total_n"]
            is_est = info.get("interpolated", False)
            map_data.append({
                "region": state,
                "value": rate,
                "metadata": {
                    "detail": f"Carbapenem R: {rate}%{' (est.)' if is_est else ''}",
                    "isolates": n,
                    "info": "Last-resort antibiotic resistance",
                    "estimated": is_est,
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
