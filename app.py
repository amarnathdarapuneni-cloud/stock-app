from flask import Flask, render_template, jsonify, request
import yfinance as yf
from datetime import datetime, timedelta
import time
from tickers import TICKERS

app = Flask(__name__)

# Simple in-memory cache
CACHE = {
    "top_gainers": {
        "data": None,
        "timestamp": 0
    }
}
CACHE_TTL = 6 * 60 * 60  # 6 hours

def get_yearly_data(symbol):
    try:
        df = yf.download(symbol, period="1y", progress=False)
        if df.empty:
            return None
        df.reset_index(inplace=True)
        return {
            "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "prices": df["Close"].round(2).tolist()
        }
    except Excep
