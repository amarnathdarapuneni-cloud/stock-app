from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tickers import TICKERS

app = Flask(__name__)

def get_same_trading_day(symbol):
    today = datetime.today()
    last_year = today - timedelta(days=365)

    df = yf.download(symbol, start=last_year - timedelta(days=5), end=today)
    df = df.dropna()

    if df.empty:
        return None

    start_price = df.iloc[0]["Close"]
    end_price = df.iloc[-1]["Close"]
    return ((end_price - start_price) / start_price) * 100

@app.route("/")
def index():
    return render_template("index.html", tickers=TICKERS)

@app.route("/stock")
def stock():
    symbol = request.args.get("symbol")
    df = yf.download(symbol, period="1y")
    df.reset_index(inplace=True)

    return jsonify({
        "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "prices": df["Close"].round(2).tolist()
    })

@app.route("/top-gainers")
def top_gainers():
    results = []
    for ticker in TICKERS:
        ret = get_same_trading_day(ticker)
        if ret is not None:
            results.append({"ticker": ticker, "return": round(ret, 2)})

    results = sorted(results, key=lambda x: x["return"], reverse=True)
    return jsonify(results[:5])

if __name__ == "__main__":
    app.run()
