from binance.client import Client
import pandas as pd
import numpy as np
import time
import os

# --- API KEYS (from environment variables) ---
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

client = Client(api_key, api_secret)

symbol = "ETHUSDT"
capital = 1000
risk_per_trade = 0.02

# --- RSI FUNCTION ---
def RSI(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- GET DATA ---
def get_data():
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_4HOUR, limit=200)
    df = pd.DataFrame(klines)
    df = df[[0,4,2,3]]
    df.columns = ["time","Close","High","Low"]
    df["Close"] = df["Close"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    return df

# --- BOT LOOP ---
position = 0
entry_price = 0

while True:
    try:
        df = get_data()

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['EMA200'] = df['Close'].ewm(span=200).mean()
        df['RSI'] = RSI(df['Close'])

        # ATR
        tr = (df['High'] - df['Low']).rolling(14).mean()
        df['ATR'] = tr

        last = df.iloc[-1]
        price = last['Close']

        # BUY
        if position == 0:
            if last['EMA50'] > last['EMA200'] and last['RSI'] < 40:

                stop_loss = price - (last['ATR'] * 2)
                sl_percent = (price - stop_loss) / price

                risk_amount = capital * risk_per_trade
                position_size = risk_amount / sl_percent

                qty = round(position_size / price, 4)

                client.order_market_buy(symbol=symbol, quantity=qty)

                entry_price = price
                position = 1

                print("BUY:", price)

        # SELL
        elif position == 1:
            change = (price - entry_price) / entry_price

            if change <= -0.03 or change >= 0.07 or last['RSI'] > 65:
                qty = round((capital / entry_price), 4)

                client.order_market_sell(symbol=symbol, quantity=qty)

                position = 0
                print("SELL:", price)

        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(60)
