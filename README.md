# BorAnalytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[Live Demo](https://boranalytics.vercel.app/)** _(Replace with actual Vercel URL natively)_

## 🚀 Deployment Architecture (v4)

BorAnalytics is configured natively as a fully automated, cloud-native platform limiting manual interventions securely:

```text
Browser -> Vercel (React SPA) -> Render (FastAPI Web Service) -> Supabase (PostgreSQL)
```

### 🌍 Cloud Infrastructure

1. **Supabase (PostgreSQL)**: Handles relational modeling tracking millions of metrics dynamically.
2. **Render (Backend API)**: Serves internal `uvicorn` instances resolving AI prediction maps utilizing `python-dotenv`. An internal `APScheduler` tracks `/health` preserving limits.
3. **Vercel (Frontend UI)**: Distributes global React bundles statically mapping cached endpoints.
4. **GitHub Actions**: Executes `.github/workflows/monthly_etl.yml` every 1st of the month, natively iterating 9 internal Python scripts fetching UN Comtrade and ECB values avoiding stale metrics completely natively.

### ⚡ Quick Start Deployment

1. Set up a free Supabase Postgres instance and map its URL as `DATABASE_URL` everywhere.
2. Push this repository to GitHub natively.
3. Track `/` on Render linking the GitHub backend parsing Python environments natively setting `ALLOWED_ORIGINS` to your Vercel URL.
4. Track `/frontend` on Vercel setting `VITE_API_BASE_URL` logically bound to Render.
5. GitHub runners automatically catch and execute schema populations natively.

## 📊 Data Sources Setup

The system automatically tracks these boundaries:

- **USGS ScienceBase**: Annual global Boron reserves and supply.
- **World Bank API**: Direct GDP mapping and macroeconomic inflation boundaries.
- **UN Comtrade API**: Bilateral logic fetching Turkish export mirrors.
- **European Central Bank (ECB) SDMX**: `USD/EUR` and `TRY/EUR` continuous currency tracking.
