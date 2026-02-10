from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tickers import TICKERS
import time

app = Flask(__name__)

# ---- SIMPLE IN-MEMORY CACHE (Render-safe) ----
CACHE = {
    "top_gainers": {
        "data": None,
        "timestamp": 0
    }
}

CACHE_TTL = 6 * 60 * 60  # 6 hours


def get_yearly_data(symbol):
    df = yf.download(symbol, period="1y", progress=False)
    if df.empty:
        return None
    df.reset_index(inplace=True)
    return {
        "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "prices": df["Close"].round(2).tolist()
    }


def get_return_last_year(symbol):
    try:
        end = datetime.today()
        start = end - timedelta(days=370)

        df = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True
        )

        if len(df) < 2:
            return None

        start_price = df.iloc[0]["Close"]
        end_price = df.iloc[-1]["Close"]

        return ((end_price - start_price) / start_price) * 100
    except Exception:
        return None


@app.ro
