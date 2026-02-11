# High-Frequency Causal Pair-Trading Engine (HF-CPTE)

HF-CPTE is a high-performance quantitative trading framework designed to identify and exploit non-linear causal relationships between financial assets. Unlike traditional cointegration-based pair trading, this engine leverages Causal Discovery algorithms to detect lead-lag relationships in high-frequency data (HFT), aiming to predict short-term price movements of a "follower" asset based on the "leader" asset's signals.

The project is built with a production-first mindset, prioritizing computational efficiency, rigorous statistical validation, and modern software engineering practices required by hedge funds and open-source organizations.

## Strategy Deep Dive

### 1. Event-Driven Data Ingestion (The Time Machine)

We simulate a real-time trading environment using an **Event-Driven Backtesting** approach.

- **Mechanism:** Instead of loading the entire dataset into memory at once (Vectorized), we fetch historical trades from the database and iterate through them strictly chronologically (`ORDER BY timestamp ASC`).
    
- **Constraint:** The engine sees only the current tick and the past. It has zero knowledge of future price movements, eliminating **Look-Ahead Bias**.
    

### 2. Tick Classification & Normalization

For every incoming market event (tick), the Python "Orchestrator" classifies the data before feeding it to the C++ Engine:

- **Asset Role:** Is this tick regarding the **Leader** (e.g., BTC, ID `0`) or the **Follower** (e.g., ETH, ID `1`)?
    
- **Side (Aggressor):** Does this trade represent a `buy` (Market Buy) or a `sell` (Market Sell)? A 'buy' side indicates aggressive buying pressure.
    

### 3. Market State Reconstruction (The Order Book)

The C++ Engine receives the tick and updates its internal **Limit Order Book** view.

- **Not a Ledger:** This is _not_ our personal account balance. It is a reconstruction of the **Market's Supply and Demand**.
    
- **Logic:** We update the lists of **Bids** (Buy Orders) and **Asks** (Sell Orders) to reflect the liquidity available at that specific millisecond.
    

### 4. Signal Generation (OBI & Sensitivity)

The engine calculates the **Order Book Imbalance (OBI)** to gauge market pressure.

- **Formula:**
    
    $$OBI = \frac{Volume_{Bid} - Volume_{Ask}}{Volume_{Bid} + Volume_{Ask}}$$
    
- **Range:** The result is between `-1` (Pure Selling Pressure) and `+1` (Pure Buying Pressure).
    
- **Threshold (Sensitivity):** We apply a filter (e.g., `0.7`).
    
    - If $OBI > +0.7$: Strong buy signal.
        
    - If $OBI < -0.7$: Strong sell signal.
        
    - Inside range $[-0.7, +0.7]$: Noise/Equilibrium (No signal).
        

### 5. Causal Execution Logic (Lead-Lag Alpha)

This is the core "Alpha" of the strategy. We observe the **Leader** to trade the **Follower**.

- **Condition:** We check the signal **only** when processing a Leader (BTC) tick.
    
- **Action:**
    
    - If **Leader OBI** is Positive ($> Threshold$): We anticipate the Follower will rise. **Action: BUY Follower.**
        
    - If **Leader OBI** is Negative ($< -Threshold$): We anticipate the Follower will fall. **Action: SELL Follower.**
        
- **Latency Arbitrage:** We aim to enter the Follower position during the tiny lag window before it catches up to the Leader.
    

### 6. Portfolio Management (State Tracking)

The Python Orchestrator updates the internal portfolio state based on the signals received from C++.

- **Cash:** Available capital (USD).
    
- **Position (Inventory):**
    
    - `0`: Flat (No exposure).
        
    - `+N`: Long (Holding N units of ETH).
        
    - `-N`: Short (Owe N units of ETH - _advanced, usually simplified to Long/Flat in basic backtests_).
        
- **Trade Count:** Metric tracking the frequency of activity.
    

### 7. Performance Analytics (ROI)

At the end of the simulation, we calculate the **Return on Investment**.

- **Equity Calculation:**
    
    $$Equity_{Final} = Cash_{Final} + (Position_{Final} \times Price_{Last})$$
    
- **ROI Formula:**
    
    $$ROI (\%) = \left( \frac{Equity_{Final} - Capital_{Initial}}{Capital_{Initial}} \right) \times 100$$
    
    - **Positive ROI:** The strategy generated profit.
        
    - **Negative ROI:** The strategy resulted in a loss.



