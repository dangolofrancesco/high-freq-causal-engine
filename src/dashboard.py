import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from engine.storage import MarketDataDB
from engine.backtest_runner import BacktestRunner

# Page Configuration
st.set_page_config(page_title="HFT Causal Engine Dashboard", layout="wide")
st.title("High-Frequency Causal Engine Dashboard")
st.markdown("Visual analysis of Lead-Lag correlation between Bitcoin (Leader) and Ethereum (Follower).")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    db = MarketDataDB()
    con = db.get_connection()
    # Load more data to see trends better
    df = con.execute("SELECT * FROM trades ORDER BY timestamp ASC LIMIT 10000").df()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"DB Error: {e}")
    st.stop()

# --- 2. SIDEBAR CONFIGURATION ---
st.sidebar.header("Strategy Parameters")
threshold = st.sidebar.slider("OBI Threshold (Sensitivity)", 0.1, 1.0, 0.3, 0.05, 
                              help="How imbalanced should BTC's order book be to trigger an order on ETH?")
initial_capital = st.sidebar.number_input("Initial Capital ($)", value=10000)

# --- 3. BACKTEST EXECUTION (PARALLEL) ---
symbols = df['symbol'].unique()
leader_symbol = next((s for s in symbols if 'BTC' in s), None)
follower_symbol = next((s for s in symbols if 'ETH' in s), None)

if not leader_symbol or not follower_symbol:
    st.error("Insufficient data: BTC and ETH are required.")
    st.stop()

with st.spinner("Running strategy simulations..."):
    # Initialize runner
    runner = BacktestRunner(threshold=threshold, initial_capital=initial_capital)
    
    # Model 1: Long Only
    res_long = runner.run(df, leader_symbol, follower_symbol, allow_short_selling=False)
    
    # Model 2: Long + Short
    res_short = runner.run(df, leader_symbol, follower_symbol, allow_short_selling=True)

# --- 4. COMPARISON STATISTICS ---
st.header("Strategy Performance Comparison")

# Metrics
col1, col2 = st.columns(2)
col1.metric("Base Model (Long Only)", f"{res_long['roi']:.2f}% ROI", delta_color="off")
col2.metric("Advanced Model (Long/Short)", f"{res_short['roi']:.2f}% ROI", 
            delta=f"{res_short['roi'] - res_long['roi']:.2f}% vs Base")

st.divider()

# --- 5. VISUALIZATION ---

# Create subplot with comparison (Enable dual axis for Row 1 and Row 3)
fig = make_subplots(
    rows=4, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.1,  # Increased spacing between charts
    row_heights=[0.3, 0.2, 0.3, 0.2],  # Increased height for OBI charts (rows 2 & 4)
    specs=[[{"secondary_y": True}], [{}], [{"secondary_y": True}], [{}]],
    subplot_titles=("Model A: Long Only", "Model A: OBI", "Model B: Bidirectional (Long & Short)", "Model B: OBI")
)

# --- CHART A (LONG ONLY) ---
# Price Line Follower (ETH) - Left Axis
fig.add_trace(go.Scatter(
    x=res_long['history_timestamps'], 
    y=res_long['history_follower_price'], 
    mode='lines', name=f'{follower_symbol} (Follower)', 
    line=dict(color='#1f77b4', width=2)
), row=1, col=1, secondary_y=False)

# Price Line Leader (BTC) - Right Axis
fig.add_trace(go.Scatter(
    x=res_long['history_timestamps'], 
    y=res_long['history_leader_price'], 
    mode='lines', name=f'{leader_symbol} (Leader)', 
    line=dict(color='#ff7f0e', width=1, dash='dot'), opacity=0.7
), row=1, col=1, secondary_y=True)

# Signals A - Row 1
fig.add_trace(go.Scatter(
    x=res_long['signals_buy']['x'], 
    y=res_long['signals_buy']['y'], 
    mode='markers', 
    marker=dict(symbol='triangle-up', color='green', size=12), 
    name='Buy (Long)',
    text=res_long['signals_buy']['desc'],
    hovertemplate="%{text}<extra></extra>"
), row=1, col=1, secondary_y=False)

