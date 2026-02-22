# Gene-Attributable Antimicrobial Resistance Aggregation (GAARA)

## Overview

This project implements a novel computational method for generating antibiotic-level antimicrobial resistance (AMR) intelligence by aggregating gene-attributable resistance signals across multiple pathogens.

Instead of averaging resistance predictions, this system decomposes resistance into gene-level contribution signals and recomposes them to generate biologically meaningful antibiotic risk indicators.

The core method is referred to as:

> **GAARA – Gene-Attributable Antibiotic Risk Aggregation**

---

## Problem Statement

Current AMR systems:

- Predict resistance per isolate or pathogen
- Report percentage resistance tables
- Aggregate using simple averages or thresholds

However, these approaches lose mechanistic information and fail to preserve genetic causation during cross-pathogen aggregation.

This project addresses this limitation.

---

## Core Innovation

GAARA performs:

1. **Prediction Decomposition**
   - Resistance predictions are decomposed into gene-level contribution components.

2. **Gene-Attributable Risk Normalization**
   - Each gene's contribution is normalized into a gene-attributable resistance risk mass.

3. **Intra-Pathogen Aggregation**
   - Gene-attributable resistance is aggregated within each pathogen.

4. **Cross-Pathogen Recomposition**
   - Gene-attributable resistance signals are recomposed across pathogens to generate antibiotic-level resistance indicators.

This preserves biological mechanism while enabling scalable surveillance.

---

## Current Implementation

### Pathogens (Phase 1)

- Escherichia coli
- Klebsiella pneumoniae

Each pathogen has:

- `model.pkl`
- `feature_importance.csv`

---

## Project Structure

AMR-AI-Platform/
│
├── models/
│ ├── e_coli/
│ │ ├── model.pkl
│ │ └── feature_importance.csv
│ │
│ ├── k_pneumoniae/
│ │ ├── model.pkl
│ │ └── feature_importance.csv
│
├── scripts/
│ ├── simple_aggregation.py
│ ├── gaara_aggregation.py
│
├── outputs/
│ ├── antibiotic_cross_pathogen_risk.csv
│
├── requirements.txt
└── README.md

---

## Outputs

### Output Class 1
- Trained pathogen-specific ML models (.pkl)

### Output Class 2
- Feature importance tables per pathogen

### Output Class 3
- Cross-pathogen antibiotic risk aggregation tables

### Output Class 4 (Demo Layer)
- Interactive UI for antibiotic-level resistance intelligence

---

## Intended Use

This system is designed for:

- Population-level AMR surveillance
- Antibiotic stewardship intelligence
- Mechanism-aware epidemiological analysis

It is **not** intended for direct clinical decision-making.

---

## Future Work

- Integration of hospital clinical datasets
- Regional stratification
- Temporal trend modeling
- Advanced GAARA weighting mechanisms
- Deployment-ready dashboard

---

## License

Academic / Research Use Only
