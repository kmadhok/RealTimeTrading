

import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

from datetime import datetime
from configparser import ConfigParser
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.requests import CryptoTradesRequest
from alpaca.data.requests import CryptoSnapshotRequest
from alpaca.data.requests import CryptoLatestOrderbookRequest
from alpaca.data.historical import CryptoHistoricalDataClient


# Get the specified credentials.
# api_key = 'AK8O18GBTJC8LFF5WSXW'
# secret_key = '5zyGVsRKxJiPSnYDxFIFrSABOFjegDwhVG3WT0bb'


# Initialize the CryptoHistoricalDataClient.
crypto_data_client = CryptoHistoricalDataClient(
    api_key=api_key,
    secret_key=secret_key
)

# Now let's define a request using the CryptoBarsRequest class.
# Limit the number of bars to 1000 and set the timeframe to 1 hour.
request = CryptoBarsRequest(
    symbol_or_symbols=['BTC/USD'],
    start=datetime(year=2021, month=1, day=1).date(),
    end=datetime(year=2023, month=1, day=9).date(),
    timeframe=TimeFrame.Day,
    limit=1000
)

# Now let's get the data.
bar_data = crypto_data_client.get_crypto_bars(request_params=request)

bar_data.df

df_btc = bar_data.df

df_btc.reset_index(inplace=True)

df_btc.set_index('timestamp', inplace=True)

# print(df_btc.head(5))

# Twitter data added to backtest the strategy - will combine this with the moving average dataframes
df_sentiment = pd.read_csv('df_sentiment_by_day.csv')

df_btc.index = pd.to_datetime(df_btc.index).date

df_sentiment['date'] = pd.to_datetime(df_sentiment['day'])
df_sentiment.set_index('date', inplace=True)

# Now merge using the indices
df_btc_merged = df_btc.merge(df_sentiment[['strong_positive']], left_index=True, right_index=True, how='left')

print(df_btc_merged.head(5))

df_btc_merged_cleaned = df_btc_merged.dropna()

def calculate_moving_averages_with_sentiment(merged_data):
    # Calculate moving averages
    signals = pd.DataFrame(index=merged_data.index)
    signals['short_ma'] = merged_data['close'].rolling(window=20).mean()
    signals['long_ma'] = merged_data['close'].rolling(window=50).mean()

    # Twitter sentiment signals are already part of the merged data
    signals['twitter_sentiment'] = merged_data['strong_positive']

    # Initialize orders column to 0 (neutral/hold)
    signals['orders'] = 0

    # Generate buy orders: When short-term MA crosses above long-term MA AND Twitter sentiment is positive
    buy_conditions = (signals['short_ma'] > signals['long_ma']) & (signals['twitter_sentiment'] == 1)
    signals.loc[buy_conditions, 'orders'] = 1

    # Generate sell orders: When long-term MA is above short-term MA AND Twitter sentiment is neutral (0)
    sell_conditions = (signals['long_ma'] > signals['short_ma']) & (signals['twitter_sentiment'] == 0)
    signals.loc[sell_conditions, 'orders'] = -1

    return signals

# Apply the function to your merged and cleaned DataFrame
signals = calculate_moving_averages_with_sentiment(df_btc_merged_cleaned)

# Let's check the first few rows to ensure it worked
print(signals.tail())

signals = signals.reindex(df_btc_merged_cleaned.index)

# Now let's change values of the orders column to 0 (neutral/hold), 1 (buy), or -1 (sell)
signals['orders'] = signals['orders'].replace(to_replace=1, value='buy')
signals['orders'] = signals['orders'].replace(to_replace=-1, value='sell')
signals['orders'] = signals['orders'].replace(to_replace=0, value='hold')
df_reset = signals.reset_index().rename(columns={'index': 'date'})
df_reset['symbol'] = 'BTC/USD'
df_reset['side'] = df_reset['orders'].apply(lambda x: 'BUY' if x == 'buy' else ('SELL' if x == 'sell' else 'N/A'))
# drop 'N/A' rows
df_reset = df_reset[df_reset['side'] != 'N/A']
# Adding new columns with specified values
df_reset['type'] = 'MARKET'  # Assigning 1 to every row in 'qty'
df_reset['order_class'] = 'SIMPLE'  # Assigning 1 to every row in 'qty'
df_reset['qty'] = 1  # Assigning 1 to every row in 'qty'
df_reset['time_in_force'] = 'gtc'  # Assigning 'gtc' to every row in 'time_in_force'
df_reset['extended_hours'] = False  # Assigning False to every row in 'extended_hours'
drop_columns = ['short_ma', 'long_ma', 'twitter_sentiment','orders']
df_reset.drop(columns=drop_columns, inplace=True)

df_reset['running_total'] = 0
btc_owned = 0

# Calculate the running total
for index, row in df_reset.iterrows():
    if row['side'] == 'BUY':
        btc_owned += row['qty']
    elif row['side'] == 'SELL' and btc_owned >= row['qty']:
        btc_owned -= row['qty']
    df_reset.at[index, 'running_total'] = btc_owned

# Filter out invalid sell orders
valid_df = df_reset.drop(df_reset[(df_reset['side'] == 'SELL') & (df_reset['running_total'] < df_reset['qty'])].index)

# Lets export the signals to a csv file
valid_df.to_csv('signals.csv', index=False)
valid_df.head(5)




api_key = 'PKI42P8BGVCADSK8LO6I'
secret_key = 'CGh7nXbPWH0eIbZVLUe5BOdZUr6BTaglrDUDjxsy'