fig.add_trace(go.Scatter(
    x=res_long['signals_sell']['x'], 
    y=res_long['signals_sell']['y'], 
    mode='markers', 
    marker=dict(symbol='triangle-down', color='black', size=12), 
    name='Exit (Long)',
    text=res_long['signals_sell']['desc'],
    hovertemplate="%{text}<extra></extra>"
), row=1, col=1, secondary_y=False)

# --- OBI A - Row 2 ---
fig.add_trace(go.Scatter(
    x=res_long['history_timestamps'], 
    y=res_long['history_leader_obi'], 
    mode='lines', name='OBI (A)',    
    line=dict(color='#9467bd', width=1), 
    fill='tozeroy', showlegend=False
), row=2, col=1)
fig.add_hline(y=threshold, line_dash="dot", row=2, col=1, line_color="green")
fig.add_hline(y=-threshold, line_dash="dot", row=2, col=1, line_color="red")
fig.update_yaxes(range=[-1.1, 1.1], title_text="OBI", row=2, col=1)

# --- CHART B (LONG + SHORT) ---
# Price Line Follower (ETH) - Left Axis
fig.add_trace(go.Scatter(
    x=res_short['history_timestamps'], 
    y=res_short['history_follower_price'], 
    mode='lines', name=f'{follower_symbol} (Follower)', 
    line=dict(color='#1f77b4', width=2),
    showlegend=False
), row=3, col=1, secondary_y=False)

# Price Line Leader (BTC) - Right Axis
fig.add_trace(go.Scatter(
    x=res_short['history_timestamps'], 
    y=res_short['history_leader_price'], 
    mode='lines', name=f'{leader_symbol} (Leader)', 
    line=dict(color='#ff7f0e', width=1, dash='dot'), opacity=0.7,
    showlegend=False
), row=3, col=1, secondary_y=True)

# Signals B - Row 3
fig.add_trace(go.Scatter(
    x=res_short['signals_buy']['x'], 
    y=res_short['signals_buy']['y'], 
    mode='markers', 
    marker=dict(symbol='triangle-up', color='green', size=12), 
    name='Long / Cover',
    text=res_short['signals_buy']['desc'],
    hovertemplate="%{text}<extra></extra>"
), row=3, col=1, secondary_y=False)

fig.add_trace(go.Scatter(
    x=res_short['signals_sell']['x'], 
    y=res_short['signals_sell']['y'], 
    mode='markers', 
    marker=dict(symbol='triangle-down', color='red', size=12), 
    name='Short / Close',
    text=res_short['signals_sell']['desc'],
    hovertemplate="%{text}<extra></extra>"
), row=3, col=1, secondary_y=False)

# Axis Configuration & Cleaner Grid
# Left Y-Axis (Follower) - Clean grid
fig.update_yaxes(title_text=f"{follower_symbol}", secondary_y=False, showgrid=True, gridcolor='lightgray', zeroline=False)
# Right Y-Axis (Leader) - No grid to avoid clutter
fig.update_yaxes(title_text=f"{leader_symbol}", secondary_y=True, showgrid=False, zeroline=False)

# OBI Axes - Clean range
fig.update_yaxes(range=[-1.1, 1.1], title_text="OBI", row=2, col=1)
fig.update_yaxes(range=[-1.1, 1.1], title_text="OBI", row=4, col=1)

# General Layout
fig.update_layout(
    height=1200,  # Increased total height for better view
    title_text="Strategy Execution Comparison",
    template="plotly_white",  # Cleaner white background
    hovermode="x unified",
    # Legend vertical on the right
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
)
fig.add_trace(go.Scatter(
    x=res_short['history_timestamps'], 
    y=res_short['history_leader_obi'], 
    mode='lines', name='OBI (B)', 
    line=dict(color='#9467bd', width=1), 
    fill='tozeroy',
    showlegend=False
), row=4, col=1)
fig.add_hline(y=threshold, line_dash="dot", row=4, col=1, line_color="green")
fig.add_hline(y=-threshold, line_dash="dot", row=4, col=1, line_color="red")
fig.update_yaxes(range=[-1.1, 1.1], row=4, col=1)

