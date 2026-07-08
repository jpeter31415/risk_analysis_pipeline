import numpy as np
import pandas as pd
from sqlalchemy import create_engine

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
    print(df.columns) 

    #pivot data into time-series matrix
    df_pivot = df.pivot(index = 'date', columns = 'ticker', values = 'adj_close_price').dropna()
    
    return df_pivot

#============================
# Sharpe Ratios and Drawdowns
#============================

def calculate_risk_metrics(price_df: pd.DataFrame, risk_free_rate: float = 0.04)->tuple:
    """
    calculates annualized sharpe ratios and maximum drawdowns for each etf
    """
    TRADING_DAYS = 252
    metrics_summary = {}
    daily_rf_log_rate = np.log(1+risk_free_rate)/TRADING_DAYS
    
    #construct a dataframe of log returns
    returns_df = np.log(price_df/price_df.shift(1)).dropna()
    
    #loop through tickers to calculate metrics for each
    for ticker in returns_df.columns:
        ticker_prices = price_df[ticker]
        ticker_returns = returns_df[ticker]
        
        #annualized return for display
        annualized_return = ticker_returns.mean()*TRADING_DAYS
        
        #annualized volatility for display
        annualized_vol = ticker_returns.std()*np.sqrt(TRADING_DAYS)
        
        #Sharpe ratio
        excess_returns = ticker_returns - daily_rf_log_rate
        mean_excess_returns = np.mean(excess_returns)
        std_excess_returns = np.std(excess_returns, ddof=1)
        daily_sharpe = mean_excess_returns/std_excess_returns
        
        #annualized sharpe ratio
        annualized_sharpe = daily_sharpe * np.sqrt(TRADING_DAYS)

        #Drawdown computation
        prices_array = ticker_prices.to_numpy()
        rolling_max = np.maximum.accumulate(prices_array)
        drawdown_array = (prices_array-rolling_max)/rolling_max
        max_drawdown = drawdown_array.min()
        
        #build dictionary to retrun
        pd.set_option('display.max_columns', None)
        metrics_summary[ticker] = {
            'Annualized Return' : f'{annualized_return:.4%}',
            'Annualized Volatility' : f'{annualized_vol:.4%}',
            'Annualized Sharpe Ratio' : f'{annualized_sharpe:.4f}',
            'Max Drawdown' : f'{max_drawdown:.4%}'
            }
    
    return metrics_summary, returns_df, price_df 

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
  
#==========
# Execution
#==========    
if __name__ == '__main__':    
    # Initialize connection using the engine 
    (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)=("postgres", "postgres", "localhost", "5432", "ticker_prices")
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    historical_data = fetch_historical_data(engine) 

    # Get risk metrics
    summary, returns_df, price_df = calculate_risk_metrics(historical_data,risk_free_rate=0.04)       
    print(pd.DataFrame(summary).T)

