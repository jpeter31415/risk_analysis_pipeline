# Multi-Asset Financial Risk Pipeline & Analytics Dashboard

A quantitative analytics pipeline designed to extract historical market data, stage it within a relational PostgreSQL database, and analyze time-varying risk and drawdown profiles over rolling horizons. 

While the system is built to accept **any arbitrary list of tickers** inside the ETL pipeline, this repository highlights a comparative study between **QQQ** (Market-Cap Weighted Nasdaq 100) and **QQQE** (Equal-Weighted Nasdaq 100) to demonstrate the mathematical impact of portfolio weighting mechanics on risk-adjusted consistency and capital preservation.

## Technology Stack & Architecture
*   **Language:** Python 3.10+ (Pandas, NumPy for vectorized matrix operations)
*   **Database:** PostgreSQL (Relational persistence with composite primary keys to guarantee data integrity)
*   **ORM Layer:** SQLAlchemy 2.0 & Psycopg2 (Idempotent `ON CONFLICT DO UPDATE` UPSERT routines)
*   **Visual Analytics:** Matplotlib & Seaborn

```text
📁 financial-risk-pipeline/
└── 📁 src/
    ├── __init__.py        # Packages modules for structured imports
    ├── etl_pipeline.py    # Extracts from yfinance and upserts raw data into PostgreSQL
    ├── risk_engine.py     # Functional mathematics layer (Rolling Sharpe, Rolling Drawdown, Returns)
    └── dashboard.py       # High-density Matplotlib/Seaborn visualization layer
```

---

## Methodology & Mathematical Foundation

### 1. Rolling Annualized Sharpe Ratio
Instead of evaluating static lifetime performance, this engine calculates a rolling 1-year (252 trading days) window to track how excess return efficiency changes over distinct macroeconomic market cycles:
$$\text{Sharpe Ratio} = \frac{R_p - R_f}{\sigma}$$
*Where $R_p$ is the annualized asset return, $R_f$ is the risk-free rate benchmark (set to a flat 4.0%), and $\sigma$ represents the annualized sample standard deviation of daily log returns.*

### 2. Rolling Drawdown Profiles ("Underwater" Horizon)
To evaluate real-world capital preservation and measure asset behavior during market stress, the pipeline monitors the peak-to-trough equity erosion over rolling horizons:
$$\text{Drawdown} = \frac{\text{Price}_t - \text{Rolling Peak}}{\text{Rolling Peak}}$$
*Where $\text{Rolling Peak}$ tracks the maximum price achieved by the asset within the designated lookback window up to time $t$.*

---

## Key Case Study Insights: QQQ (Market-Cap) vs. QQQE (Equal-Weight)

Because **QQQ** and **QQQE** hold the **exact same 100 technology stocks**, any divergence in their risk and drawdown matrices is purely driven by their mathematical weighting schemes. This pipeline uncovers two major structural phenomena:

### 1. The Cost of Concentration Drag (Rolling Sharpe Dynamics)
In a market-cap weighted model (QQQ), mega-cap tech giants dominate the total portfolio variance.
*   **Bull Markets & Expansion:** When a few multi-trillion-dollar companies lead a narrow momentum rally, QQQ’s returns outpace the broader basket, generating a higher rolling Sharpe ratio.
*   **Regime Shifts:** Over full market cycles, QQQE's equal-weighted model (allocating a flat 1% to all 100 companies) taps into the size premium and avoids concentration drag. The rolling Sharpe chart visually captures extended periods where broad market participation allows QQQE to achieve equivalent or superior risk-adjusted efficiency compared to its top-heavy counterpart.

### 2. Drawdown Depth & Structural Fragility
Analyzing the rolling "underwater" drawdown charts reveals the trade-offs of diversification during market contractions:
*   **Mega-Cap Safe Havens:** During systemic tech-sector corrections, cash-rich mega-caps occasionally act as corporate fortress balance sheets. Because QQQ is heavily weighted in these giants, it can exhibit shallower drawdowns than QQQE if mid-cap tech firms experience a sharper liquidity contraction.
*   **Concentration Busts:** Conversely, when valuation bubbles pop specifically within the mega-cap cohort, QQQ suffers deeper, more punishing peak-to-trough drawdowns. QQQE's diversified structure mitigates this concentration penalty, showcasing a shallower drawdown ceiling.

---

## 🚀 Execution & Replication Guide

1. **Clone the repository and install dependencies:**
   ```bash
   git clone https://github.com
   cd financial-risk-pipeline
   pip install -r requirements.txt
   ```

2. **Configure local environment variables (Ensure PostgreSQL is running locally):**
   ```bash
   export DB_USER="postgres"
   export DB_PASSWORD="your_secure_password"
   export DB_HOST="localhost"
   export DB_PORT="5432"
   export DB_NAME="finance_analytics"
   ```

3. **Run the pipeline modules sequentially:**
   ```bash
   python src/etl_pipeline.py    # Pipeline triggers data ingestion
   python src/risk_engine.py     # Computes Sharpe ratios and max drawdowns
   pythin src/dashboard.py       # Computes rolling Sharpe ratios and rolling drawdowns and launches dashboard
   ```

