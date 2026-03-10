# BorAnalytics Data Sources

All data used in this project is sourced from publicly available, legally accessible datasets. No proprietary or internal Eti Maden data is used.

## 1. UN Comtrade

- **Data Provided**: Turkey boron exports by country/year (HS 2528, 2840, 2841).
- **Access Method**: Free REST API (`comtradeapi.un.org`).
- **Legal Basis**: Public domain, free tier (with rate limits).

## 2. World Bank

- **Data Provided**: Commodity price indices, GDP per country.
- **Access Method**: Free REST API (`api.worldbank.org`).
- **Legal Basis**: Open Data license.

## 3. TuIK (Turkish Statistical Institute)

- **Data Provided**: Turkey mining production statistics.
- **Access Method**: Public datasets (CSV downloads).
- **Legal Basis**: Public domain.

## 4. Eti Maden Annual Reports

- **Data Provided**: Facility-level production volumes (Bandırma, Kırka, Emet, Bigadiç).
- **Access Method**: Public PDFs available on `etimaden.gov.tr`.
- **Legal Basis**: Publicly published reports.

> Note: HS Commodity Code Reference: 2528 covers natural borates and concentrates; related codes 2840 (borates) and 2841 (perborates) are also included where available.
<<<<<<< Updated upstream
=======

## 5. USGS Mineral Commodity Summaries (v2)

- **Data Provided**: Global boron production volumes and active reserves.
- **Access Method**: ScienceBase API / PDF Parse.
- **Legal Basis**: Public domain (USGS).

## 6. UN Comtrade Bilateral Mirror Imports (v2)

- **Data Provided**: Secondary declarations from top 30 global importing nations tracking Turkish export gaps.
- **Access Method**: Free REST API `comtradeapi.un.org` (Flow=M).

## 7. European Central Bank (ECB) Statistical Data Warehouse (v3)

- **Data Provided**: Annual average USD/EUR and TRY/EUR mappings generating direct USD/TRY cross-rates.
- **Access Method**: `sdw-wsrest.ecb.europa.eu` API endpoints safely.
- **Legal Basis**: Open-source domain logic.
>>>>>>> Stashed changes
