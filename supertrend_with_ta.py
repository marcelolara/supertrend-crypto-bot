import ccxt
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import schedule
import time
import warnings

pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)

warnings.filterwarnings('ignore')

exchange = ccxt.binance()


in_position = False


def check_buy_sell_signals(df):
    global in_position

    print('Checking for buys and sell')
    print(df.tail(2))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['super_trend'][previous_row_index] and df['super_trend'][last_row_index]:
        print("Changed to uptrend, buy")
        if not in_position:
            print('buy')
            in_position = True

    if df['super_trend'][previous_row_index] and not df['super_trend'][last_row_index]:
        print("Changed to downtrend, sell")
        if in_position:
            print('Sell')
            in_position = False


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=100)
    df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')

    df['super_trend'] = ta.supertrend(df['high'], df['low'], df['close'])['SUPERTd_7_3.0']

    check_buy_sell_signals(df)


schedule.every(10).seconds.do(run_bot)

while True:
   schedule.run_pending()
   time.sleep(1)
