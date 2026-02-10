from flask import Flask, render_template, jsonify, request
import yfinance as yf
from datetime import datetime, timedelta
import time
from tickers import TICKERS

app = Flask(__name__)

# Simple cache to avoid repeated slow API calls
CACHE = {"top_gainers": {"data": None, "timestamp": 0}}
CACHE_TTL = 6 * 60 * 60  # 6 hours

# --- Helper functions ---
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
    except Exception:
        return None

def get_return_last_year(symbol):
    try:
        end = datetime.today()
        start = end - timedelta(days=370)
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if len(df) < 2:
            return None
        start_price = df.iloc[0]["Close"]
        end_price = df.iloc[-1]["Close"]
        return ((end_price - start_price) / start_price) * 100
    except Exception:
        return None

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html", tickers=TICKERS)

@app.route("/stock")
def stock():
    symbol = request.args.get("symbol")
    data = get_yearly_data(symbol)
    if not data:
        return jsonify({"error": "No data"}), 400
    return jsonify(data)

@app.route("/top-gainers")
def top_gainers():
    now = time.time()
    # Use cache if recent
    if CACHE["top_gainers"]["data"] and now - CACHE["top_gainers"]["timestamp"] < CACHE_TTL:
        return jsonify(CACHE["top_gainers"]["data"])

    results = []
    # Limit to first 5 tickers to avoid long API calls
    for ticker in TICKERS[:5]:
        ret = get_return_last_year(ticker)
        if ret is not None:
            results.append({"ticker": ticker, "return": round(ret, 2)})
    results.sort(key=lambda x: x["return"], reverse=True)
    results = results[:3]

    CACHE["top_gainers"] = {"data": results, "timestamp": now}
    return jsonify(results)

# --- Run app ---
if __name__ == "__main__":
    app.run()
