# BorAnalytics Model Notes (v2.0)

## Overview

BorAnalytics predicts global Boron market demand, prices, and supply impacts using two primary machine learning methodologies.

### 1. XGBoost Revenue Prediction & SHAP

The XGBoost regressor is trained on engineered features tracking historical export values (UN Comtrade) and World Bank GDP.

- **v2 Upgrade**: We now integrate `shap.TreeExplainer` to extract deterministic feature ranking attributions.
- **Scenario Simulations**: Market shocks are dynamically simulated by overriding feature parameters mapping competitor capacity (-% delta), GDP contractions (hard overrides), and Sectoral Demand shifts (proportional array scaling).

### 2. Hierarchical Forecasting (NHITS + MinTrace)

Replaces the independent LSTM baseline models from v1.

- **Structure**: Time-series matrix modeled with `GLOBAL:TOTAL` > `PRODUCT:CODE` > `COUNTRY:LEAF` unique_ids.
- **NHITS**: Neural Hierarchical Interpolation for Time Series trains on 2000-2023 with walk-forward validation.
- **MinTrace Reconciliation**: Applying `mint_shrink` mathematically ensures individual country import demands sum functionally exact to broader Product and Global macro totals.
