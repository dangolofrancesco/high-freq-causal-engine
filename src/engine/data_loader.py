import yfinance as yf
import pandas as pd
import logging
import numpy as np
from storage import MarketDataDB

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataLoader:
    """
    Handles the ETL process (Extract, Transform, Load) for market data.
    It fetches raw data from external providers (Yahoo Finance), cleans it,
    and stores it into the local DuckDB instance.
    """

    def __init__(self, db: MarketDataDB):
        """
        Initializes the DataLoader with a MarketDataDB instance.
        
        Args:
            db (MarketDataDB): An instance of MarketDataDB for data storage.
        """
        self.db = db
    
    def fetch_and_store(self, symbol: str, period: str = "1mo", interval: str = "1h") -> None:
        """
        Downloads historical OHLCV data from Yahoo Finance, cleans it,
        and stores it into the DuckDB database.
        
        Args:
            symbol (str): The ticker symbol to fetch data for (e.g., 'BTC-USD').
            period (str): The period over which to fetch data (e.g., '1mo').
            interval (str): The data interval (e.g., '1h').
        """
        logging.info(f"Fetching data for {symbol} for period {period} with interval {interval}")

        try:
            # Extract data from Yahoo Finance API
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logging.warning(f"No data fetched for {symbol}.")
                return
            
            # Clean and prepare data
            # Reset index to have date as a column
            df.reset_index(inplace=True)

            # Standardize column names to lowercase to match database schema
            df.columns = [col.lower() for col in df.columns]

            # Rename columns to match database schema
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            elif 'date' in df.columns:
                df.rename(columns={'date': 'timestamp'}, inplace=True)

            # Remove timezone information 
            if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)

            # Add symbol column
            df['symbol'] = symbol

            # Filter relevant columns
            needed_cols = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]

            # Check if all needed columns are present
            available_cols = needed_cols.columns.tolist()
            df = df[available_cols]

            # For optimization, explicitly cast float columns to FLOAT4
            float_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in float_cols:
                if col in df.columns:
                    df[col] = df[col].astype(np.float32)

            # Load data into DuckDB
            conn = self.db.get_connection()

            # 'INSERT OR IGNORE' to avoid duplicates based on primary key
            conn.execute("INSERT OR IGNORE INTO ohlcv SELECT * FROM df")

            logging.info(f"Successfully stored {len(df)} rows for {symbol} into the database.")

        except Exception as e:
            logging.error(f"Error fetching or storing data for {symbol}: {e}")

if __name__ == "__main__":
    db = MarketDataDB()
    loader = DataLoader(db)
    
    # Test assets: Bitcoin and Ethereum (High correlation pair)
    assets = ["BTC-USD", "ETH-USD"] 
    
    for asset in assets:
        loader.fetch_and_store(asset)
    

    con = db.get_connection()
    count = con.execute("SELECT count(*) FROM ohlcv").fetchone()
    print(f"\nTotal rows in database: {count[0]}")
    
    # Show sample data with types to verify FLOAT4
    print("\nData Sample:")
    print(con.execute("SELECT * FROM ohlcv LIMIT 3").df())