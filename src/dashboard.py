import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick

#===============
# Data Retrieval
#===============

def fetch_historical_data(engine)-> pd.DataFrame:
    """
    fetches data from ticker_prices table in PSQL. 
    pivots data into a time-series matrix.
    """
    
    query = """
            SELECT
                date,
                ticker,
                adj_close_price
            FROM ticker_prices   
            ORDER BY DATE
            """
    
    #pull in data
    df = pd.read_sql(query, con=engine, parse_dates = ['date'])

    #pivot data into time-series matrix
    df_pivot = df.pivot(index = 'date', columns = 'ticker', values = 'adj_close_price').dropna()
    
    return df_pivot

#=====================
# Rolling Calculations    
#=====================

def compute_rolling_metrics(returns_df: pd.DataFrame, price_df: pd.DataFrame, window: int=252)->tuple:
    """
    generates time-series dataframes for rolling one year windows
    """
    TRADING_DAYS = 252
    
    #pandas rolling mean over entire dataframe
    r_mean = returns_df.rolling(window=window).mean()*TRADING_DAYS
    r_std = returns_df.rolling(window=window).std()*np.sqrt(TRADING_DAYS)
    rolling_sharpe = ((r_mean - 0.04)/r_std).dropna()
    
    #pandas rolling dd over entire dataframe
    r_max = price_df.rolling(window= window).max()
    rolling_dd = ((price_df - r_max)/r_max).dropna()

    return rolling_sharpe, rolling_dd

#==============
# Visualization
#==============

def generate_risk_analytics_dashboard(rolling_sharpe: pd.DataFrame, rolling_drawdown: pd.DataFrame):
    """
    Generates a dual-panel dashboard comparing rolling Sharpe Ratios and 
    Drawdown profiles.
    """
    #====================
    # STYLE CONFIGURATION
    #====================
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 16
    })

    # 1-row, 2-column subplot framework
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), sharex=True)
    

    # =========================================================================
    # PANEL 1: ROLLING 1-YEAR SHARPE RATIO TIME-SERIES
    # =========================================================================
    ax1 = axes[0]
    for ticker in rolling_sharpe.columns:
        ax1.plot(
            rolling_sharpe.index, 
            rolling_sharpe[ticker], 
            label=ticker, 
            linewidth=1.5,
            alpha=0.85
        )
    
    #context lines to help read the metric
    ax1.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5) # Breakeven
    ax1.axhline(1, color='green', linestyle=':', linewidth=1, alpha=0.5)  # "Good" Sharpe threshold
    
    ax1.set_title("Rolling 1-Year Sharpe Ratio Time-Series\n(Risk-Adjusted Performance Dynamics)")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Sharpe Ratio (Annualized)")
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # =========================================================================
    # PANEL 2: ROLLING 1-YEAR DRAWDOWN PROFILE ("UNDERWATER" CHART)
    # =========================================================================
    ax2 = axes[1]
    for ticker in rolling_drawdown.columns:
        ax2.plot(
            rolling_drawdown.index, 
            rolling_drawdown[ticker], 
            label=ticker, 
            linewidth=1.5,
            alpha=0.75 
        )
        
        #light shade fill under the curve 
        ax2.fill_between(
            rolling_drawdown.index, 
            rolling_drawdown[ticker], 
            0, 
            alpha=0.03
        )

    #convert y-axis formatting into standard percentages
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    ax2.set_title("Rolling 1-Year Drawdown Horizon\n(Capital Destruction and Peak-to-Trough Exposure)")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Drawdown from Rolling Peak (%)")
    ax2.legend(loc="lower left", frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # =========================================================================
    # GLOBAL DASHBOARD ADJUSTMENTS
    # =========================================================================
    plt.suptitle("Comparing Risk-Adjusted Profiles for Tickers", fontweight='bold')
    plt.tight_layout()
    
    #display the final plots
    plt.show()

if __name__=='__main__':
    # Initialize connection using the engine 
    (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)=("postgres", "postgres", "localhost", "5432", "ticker_prices")
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    price_df = fetch_historical_data(engine)
    
    # Construct a dataframe of log returns
    returns_df = np.log(price_df/price_df.shift(1)).dropna()
    
    # Compute rolling metrics and display dashboard
    rolling_sharpe_1y, rolling_dd_1y = compute_rolling_metrics(returns_df, price_df)
    generate_risk_analytics_dashboard(rolling_sharpe_1y, rolling_dd_1y)
