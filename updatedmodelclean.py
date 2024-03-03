# First, let's wrap the given code into a function that can be called when run in another file.
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
api_key = 'AK8O18GBTJC8LFF5WSXW'
secret_key = '5zyGVsRKxJiPSnYDxFIFrSABOFjegDwhVG3WT0bb'


def tradestrategy():
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
    api_key = 'AK8O18GBTJC8LFF5WSXW'
    secret_key = '5zyGVsRKxJiPSnYDxFIFrSABOFjegDwhVG3WT0bb'

    # Initialize the CryptoHistoricalDataClient.
    crypto_data_client = CryptoHistoricalDataClient(
        api_key=api_key,
        secret_key=secret_key
    )

    # Now let's define a request using the CryptoBarsRequest class.
    request = CryptoBarsRequest(
        symbol_or_symbols=['BTC/USD'],
        start=datetime(year=2021, month=1, day=1).date(),
        end=datetime(year=2023, month=1, day=9).date(),
        timeframe=TimeFrame.Day,
        limit=1000
    )

    # Get the data.
    bar_data = crypto_data_client.get_crypto_bars(request_params=request)
    df_btc = bar_data.df
    df_btc.reset_index(inplace=True)
    df_btc.set_index('timestamp', inplace=True)

    # Twitter data added to backtest the strategy
    df_sentiment = pd.read_csv('df_sentiment_by_day.csv')
    df_btc.index = pd.to_datetime(df_btc.index).date
    df_sentiment['date'] = pd.to_datetime(df_sentiment['day'])
    df_sentiment.set_index('date', inplace=True)

    # Merge using the indices
    df_btc_merged = df_btc.merge(df_sentiment[['strong_positive']], left_index=True, right_index=True, how='left')
    df_btc_merged_cleaned = df_btc_merged.dropna()

    def calculate_moving_averages_with_sentiment(merged_data):
        signals = pd.DataFrame(index=merged_data.index)
        signals['short_ma'] = merged_data['close'].rolling(window=20).mean()
        signals['long_ma'] = merged_data['close'].rolling(window=50).mean()
        signals['twitter_sentiment'] = merged_data['strong_positive']
        signals['orders'] = 0

        # Generate buy and sell orders based on conditions
        buy_conditions = (signals['short_ma'] > signals['long_ma']) & (signals['twitter_sentiment'] == 1)
        signals.loc[buy_conditions, 'orders'] = 1
        sell_conditions = (signals['long_ma'] > signals['short_ma']) & (signals['twitter_sentiment'] == 0)
        signals.loc[sell_conditions, 'orders'] = -1
        return signals

    signals = calculate_moving_averages_with_sentiment(df_btc_merged_cleaned)
    signals = signals.reindex(df_btc_merged_cleaned.index)

    # Change values of the orders column
    signals['orders'] = signals['orders'].replace(to_replace=1, value='buy')
    signals['orders'] = signals['orders'].replace(to_replace=-1, value='sell')
    signals['orders'] = signals['orders'].replace(to_replace=0, value='hold')
    df_reset = signals.reset_index().rename(columns={'index': 'date'})
    df_reset['symbol'] = 'BTC/USD'
    df_reset['side'] = df_reset['orders'].apply(lambda x: 'BUY' if x == 'buy' else ('SELL' if x == 'sell' else 'N/A'))
    df_reset = df_reset[df_reset['side'] != 'N/A']
    df_reset['type'] = 'MARKET'
    df_reset['order_class'] = 'SIMPLE'
    df_reset['qty'] = 0.01
    df_reset['time_in_force'] = 'gtc'
    df_reset['extended_hours'] = False
    drop_columns = ['short_ma', 'long_ma', 'twitter_sentiment', 'orders']
    df_reset.drop(columns=drop_columns, inplace=True)

    # Calculate the running total
    btc_owned = 0
    for index, row in df_reset.iterrows():
        if row['side'] == 'BUY':
            btc_owned += row['qty']
        elif row['side'] == 'SELL' and btc_owned >= row['qty']:
            btc_owned -= row['qty']
        df_reset.at[index, 'running_total'] = btc_owned

    # Filter out invalid sell orders
    valid_df = df_reset.drop(df_reset[(df_reset['side'] == 'SELL') & (df_reset['running_total'] < df_reset['qty'])].index)

    # Export the signals to a csv file
    valid_df.to_csv('signals.csv', index=False)

