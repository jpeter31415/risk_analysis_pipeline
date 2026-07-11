import os
import logging
import datetime as dt
from dateutil.relativedelta import relativedelta
import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import (create_engine, Table, Column, String, Date, 
                        Numeric, MetaData)

#===================
# setup and logging
#===================

#logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - [%(levelname)s] - %(message)s'
    )

#tickers, start_date (10 years ago), end_date (today)
tickers = ['QQQ','QQQE']
start_date = dt.date.today() - relativedelta(years=10)
end_date = dt.date.today()

#database credentials
db_user = os.getenv('db_user', 'postgres')
db_password = os.getenv('db_password', 'your secure password')
db_host = os.getenv('db_host', 'localhost')
db_port = os.getenv('db_port', '5432')
db_name = os.getenv('db_name', 'ticker_prices')

#create connection engine for PSQL
database_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(database_url)
metadata = MetaData()

# Define table metadata using sqlalchemy Table method
ticker_prices_table = Table(
    'ticker_prices',
    metadata,
    Column('ticker', String(10), primary_key = True),
    Column('date', Date, primary_key = True),
    Column('open_price', Numeric(12,2)),
    Column('high_price', Numeric(12,2)),
    Column('low_price', Numeric(12,2)),
    Column('close_price', Numeric(12,2)),
    Column('adj_close_price', Numeric(12,2)),
    Column('volume', Numeric)
    )

#==============================================
# Extraction (API Sourcing) and Transformatiton
#==============================================
def extract_ticker_data(tickers: list, start: str, end: str) -> pd.DataFrame:
    """
    Uses yfinance to extract historical daily
    prices, making sure to have columns for both close_price and
    adj_close_price by passing in auto_adjust = False.
    """
    logging.info(f'Extracting tickers: {tickers} from {start} to {end}.')
    try:
        raw_data = yf.download(tickers, start = start, end = end, group_by = 
                               'ticker', auto_adjust= False)
        return raw_data
    except Exception as e:
        logging.error(f'Extraction error: {e}')
        raise

def parse_and_reformat(raw_df: pd.DataFrame, tickers: list) -> pd.DataFrame:
    """
    Reformats the multi-index structure from yfinance. 
    Renames columns to conform to PSQL standards.
    """
    logging.info('Reshaping raw dataframe into standard relational rows.')
    parsed_records = []
    
    #verify that tickers are in raw dataframe
    for ticker in tickers:
        if ticker not in raw_df.columns.levels[0]:
            logging.error(f'Ticker {ticker} not found in dataset columns.')
            
        #reformat the dataframes for each ticker
        ticker_df = raw_df[ticker].copy().reset_index()
        #add column for ticker
        ticker_df['ticker'] = ticker
        
        #rename columns for PSQL
        ticker_df.rename(columns = {
            'Date':'date',
            'Open':'open_price',
            'High':'high_price',
            'Low':'low_price',
            'Close':'close_price',
            'Adj Close':'adj_close_price',
            'Volume':'volume'
            },
            inplace = True)
        
        # Select explicit targets to strip extraneous indexes
        target_cols = ['ticker', 'date', 'open_price', 'high_price',
                       'low_price', 'close_price', 'adj_close_price', 
                       'volume']
        parsed_records.append(ticker_df[target_cols])
        
    return pd.concat(parsed_records, ignore_index = True)     
    
#==================
#DATABASE INGESTION    
#==================
def init_db():
    """
    Ensuring relational databases are built in PSQL
    """
    logging.info('Initializing PSQL Tables')
    metadata.create_all(engine)

def load_data_to_psql(df: pd.DataFrame):
    """
    Uses an upseert statement to load df as the values to the ticker_prices
    table in PSQL.      
    """
    logging.info(f'Pushing {len(df)} records into PSQL')
    
    #convert df to a list of dictionaries
    records = df.to_dict(orient='records')
    
    #insert statement
    stmt = insert(ticker_prices_table).values(records)
    
    #upsert logic
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=['ticker','date'],
        set_={
            'open_price': stmt.excluded.open_price,
            'high_price': stmt.excluded.high_price,
            'low_price': stmt.excluded.low_price,
            'close_price': stmt.excluded.close_price,
            'adj_close_price': stmt.excluded.adj_close_price,
            'volume': stmt.excluded.volume
            }
        )
    
    #execute the statement
    with engine.connect() as connection:
        connection.execute(upsert_stmt)
        connection.commit()
    
    logging.info('Data successfully loaded.')    
    
#===========
# Execution
#===========

if __name__ == '__main__':
    #Extracting raw data
    raw_data = extract_ticker_data(tickers, start_date, end_date)
    
    #Cleaning data
    cleaned_df = parse_and_reformat(raw_data, tickers)

    #Database ingestion  
    init_db()   
    load_data_to_psql(cleaned_df)
