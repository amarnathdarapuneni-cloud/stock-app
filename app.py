from datetime import date, datetime, timedelta
import time

from flask import Flask, jsonify, render_template, request
import yfinance as yf

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
            "prices": df["Close"].round(2).tolist(),
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


def calculate_what_if(symbol, invest_date, amount):
    try:
        start = datetime.combine(invest_date, datetime.min.time())
        end = datetime.today() + timedelta(days=1)
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None, "No price data found for that date range."

        buy_price = float(df.iloc[0]["Close"])
        current_price = float(df.iloc[-1]["Close"])
        shares = amount / buy_price
        current_value = shares * current_price
        gain_loss = current_value - amount
        gain_loss_pct = (gain_loss / amount) * 100

        return {
            "buy_date": df.index[0].strftime("%Y-%m-%d"),
            "buy_price": round(buy_price, 2),
            "current_price": round(current_price, 2),
            "shares": round(shares, 4),
            "current_value": round(current_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
        }, None
    except Exception:
        return None, "Unable to calculate investment outcome right now."


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        amount_raw = request.form.get("amount", "").strip()
        date_raw = request.form.get("invest_date", "").strip()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            error = "Please provide a valid investment amount greater than 0."
            amount = None

        try:
            invest_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
            if invest_date > date.today():
                error = "Investment date cannot be in the future."
        except ValueError:
            invest_date = None
            error = "Please provide a valid investment date."

        if symbol not in TICKERS:
            error = "Please select a supported ticker symbol."

        if not error:
            result, error = calculate_what_if(symbol, invest_date, amount)
            if result:
                result["symbol"] = symbol
                result["amount"] = round(amount, 2)

    return render_template("index.html", tickers=TICKERS, result=result, error=error, today=date.today().isoformat())


@app.route("/stock")
def stock():
    symbol = request.args.get("symbol", "").upper().strip()
    if symbol not in TICKERS:
        return jsonify({"error": "Unsupported ticker"}), 400

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
    # Limit to first 10 tickers to balance speed and useful ranking
    for ticker in TICKERS[:10]:
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
