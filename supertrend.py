import ccxt
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)
# pd.set_option('display.expand_frame_repr', False)

import warnings
warnings.filterwarnings('ignore')

from datetime import datetime
import time

exchange = ccxt.binance()

def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    return data[['high-low', 'high-pc', 'low-pc']].max(axis=1)


def atr(data, period=14):
    data['tr'] = tr(data)
    return data['tr'].rolling(period).mean()


def supertrend(df, period=7, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]

    return df


in_position = False

def check_buy_sell_signals(df):
    global in_position

    print('Checking for buys and sell')
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend, buy")
        if not in_position:
            print('buy')
            in_position = True

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        print("Changed to downtrend, sell")
        if in_position:
            print('Sell')
            in_position = False


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1d', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)

    check_buy_sell_signals(supertrend_data)


schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)