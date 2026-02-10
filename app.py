from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tickers import TICKERS
import time

app = Flask(__name__)

# ---- SIMPLE IN-MEMORY CACHE ----
CACHE = {
    "top_gainers": {
        "data": None,
        "timestamp": 0
    }
}
CACHE_TTL = 6 * 60 * 60  # 6 hours
