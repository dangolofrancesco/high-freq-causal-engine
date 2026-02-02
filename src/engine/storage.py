"""
Docstring for engine.storage
This module contains classes and functions related to data storage management
"""

import logging
from pathlib import Path
from typing import Optional

import duckdb

# Set up logging configuration (useful for debugging and tracking)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MarketDataDB:
    """
    Manages the connection and operations for the DuckDB database.
    Designed for OLAP operations on financial time-series data.
    """

    def __init__(self, db_path: str = "data/market_data.duckdb"):
        """
        Initializes the database connection.

        Args:
            db_path (str): The file path for the DuckDB database.
        """

        # Ensure the directory for the database exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path)
        self._initialize_scheme()
        logging.info(f"Connected to DuckDB database at {self.db_path}")

    def _initialize_scheme(self) -> None:
        """
        Initialize the database schema for market data storage if not already present.
        We add a 'trades' table for High-Frequency Trading data.

        Schema decisions:
        - FLOAT4 is used for price data to optimize memory usage and vectorization speed.
        - The primary key (symbol, timestamp) prevents duplicate entries for the same candle.
        """

        query_ohlcv = """
        CREATE TABLE IF NOT EXISTS ohlcv (
            symbol TEXT,             
            timestamp TIMESTAMP,     
            open FLOAT4,             
            high FLOAT4,             
            low FLOAT4,              
            close FLOAT4,
            volume FLOAT4,
            PRIMARY KEY (symbol, timestamp)
        );
        """

        # New table for trades data
        # This table captures individual trade events and will use C++ engine
        """
        timestamp: what time the trade occurred (ms precision)
        price: price at which the trade was executed
        quantity: volume of the trade
        side: 'buy' or 'sell' indicating the trade direction
        """

        query_trades = """
        CREATE TABLE IF NOT EXISTS trades (
            symbol TEXT,
            timestamp TIMESTAMP,
            price FLOAT4,
            quantity FLOAT4,
            side TEXT,
            PRIMARY KEY (symbol, timestamp, price, quantity)
        );
        """
        # Primay key is complext because in a ms can occur multiple trades at same price and quantity
        # In prod we should consider adding a unique trade ID from the exchange

        try:
            self.conn.execute(query_ohlcv)
            self.conn.execute(query_trades)
            logging.info(
                "Database schemas (OHLCV and Trades) initialized successfully."
            )
        except Exception as e:
            logging.error(f"Error initializing database schema: {e}")
            raise

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get the current database connection.

        Returns:
            duckdb.DuckDBPyConnection: The current DuckDB connection.
        """
        return self.conn

    def close(self) -> None:
        """
        Close the database connection.
        """
        self.conn.close()


# Block to test the MarketDataDB class functionality independently
if __name__ == "__main__":
    try:
        db = MarketDataDB()
        print(f"Database connected at: {db.db_path}")

        con = db.get_connection()
        tables = con.execute("SHOW TABLES").fetchall()
        print(f"Tables found: {tables}")

        if tables:
            columns = con.execute("DESCRIBE ohlcv").fetchall()
            print("Table Schema (ohlcv):")
            for col in columns:
                print(col)

        db.close()

    except Exception as e:
        print(f"Error during module test: {e}")
