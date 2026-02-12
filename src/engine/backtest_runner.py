"""
Backtest Runner Module
Handles the execution of trading strategy backtests with C++ engine integration.
"""

import engine_core
from typing import Dict, List, Tuple
import pandas as pd


class BacktestRunner:
    """Executes a pairs trading backtest using the C++ engine."""
    
    def __init__(self, threshold: float, initial_capital: float):
        """
        Initialize the backtest runner.
        
        Args:
            threshold: OBI threshold for signal generation
            initial_capital: Starting capital for trading
        """
        self.threshold = threshold
        self.initial_capital = initial_capital
        # Strategy will be initialized per run to ensure clean state
        
    def run(self, df: pd.DataFrame, leader_symbol: str, follower_symbol: str, allow_short_selling: bool = False) -> Dict:
        """
        Execute the backtest on historical data.
        
        Args:
            df: DataFrame with columns: timestamp, symbol, price, quantity, side
            leader_symbol: Symbol of the leader asset (e.g., 'BTC-USD')
            follower_symbol: Symbol of the follower asset (e.g., 'ETH-USD')
            allow_short_selling: If True, enables short selling strategies.
            
        Returns:
            Dictionary containing simulation results.
        """
        # Re-initialize strategy to ensure clean state for each run
        self.strategy = engine_core.PairStrategy(self.threshold)
        
        # Initialize tracking variables
        history_timestamps = []
        history_leader_obi = []
        history_follower_price = []
        history_leader_price = []
        history_equity = []
        
        signals_buy = {'x': [], 'y': [], 'desc': []}
        signals_sell = {'x': [], 'y': [], 'desc': []}
        
        # Position tracking: 0=Flat, 1=Long, -1=Short
        position = 0
        cash = self.initial_capital
        last_leader_price = 0.0
        
        # Process each market data tick
        for row in df.itertuples():
            symbol_type = 0 if row.symbol == leader_symbol else 1
            is_bid = True if row.side == 'buy' else False
            
            # Update leader price tracking
            if symbol_type == 0:
                last_leader_price = row.price
            
            # Update C++ engine
            self.strategy.on_market_data(symbol_type, row.price, row.quantity, is_bid)
            
            # Record data when follower updates (for synchronization)
            if symbol_type == 1 and last_leader_price > 0:
                current_price = row.price
                current_obi = self.strategy.get_leader_imbalance()
                
                history_timestamps.append(row.timestamp)
                history_leader_obi.append(current_obi)
                history_follower_price.append(current_price)
                history_leader_price.append(last_leader_price)
                
                # Calculate and store current equity
                # Equity = Cash + (Position * Current Price)
                # Works for short too: if position is -1, we subtract the cost to cover
                current_equity = cash + (position * current_price)
                history_equity.append(current_equity)
                
                # Check for trading signals
                signal = self.strategy.check_signals()
                
                if allow_short_selling:
                    # --- SHORT SELLING LOGIC ---
                    if signal == 1: # BUY SIGNAL
                        if position == 0: # Flat -> Long
                            position = 1
                            cash -= current_price
                            self._record_signal(signals_buy, row.timestamp, current_price, current_obi, "Long Entry", quantity=1.0)
                        elif position == -1: # Short -> Long (Reverse)
                            position = 1
                            cash -= (current_price * 2) # Cover short + Go long
                            self._record_signal(signals_buy, row.timestamp, current_price, current_obi, "Short Cover & Long Entry", quantity=2.0)
                            
                    elif signal == -1: # SELL SIGNAL
                        if position == 0: # Flat -> Short
                            position = -1
                            cash += current_price # Receive cash from short sale
                            self._record_signal(signals_sell, row.timestamp, current_price, current_obi, "Short Entry", quantity=1.0)
                        elif position == 1: # Long -> Short (Reverse)
                            position = -1
                            cash += (current_price * 2) # Sell long + Go short
                            self._record_signal(signals_sell, row.timestamp, current_price, current_obi, "Long Close & Short Entry", quantity=2.0)
                
                else:
                    # --- LONG ONLY LOGIC ---
                    if signal == 1 and position == 0: # Buy
                        position = 1
                        cash -= current_price
                        self._record_signal(signals_buy, row.timestamp, current_price, current_obi, "Long Entry", quantity=1.0)
                        
                    elif signal == -1 and position > 0: # Sell to Close
                        position = 0
                        cash += current_price
                        self._record_signal(signals_sell, row.timestamp, current_price, current_obi, "Long Close", quantity=1.0)
        
        # Calculate final metrics
        final_price = history_follower_price[-1] if history_follower_price else 0
        final_equity = cash + (position * final_price)
        roi = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        total_trades = len(signals_buy['x']) + len(signals_sell['x'])
        
        return {
            'history_timestamps': history_timestamps,
            'history_leader_obi': history_leader_obi,
            'history_follower_price': history_follower_price,
            'history_leader_price': history_leader_price,
            'history_equity': history_equity,
            'signals_buy': signals_buy,
            'signals_sell': signals_sell,
            'final_position': position,
            'final_cash': cash,
            'final_equity': final_equity,
            'roi': roi,
            'total_trades': total_trades
        }

    def _record_signal(self, signal_dict, timestamp, price, obi, action_type, quantity=1.0):
        """Helper to record signal details."""
        signal_dict['x'].append(timestamp)
        signal_dict['y'].append(price)
        signal_dict['desc'].append(
            f"<b>{action_type}</b><br>"
            f"Price: ${price:.2f}<br>"
            f"Quantity: {quantity}<br>"
            f"Leader OBI: {obi:.2f}<br>"
            f"Threshold: ±{self.threshold}"
        )
