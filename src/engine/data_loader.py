import logging
import time

import ccxt
import numpy as np
import pandas as pd
from .storage import MarketDataDB

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DataLoader:
    """
    Handles ETL for High-Frequency Trading data from various exchanges into DuckDB using CCXT.
    Fetches raw tick-by-tick trades from Crypto Exchanges (Kraken).
    """

    def __init__(self, db: MarketDataDB):
        """
        Initializes the DataLoader with a MarketDataDB instance.

        Args:
            db (MarketDataDB): An instance of MarketDataDB for data storage.
        """
        self.db = db
        # Initialize CCXT exchange instance (Kraken)
        self.exchange = ccxt.kraken()

    def fetch_and_store_trades(self, symbol: str, limit: int = 1000) -> None:
        """
        Fetches the most recent trades (ticks) for a symbol.

        Args:
            symbol (str): Symbol in CCXT format (e.g., 'BTC/USDT').
            limit (int): Number of recent trades to fetch (Max usually 1000 per call).
        """
        logging.info(f"Fetching data for {symbol} with limit {limit}")

        try:
            # EXTRACT: fectehs recent trades data
            # Returns a list of dicts: [{'timestamp': 167..., 'price': 23000, 'side': 'buy', ...}]
            trades = self.exchange.fetch_trades(symbol, limit=limit)

            if not trades:
                logging.warning(f"No trade data returned for {symbol}.")
                return

            df = pd.DataFrame(trades)

            # Select only relevant columns for DB
            df = df[["timestamp", "price", "amount", "side"]]

            # Rename 'amount' to 'quantity' for clarity
            df.rename(columns={"amount": "quantity"}, inplace=True)

            # Convert 'BTC/USDT' to 'BTC-USD' format for DB consistency
            clean_symbol = symbol.replace("/", "-")
            df["symbol"] = clean_symbol

            # convert timestamp from ms to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # OPTIMIZE: cast price and quantity to FLOAT4
            df["price"] = df["price"].astype(np.float32)
            df["quantity"] = df["quantity"].astype(np.float32)

            # Manage side: if none, set to 'unknown'
            df["side"] = df["side"].fillna("unknown")

            # Reorder columns
            df = df[["symbol", "timestamp", "price", "quantity", "side"]]

            # Load data into DuckDB
            conn = self.db.get_connection()

            # 'INSERT OR IGNORE' to avoid duplicates based on primary key
            conn.execute("INSERT OR IGNORE INTO trades SELECT * FROM df")

            logging.info(
                f"Successfully stored {len(df)} rows for {symbol} into the database."
            )

        except Exception as e:
            logging.error(f"Error fetching or storing data for {symbol}: {e}")


if __name__ == "__main__":
    db = MarketDataDB()
    loader = DataLoader(db)

    assets = ["BTC/USD", "ETH/USD"]

    for asset in assets:
        loader.fetch_and_store_trades(asset, limit=1000)

    con = db.get_connection()

    # Count total ticks stored
    count = con.execute("SELECT count(*) FROM trades").fetchone()
    print(f"\nTotal ticks in database: {count[0]}")

    print("\nTick Data Sample (What the C++ Engine will eat):")
    print(con.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 5").df())
