# currencyconverter

A production-ready Currency Converter web application featuring a high-performance Python FastAPI backend and live exchange rates from ExchangeRate-API.

---

## 1. Project Overview

This repository transforms a Google Colab prototype into a production-grade full-stack currency conversion platform:
- **Core Currency Converter Backend:** Async FastAPI service providing sub-millisecond conversion calculations, validation, in-memory rate caching, and support for 160+ ISO 4217 currencies.
- **Original Google Colab Notebook:** Preserved in [currencyconerter.ipynb](file:///c:/Users/chara/OneDrive/Desktop/projects/currencyconverter/currencyconverter/currencyconerter.ipynb) (featuring deterministic tool calling and an optional conversational Gemini assistant).
- **Target Architecture:** Render (Backend API) + Vercel (React + TypeScript + Vite Frontend in Phase 3).

---

## 2. Original Colab Notebook & Gemini Assistant

The original notebook ([currencyconerter.ipynb](file:///c:/Users/chara/OneDrive/Desktop/projects/currencyconverter/currencyconverter/currencyconerter.ipynb)) contains:
1. `convert_currency(amount, from_currency, to_currency)`: Deterministic live exchange rate calculation querying `https://open.er-api.com/v6/latest/{from_currency}`.
2. `ask_currency_assistant(prompt)`: An experimental natural-language chatbot using Google GenAI SDK (`google-genai`) with Gemini function calling and Colab Secrets (`userdata.get("sec1")`).

*Note:* Ordinary currency conversions require **no API keys or credentials**. The production backend implements the deterministic logic directly without external LLM latency or costs. The original notebook remains untouched in the root directory.

---

## 3. Directory Structure

```text
currencyconverter/
├── .gitignore                          # Ignores .venv, env secrets, caches, and build files
├── .python-version                     # Runtime pin (Python 3.12.10)
├── README.md                           # Project documentation and run guide
├── currencyconerter.ipynb              # Original Google Colab notebook (preserved)
├── backend/
│   ├── requirements.txt                # Pinned production and testing dependencies
│   ├── .env.example                    # Environment variable template
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application, CORS, and error handlers
│   │   ├── config.py                   # Pydantic BaseSettings environment loader
│   │   ├── schemas.py                  # Pydantic request and response models
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py               # GET /health process check
│   │   │   └── convert.py              # POST /api/convert & GET /api/currencies
│   │   └── services/
│   │       ├── __init__.py
│   │       └── currency_service.py     # Async HTTPX rate fetcher & in-memory caching
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                 # Pytest fixtures and mock responses
│       ├── test_health.py              # Tests for /health, CORS, and settings
│       └── test_convert.py             # 22+ tests for conversion, caching, and validation
└── frontend/                           # MONETA Editorial Frontend (React + TS + Vite)
    ├── index.html                      # Semantic HTML5 with editorial fonts
    ├── package.json                    # React 18, Vite 6, TypeScript 5, Lucide React
    ├── tsconfig.json                   # Strict TypeScript compiler options
    ├── vite.config.ts                  # Vite config with backend proxy
    ├── .env.example                    # VITE_API_BASE_URL template
    └── src/
        ├── main.tsx                    # Application entry point
        ├── App.tsx                     # Main Moneta conversion interface
        ├── index.css                   # Editorial design system & signature transfer animation
        ├── types/currency.ts           # TypeScript interfaces matching backend models
        ├── services/currencyApi.ts     # Centralized API client with error handling
        └── components/
            ├── AppHeader.tsx           # Moneta wordmark & live API status indicator
            ├── CurrencyField.tsx       # Decimal amount input with tabular numerals
            ├── CurrencySelect.tsx      # Searchable ISO currency selector dropdown
            ├── SwapButton.tsx          # Directional currency swap control
            ├── ConversionResult.tsx    # Result reveal with rate summary & stale badge
            ├── RateMetadata.tsx        # Provider attribution & rate timestamps
            └── ErrorBanner.tsx         # Accessible contextual error alert & retry
```

---

## 4. Python Version & Requirements

- **Python Runtime:** Python `3.12.x` (verified on `3.12.10`).
- **Framework & Libraries:**
  - `fastapi>=0.115.0,<0.116.0`
  - `uvicorn[standard]>=0.32.0,<0.33.0`
  - `pydantic>=2.10.0,<3.0.0`
  - `pydantic-settings>=2.6.0,<3.0.0`
  - `httpx>=0.28.0,<0.29.0`
  - `python-dotenv>=1.0.1,<2.0.0`
  - `pytest>=8.3.0,<9.0.0`
  - `pytest-asyncio>=0.24.0,<1.0.0`

---

## 5. Local Setup & Execution Guide

### Windows PowerShell

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create an isolated virtual environment:
   ```powershell
   py -3.12 -m venv .venv
   ```

3. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Configure local environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```
   - Open `backend/.env` and replace `replace_with_your_actual_gemini_api_key` with your Google Gemini API key from Google AI Studio.
   - **Security:** `backend/.env` is ignored by Git and must never be committed or shared publicly.
   - **Note:** Standard currency conversion (`/health`, `/api/currencies`, `/api/convert`) does **not** require a Gemini key. The key is reserved for future conversational AI assistant features.

6. Start the local development server:
   ```powershell
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

The API will be available at `http://127.0.0.1:8000`. Interactive documentation is accessible at `http://127.0.0.1:8000/docs`.

### Frontend Setup & Execution Guide (MONETA)

In a separate terminal:

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. (Optional) Configure custom backend URL:
   ```powershell
   Copy-Item .env.example .env
   ```
   *Note:* In local development, Vite proxies API requests directly to `http://127.0.0.1:8000`.

4. Start development server:
   ```powershell
   npm run dev
   ```

5. Build for production:
   ```powershell
   npm run build
   ```

The application interface will be live at `http://127.0.0.1:5173`.

---

## 6. Running Automated Tests

Run the full automated test suite using `pytest`:

```powershell
cd backend
.\.venv\Scripts\pytest.exe -v
```

All external exchange-rate provider requests are mocked for deterministic, network-independent test execution.

---

## 7. API Endpoints

### `GET /health`
Returns process health status without calling upstream services.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0"
}
```

---

### `POST /api/convert`
Converts an amount between two 3-letter ISO 4217 currency codes.

**Request Body:**
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "INR"
}
```

**Validation Rules:**
- `amount`: Number strictly `>= 0`, finite (no `NaN` or `Infinity`), boolean disallowed, max limit `1,000,000,000,000`.
- `from_currency`: 3 uppercase alphabetic characters (`^[A-Z]{3}$`).
- `to_currency`: 3 uppercase alphabetic characters (`^[A-Z]{3}$`).

**Response `200 OK`:**
```json
{
  "success": true,
  "amount": 100.0,
  "from_currency": "USD",
  "to_currency": "INR",
  "exchange_rate": 96.829695,
  "converted_amount": 9682.97,
  "rate_last_updated_utc": "Sun, 11 Oct 2026 00:02:31 +0000",
  "rate_next_update_utc": "Mon, 12 Oct 2026 00:14:21 +0000",
  "source": "open.er-api.com"
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Request validation failure (malformed currency code, negative amount, non-numeric input).
- `404 Not Found`: Formatted currency code is unsupported by provider.
- `502 Bad Gateway`: Upstream exchange-rate service connection failure or malformed upstream response.
- `504 Gateway Timeout`: Upstream exchange-rate service timed out.

---

### `GET /api/currencies`
Returns a sorted list of all active supported currency codes.

**Response `200 OK`:**
```json
{
  "success": true,
  "count": 166,
  "base_currency": "USD",
  "currencies": ["AED", "AFN", "ALL", "AMD", "ANG", "USD", "INR", "..."]
}
```

---

## 8. Deployment Prerequisites (Render)

- **Service Type:** Web Service
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`
- **Environment Variables:**
  - `ENVIRONMENT=production`
  - `CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app`

---

## 9. Next Steps

- **Phase 3:** React + TypeScript + Vite frontend development.
- **Phase 4:** Full-stack integration and end-to-end verification.
- **Phase 5:** Production deployment to Render and Vercel.