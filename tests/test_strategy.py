import time

import engine_core

print("--- TEST PAIR TRADING STRATEGY ---")

# 1. Initialize Strategy
# Thrshold 0.7: If imbalance exceeds 0.7 (or drops below -0.7), trigger signal.
try:
    strategy = engine_core.PairStrategy(0.7)
    print("✅ C++ module loaded successfully.")
except AttributeError:
    print(
        "❌ ERROR: The engine_core module does not contain PairStrategy. Did you recompile?"
    )
    exit()

# Constants for readability
LEADER = 0  # BTC
FOLLOWER = 1  # ETH
BID = True
ASK = False

# 2. Neutral Situation
print("\n[T=0] Calm Market...")
# Insert a buy order and a sell order on the Leader
strategy.on_market_data(LEADER, 100.0, 1.0, BID)
strategy.on_market_data(LEADER, 101.0, 1.0, ASK)

# Check signals and OBI
signal = strategy.check_signals()
obi = strategy.get_leader_imbalance()
print(f"Leader OBI: {obi:.2f} -> Signal: {signal} (Hold)")

# 3. Leader Pumping Situation (BTC)
print("\n[T=1] Large buy orders arriving on BTC (Leader)...")

# Simulate 10 large buy orders on BTC
for _ in range(10):
    strategy.on_market_data(LEADER, 100.0, 5.0, BID)

# Now the BTC book is full of Bids. The Imbalance should be high.
obi = strategy.get_leader_imbalance()
signal = strategy.check_signals()

print(f"Leader OBI: {obi:.4f}")

if signal == 1:
    print(f"✅ SIGNAL GENERATED: {signal} (BUY ETH)")
    print("Lead-Lag logic confirmed: Pressure on BTC -> Buy ETH.")
elif signal == 0:
    print(f"❌ No signal generated, but expected 1. OBI: {obi:.4f}")
else:
    print(f"⚠️ UNEXPECTED SIGNAL: {signal}")

# 4. Leader Crash Situation (Panic Selling)
print("\n[T=2] Panic Selling on BTC (Reset Strategy)...")
strategy = engine_core.PairStrategy(0.7)  # Reset to clear the books

# Insert many sellers (ASKS)
for _ in range(20):
    strategy.on_market_data(LEADER, 100.0, 5.0, ASK)

obi = strategy.get_leader_imbalance()
signal = strategy.check_signals()
print(f"Leader OBI: {obi:.4f} -> Signal: {signal}")

if signal == -1:
    print("✅ SIGNAL GENERATED: -1 (SELL ETH)")
    print("Lead-Lag logic confirmed: BTC Crash -> Sell ETH.")
else:
    print("❌ Errore nel segnale di vendita.")