fig.update_layout(height=800, title_text="Strategy Execution Comparison")
st.plotly_chart(fig, use_container_width=True)

# --- 6. EQUITY CURVE COMPARISON ---
st.subheader(" Performance Analysis (Equity Curve)")
fig_eq = go.Figure()
fig_eq.add_trace(go.Scatter(
    x=res_long['history_timestamps'], 
    y=res_long['history_equity'], 
    mode='lines', name='Equity Long Only', 
    line=dict(color='blue')
))
fig_eq.add_trace(go.Scatter(
    x=res_short['history_timestamps'], 
    y=res_short['history_equity'], 
    mode='lines', name='Equity Long/Short', 
    line=dict(color='purple')
))

fig_eq.update_layout(
    title="Equity Curve Comparison",
    xaxis_title="Time",
    yaxis_title="Account Value ($)",
    hovermode="x unified"
)
st.plotly_chart(fig_eq, use_container_width=True)

# --- 7. DETAILED METRICS GRID ---
st.divider()
st.subheader(" Detailed Metrics Comparison")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Model A: Long Only")
    c1, c2, c3 = st.columns(3)
    c1.metric("Trades", res_long['total_trades'])
    c2.metric("Final Position", f"{res_long['final_position']}")
    c3.metric("Final Equity", f"${res_long['final_equity']:.2f}")

with col_right:
    st.markdown("### Model B: Long/Short")
    c1, c2, c3 = st.columns(3)
    c1.metric("Trades", res_short['total_trades'])
    c2.metric("Final Position", f"{res_short['final_position']}")
    c3.metric("Final Equity", f"${res_short['final_equity']:.2f}")

st.info("""
**Comparison Guide:**
- **Model A (Long Only):** Traditional strategy. Buys when BTC pressure is high, closes when pressure reverses. No profit from downtrends.
- **Model B (Bidirectional):** Advanced strategy. Can profit from downtrends by Short Selling (Selling high, buying low).
- **OBI (Order Book Imbalance):** Indicator that measures buying/selling pressure. Values > 0 indicate buy pressure, < 0 indicate sell pressure. The thresholds (green/red lines) trigger trade signals.
- **Equity Curve:** The chart above shows how your account value grows over time for both strategies.
""")


# --- 6. STRATEGIC ANALYSIS SECTION ---
st.markdown("---")
st.header(" Strategic Analysis & Performance Report")

with st.expander(" Read Detailed Explanation", expanded=True):
    st.markdown("""
    This dashboard compares two execution logic variations based on the same C++ Causal Signal (OBI):
    
    * **Model A (Long Only - Risk Averse):** This strategy mimics a traditional spot trader. It buys ETH when BTC shows buying pressure. When BTC crashes, it sells ETH to protect capital (Cash). 
        * *Result:* During a market crash, the Equity Curve is flat (preserves capital).
    * **Model B (Bidirectional - Hedge Fund Style):** This strategy utilizes **Short Selling**. When the signal turns negative, it doesn't just close the Long position; it **flips** to Short.
        * *Result:* During a market crash, the Equity Curve **rises** because the strategy profits from the decline.


    ### Strategies for improvement 
    While Model B outperforms Model A, it can be further optimized:
    
    * ** Exit on Neutral (Mean Reversion):** Currently, Model B holds the Short position forever until a Buy signal appears. A better approach is to close the position when the OBI returns to the "Neutral Zone" (e.g., between -0.1 and +0.1), locking in profits earlier.
    * **Gauging Volatility (Z-Score):** Instead of a fixed threshold (e.g., 0.3), we should use a dynamic threshold based on standard deviation ($Z = (x - \mu) / \sigma$). This adapts the bot to calm vs. chaotic market conditions.
    * ** Transaction Costs:** This simulation assumes zero fees. In a real environment, flipping positions frequently incurs taker fees. We must incorporate a cost model to ensure the alpha survives real-world friction.
    """)

