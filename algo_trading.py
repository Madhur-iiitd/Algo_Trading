import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    ema_up = up.ewm(com=window-1, adjust=False).mean()
    ema_down = down.ewm(com=window-1, adjust=False).mean()

    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Replace 'Axis Bank Limited' with a valid stock ticker symbol
symbol = 'PAYTM.NS'  # Example: Apple Inc.

# Download daily stock data
stock_data_daily = yf.download(symbol, start='2022-01-01', end=datetime.today().strftime('%Y-%m-%d'))

# Ensure 'Close' column exists
if 'Close' not in stock_data_daily.columns:
    print("Unable to retrieve 'Close' data.")
    exit()

# Calculate RSI for the daily 'Close' column
stock_data_daily['Daily_RSI'] = calculate_rsi(stock_data_daily)
stock_daily_2023_onwards = stock_data_daily[stock_data_daily.index.year >= 2023]

# Download weekly stock data
stock_data_weekly = yf.download(symbol, start='2022-01-01', interval='1wk', end=datetime.today().strftime('%Y-%m-%d'))
stock_data_weekly['Weekly_RSI'] = calculate_rsi(stock_data_weekly) 

# Ensure 'Close' column exists
if 'Close' not in stock_data_weekly.columns:
    print("Unable to retrieve 'Close' data.")
    exit()

# Reset index for merging
stock_data_daily.reset_index(inplace=True)
stock_data_weekly.reset_index(inplace=True)

# Merge the dataframes on 'Date' column
merged_data_total = pd.merge(stock_data_daily, stock_data_weekly[['Date', 'Weekly_RSI']], on='Date', how='left')

# Forward fill the NaN values in 'Weekly_RSI'
merged_data_total['Weekly_RSI'].fillna(method='ffill', inplace=True)

# Set 'Date' as index again
merged_data_total.set_index('Date', inplace=True)

merged_data = merged_data_total[merged_data_total.index.year >= 2023]

merged_data['Signal'] = 0

# buy_signal = 0
crossed_below_30 = 0
crossed_above_70 = 0

first_row = merged_data.iloc[0]
if first_row.Daily_RSI < 35 and first_row.Weekly_RSI > 50:
    crossed_below_30 = 1

if first_row.Daily_RSI > 75 and first_row.Weekly_RSI > 50:
    crossed_above_70 = 1

for row in merged_data.itertuples():
    if row.Daily_RSI<35 and row.Weekly_RSI>50 and crossed_below_30==0:
        crossed_below_30=1

    if row.Daily_RSI>35 and row.Weekly_RSI>50 and crossed_below_30==1:
        crossed_below_30=0
        merged_data.at[row.Index, 'Signal'] = 1

for row in merged_data.itertuples():
    if row.Daily_RSI>75 and row.Weekly_RSI>50 and crossed_above_70==0:
        crossed_above_70=1

    if row.Daily_RSI<75 and row.Weekly_RSI>50 and crossed_above_70==1:
        crossed_above_70=0
        merged_data.at[row.Index, 'Signal'] = 2

n_signal_1 = merged_data[merged_data.Signal == 1]
n_signal_2 = merged_data[merged_data.Signal == 2]

# Print signals to CSV
n_signal_1.to_csv('buy_signals.csv')
n_signal_2.to_csv('sell_signals.csv')

# Print merged data to CSV
merged_data.to_csv('merged_data.csv')

# Create subplots with shared x-axis
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=["RSI", "Buy and Sell Signals"])

# Plot RSI
fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data['Daily_RSI'], name='Daily RSI', line=dict(color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data['Weekly_RSI'], name='Weekly RSI', line=dict(color='green')), row=1, col=1)

# Highlight buy and sell signals
buy_signals = merged_data[merged_data['Signal'] == 1]
sell_signals = merged_data[merged_data['Signal'] == 2]

fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Daily_RSI'], mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Daily_RSI'], mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

# Create a trace for buy signals
fig.add_trace(go.Scatter(x=n_signal_1.index, y=n_signal_1['Daily_RSI'], mode='markers', name='Buy Signals', marker=dict(color='green', symbol='triangle-up', size=10)), row=2, col=1)

# Create a trace for sell signals
fig.add_trace(go.Scatter(x=n_signal_2.index, y=n_signal_2['Daily_RSI'], mode='markers', name='Sell Signals', marker=dict(color='red', symbol='triangle-down', size=10)), row=2, col=1)

# Update layout
fig.update_layout(
    title='RSI with Buy and Sell Signals',
    xaxis=dict(title='Date'),
    yaxis=dict(title='RSI', range=[0, 100]),
    showlegend=False  # Show legend in a separate box
)

# Show the interactive plot
fig.show()



### Main Code##################################
