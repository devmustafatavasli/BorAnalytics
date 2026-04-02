# BorAnalytics API Reference

Base URL (Development): `http://localhost:8000/api`

## Core Endpoints

### 1. GET `/api/exports`

Retrieves export records with optional filtering.

**Parameters:**

- `year` (int, optional)
- `country_iso3` (str, optional)
- `product_hs_code` (str, optional)
- `limit` (int, default=100)

**Response:**

```json
[
  {
    "year": 2023,
    "country_name": "China",
    "country_iso3": "CHN",
    "product_name": "Natural Borates",
    "hs_code": "2528",
    "value_usd": 150000000,
    "volume_tons": 500000,
    "anomaly_flag": false
  }
]
```

### 2. GET `/api/production`

Retrieves production volumes by facility and year.

**Parameters:**

- `year` (int, optional)
- `facility` (str, optional)

**Response:**

```json
[
  {
    "year": 2023,
    "facility": "Kırka",
    "product_name": "Natural Borates",
    "hs_code": "2528",
    "volume_tons": 80000
  }
]
```

### 3. GET `/api/countries`

Returns reference list of all countries.

## Analytics Endpoints

### 4. GET `/api/analytics/top-destinations`

Top N export destinations by value.

**Parameters:**

- `year` (int, default=2023)
- `limit` (int, default=10)

**Response:**

```json
[
  {
    "country_name": "China",
    "value_usd": 150000000
  }
]
```

### 5. GET `/api/analytics/market-share`

Turkey vs ROW market share comparisons.

**Parameters:**

- `start_year` (int, default=2000)
- `end_year` (int, default=2023)

### 6. GET `/api/analytics/yoy-growth`

Year-over-Year growth of total export value.

**Parameters:**

- `product_hs_code` (str, optional)

## ML Predictions

### 7. GET `/api/predictions/demand`

Returns LSTM model forecasts with confidence intervals.

**Parameters:**

- `product_hs_code` (str, required)
- `country_iso3` (str, required)
- `horizon` (int, default=3, max=5)

**Response:**

```json
{
  "country_name": "China",
  "product_name": "Natural Borates",
  "model_type": "lstm",
  "mae": 1504.2,
  "rmse": 1802.5,
  "forecasts": [
    {
      "year": 2024,
      "predicted_value": 450000,
      "lower_ci": 405000,
      "upper_ci": 495000
    }
  ]
}
```

## BorAnalytics v2 Endpoints

### 8. GET `/api/supply`

USGS global production and reserves data.

- **Parameters**: `year`, `country_iso3`

### 9. GET `/api/analytics/price-index`

Rolling 10-year Z-scores for median unit pricing and anomaly flags.

- **Parameters**: `product`

### 10. GET `/api/analytics/reconciliation`

Mirror trade discrepancy evaluations mapped globally.

### 11. GET `/api/analytics/anomalies`

Contextual anomaly attribution logic combining World Bank GDP and breadth checks.

### 12. GET `/api/predictions/hierarchical`

NeuralForecast (NHITS + MinTrace) coherent interval predictions mapping structural hierarchy.

- **Parameters**: `level` (global, product, country), `horizon`

### 13. GET `/api/predictions/explanation`

SHAP TreeExplainer feature attributions rendering dynamically semantic UI descriptions.

- **Parameters**: `prediction_id`

### 14. POST `/api/scenarios/run`

What-If Engine evaluating scenario logic (A, B, C) targeting macro capabilities exactly via active XGBoost.

- **Body**: `scenario`, `parameter`, `country_iso3`
