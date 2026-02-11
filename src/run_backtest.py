import sys
import os
import time
import pandas as pd

# Add src directory to path so engine_core.so can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.append(os.getcwd())

import engine_core
from engine.storage import MarketDataDB
from engine.data_loader import DataLoader
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

def run_simulation():
    """
    Orchestrates the Event-Driven Backtest.
    It feeds historical data tick-by-tick into the C++ engine 
    and simulates trading execution.
    """

    print("Starting Backtest Simulation...")

    # 1 - Initialize MarketDataDB and get connection
    try:
        db = MarketDataDB()
        con = db.get_connection()

        print("MarketDataDB initialized successfully.")

        # IMPORTANT: We must order by timestamp ASCENDING to simulate real-time data flow
        query = "SELECT * FROM trades ORDER BY timestamp ASC"
        df = con.execute(query).df()

        if df.empty:
            logging.warning("No trade data found in the database. Please run the data loading script first.")
            return
        print(df.head(1))
        print(f"Fetched {len(df)} trades from the database for simulation.")

    except Exception as e:
        logging.error(f"Error initializing database or fetching data: {e}")
        return
    
    # 2 - Simulate feeding data tick-by-tick into the C++ engine
    # We need to map symbols (e.g., 'BTC-USD') to integers (0 or 1)
    # because the C++ engine expects integer identifiers for assets.
    symbols = df["symbol"].unique()
    print(f"Unique symbols in data: {symbols}")

    leader_symbol = None
    follower_symbol = None

    # Simple logic to find BTC (Leader) and ETH (Follower)
    for sym in symbols:
        if "BTC" in sym:
            leader_symbol = sym
        elif "ETH" in sym:
            follower_symbol = sym

    if not leader_symbol or not follower_symbol:
        logging.error("Could not identify Leader (BTC) and Follower (ETH) symbols in the data.")
        return
    
    print(f"Identified Leader: {leader_symbol}, Follower: {follower_symbol}")

    # 3 - Initialize the C++ Engine
    # We set the thresholld for Order Boook Imbalance 
    # 0.2 means: if OBI > 0.2 (strong by pressure), generate a signal
    # We use a low threshold for testing to see more signals generated
    strategy_threshold = 0.2
    strategy = engine_core.PairStrategy(strategy_threshold)


    # 4 - Portfolio Variables (Simulation of capital and positions)
    initial_capital = 10000  # $10k starting capital 
    cash = initial_capital
    position = 0.0  # Amount of Follower asset (ETH) we hold
    trade_count = 0 

    # 5 - Simulate tick-by-tick processing
    # Each row in the DataFrame represents a trade tick. We will feed it into the C++ engine.
    tick_times = []
    for row in df.itertuples():
        tick_start = time.perf_counter_ns()

        # Prepare data for C++ engine
        # We need to convert the symbol to an integer ID (0 for Leader, 1 for Follower)
        symbol_id = 0 if row.symbol == leader_symbol else 1

        # Map the 'side' string to a boolean
        # 'buy' means the aggressor bouth (price likely to go up) ->  is_bid = True
        is_bid = True if row.side == 'buy' else False

        # Feed the tick into the C++ engine and get a signal
        strategy.on_market_data(symbol_id, row.price, row.quantity, is_bid)

        # Check if the strategy generated a signal
        signal = strategy.check_signals()
        
        # Execute trades based on the signal
        current_price = row.price  # Current price of the Follower asset (ETH)

        # If the current row (tick) is not for the Follower asset, we skip trade execution logic
        # we only trade ETH based on BTC signals
        if symbol_id != 1:
            continue

        # BUY LOGIC: if signal is 1 and we don't have a position, we buy ( 1 trade at a time for simplicity)
        if signal == 1 and position == 0.0:
            cost = current_price * 1  # Buying 1 unit of ETH

            # Check if we have enough cash to buy
            if cash >= cost:
                cash -= cost
                position += 1.0
                trade_count += 1
                print(f"[{row.timestamp}] BUY: Bought 1 unit of {follower_symbol} at ${current_price:.2f}. Cash: ${cash:.2f}, Position: {position} units")

        # SELL LOGIC: if signal is -1 and we have a position, we sell
        elif signal == -1 and position > 0.0:
            revenue = current_price * 1  # Selling 1 unit of ETH

            cash += revenue
            position -= 1.0
            trade_count += 1
            print(f"[{row.timestamp}] SELL: Sold 1 unit of {follower_symbol} at ${current_price:.2f}. Cash: ${cash:.2f}, Position: {position} units")

        tick_elapsed_ns = time.perf_counter_ns() - tick_start
        tick_times.append(tick_elapsed_ns)
        print(f"Done processing tick. Latency: {tick_elapsed_ns / 1000:.2f} µs")

    # --- Tick Processing Latency Statistics ---
    if tick_times:
        import numpy as np
        arr = np.array(tick_times, dtype=float) / 1000.0  # convert to µs
        print(f"\n--- TICK LATENCY STATS ---")
        print(f"Total ticks processed: {len(arr)}")
        print(f"Mean latency:   {arr.mean():.2f} µs")
        print(f"Median latency: {np.median(arr):.2f} µs")
        print(f"Min latency:    {arr.min():.2f} µs")
        print(f"Max latency:    {arr.max():.2f} µs")
        print(f"P95 latency:    {np.percentile(arr, 95):.2f} µs")
        print(f"P99 latency:    {np.percentile(arr, 99):.2f} µs")
        print(f"--------------------------\n")

    # 6 - Calculate perfrormance metrics at the end of the simulation
    last_known_price = df.iloc[-1]['price']
    final_equity = cash + (position * last_known_price)

    roi = ((final_equity - initial_capital) / initial_capital) * 100

    print("\n--- BACKTEST RESULTS ---")
    print(f"Total Trades Executed: {trade_count}")
    print(f"Number of assets held at the end: {position} units of {follower_symbol}")
    print(f"Initial Capital:       ${initial_capital:.2f}")
    print(f"Final Equity:          ${final_equity:.2f}")
    print(f"Return on Investment:  {roi:.4f}%")
    print("------------------------")
    
    # Debug info from C++ engine
    print(f"Final Leader Imbalance (C++ internal state): {strategy.get_leader_imbalance():.4f}")

if __name__ == "__main__":
    run_simulation()