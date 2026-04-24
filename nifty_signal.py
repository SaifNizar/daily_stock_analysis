import pytz
import sys
import os
import requests
import yfinance as yf
from groq import Groq
from datetime import datetime

# ── TIMEZONE HELPER ──────────────────────────────────────────────────
def get_ist_now():
    """Always returns fresh IST time — call this right before sending"""
    return datetime.now(pytz.timezone("Asia/Kolkata"))

# ── WEEKEND CHECK ────────────────────────────────────────────────────
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

if now.weekday() >= 5:
    print("Weekend — skipping")
    sys.exit(0)

print("Running at " + now.strftime("%d %b %Y | %H:%M IST"))

# ── SAFE FLOAT HELPER (fixes NaN issue) ──────────────────────────────
def safe(val, decimals=2):
    """Converts any value to float safely. Returns 0.0 if NaN or error."""
    try:
        f = float(val)
        if f != f:  # NaN check — NaN is the only value not equal to itself
            return 0.0
        return round(f, decimals)
    except:
        return 0.0

# ── FETCH SINGLE STOCK DATA ──────────────────────────────────────────
def get_data(name, ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")

        if hist is None or hist.empty:
            return {"name": name, "error": "No data"}

        current  = hist["Close"].iloc[-1]
        prev     = hist["Close"].iloc[-2]
        change   = current - prev
        pct      = (change / prev) * 100
        delta    = hist["Close"].diff()
        gain     = delta.clip(lower=0).mean()
        loss     = (-delta.clip(upper=0)).mean()
        rs       = gain / loss if loss != 0 else 100
        rsi      = 100 - (100 / (1 + rs))
        high     = hist["High"].iloc[-1]
        low      = hist["Low"].iloc[-1]

        return {
            "name":   name,
            "price":  safe(current),
            "change": safe(change),
            "pct":    safe(pct),
            "rsi":    safe(rsi),
            "high":   safe(high),
            "low":    safe(low),
        }
    except Exception as e:
        return {"name": name, "error": str(e)}

# ── FETCH ALL DATA ───────────────────────────────────────────────────
def get_all_data():
    targets = {
        # INDICES
        "NIFTY 50":     "^NSEI",
        "BANK NIFTY":   "^NSEBANK",
        "SENSEX":       "^BSESN",
        "FINNIFTY":     "^CNXFIN",
        "NIFTY IT":     "^CNXIT",
        "NIFTY AUTO":   "^CNXAUTO",
        "NIFTY PHARMA": "^CNXPHARMA",
        "NIFTY MIDCAP": "^NSEMDCP50",
        "INDIA VIX":    "^INDIAVIX",
        # TOP STOCKS
        "RELIANCE":     "RELIANCE.NS",
        "TCS":          "TCS.NS",
        "HDFC BANK":    "HDFCBANK.NS",
        "INFOSYS":      "INFY.NS",
        "ICICI BANK":   "ICICIBANK.NS",
        "AIRTEL":       "BHARTIARTL.NS",
        "ITC":          "ITC.NS",
        "KOTAK BANK":   "KOTAKBANK.NS",
        "LT":           "LT.NS",
        "AXIS BANK":    "AXISBANK.NS",
        "BAJAJ FINANCE":"BAJFINANCE.NS",
        "SBI":          "SBIN.NS",
        "WIPRO":        "WIPRO.NS",
        "HCL TECH":     "HCLTECH.NS",
        "MARUTI":       "MARUTI.NS",
        "TITAN":        "TITAN.NS",
        "ADANI PORTS":  "ADANIPORTS.NS",
        "TATA MOTORS":  "M&M.NS",
        "TATA STEEL":   "TATASTEEL.NS",
        "ONGC":         "ONGC.NS",
        "NIFTYFIN.NS":  "NIFTYFIN SERVICE.NS",
    }

    results = {}
    for name, ticker in targets.items():
        d = get_data(name, ticker)
        results[name] = d if d is not None else {"name": name, "error": "Failed"}
    return results

# ── SIGNAL LABEL ─────────────────────────────────────────────────────
def signal(pct, rsi):
    if pct > 0.5 and rsi < 70:
        return "🟢 BULLISH"
    elif pct < -0.5 and rsi > 30:
        return "🔴 BEARISH"
    else:
        return "🟡 NEUTRAL"

# ── FORMAT INDICES SECTION ───────────────────────────────────────────
def format_indices(data):
    indices = [
        "NIFTY 50", "BANK NIFTY", "SENSEX", "FINNIFTY",
        "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA",
        "NIFTY MIDCAP", "INDIA VIX"
    ]
    msg = "📊 <b>INDICES</b>\n"
    for name in indices:
        d = data.get(name, {})
        if d and "error" not in d and "price" in d:
            arrow = "📈" if d["pct"] >= 0 else "📉"
            sig   = signal(d["pct"], d.get("rsi", 50)) if name != "INDIA VIX" else ""
            msg  += (
                f"{arrow} <b>{name}</b>: {d['price']:,} "
                f"({'+' if d['change'] >= 0 else ''}{d['pct']}%) {sig}\n"
                f"   H:{d['high']} L:{d['low']} RSI:{d['rsi']}\n"
            )
        else:
            msg += f"🔵 <b>{name}</b>: Data unavailable\n"
    return msg

# ── FORMAT STOCKS SECTION ────────────────────────────────────────────
def format_stocks(data):
    stocks = [
        "RELIANCE", "TCS", "HDFC BANK", "INFOSYS",
        "ICICI BANK", "AIRTEL", "ITC", "KOTAK BANK",
        "LT", "AXIS BANK", "BAJAJ FINANCE", "SBI",
        "WIPRO", "HCL TECH", "MARUTI", "TITAN",
        "ADANI PORTS", "TATA MOTORS", "TATA STEEL", "ONGC"
    ]
    msg = "\n🏢 <b>TOP STOCKS</b>\n"
    for name in stocks:
        d = data.get(name, {})
        if d and "error" not in d and "price" in d:
            arrow = "📈" if d["pct"] >= 0 else "📉"
            msg  += (
                f"{arrow} <b>{name}</b>: ₹{d['price']:,} "
                f"({'+' if d['change'] >= 0 else ''}{d['pct']}%) "
                f"RSI:{d['rsi']}\n"
            )
        else:
            msg += f"🔵 <b>{name}</b>: Unavailable\n"
    return msg

# ── GROQ AI ANALYSIS ─────────────────────────────────────────────────
def get_ai_analysis(data):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    nifty  = data.get("NIFTY 50",   {})
    bank   = data.get("BANK NIFTY", {})
    vix    = data.get("INDIA VIX",  {})

    prompt = f"""You are an expert Indian stock market analyst.
Based on this data give sharp analysis:

Nifty 50: {nifty.get('price','N/A')} | Change: {nifty.get('pct','N/A')}%
Bank Nifty: {bank.get('price','N/A')} | Change: {bank.get('pct','N/A')}%
India VIX: {vix.get('price','N/A')} | Change: {vix.get('pct','N/A')}%

Respond in this EXACT format:

🤖 <b>AI VERDICT</b>
Market Mood: [BULLISH/BEARISH/NEUTRAL]
Volatility: [LOW/MEDIUM/HIGH]

🎯 <b>KEY LEVELS</b>
Nifty Support: [level] | Resistance: [level]
BankNifty Support: [level] | Resistance: [level]

📋 <b>STRATEGY</b>
[2 simple sentences on what to do today]

⭐ <b>STOCKS TO WATCH</b>
[2-3 stocks with one line reason each]

Use simple English. No jargon."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content

# ── SEND TELEGRAM ────────────────────────────────────────────────────
def send_telegram(message):
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    max_len = 4000

    if not token or not chat_id:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in secrets!")
        return

    parts = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    for part in parts:
        url      = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            "chat_id":    chat_id,
            "text":       part,
            "parse_mode": "HTML"
        })
        print(f"Telegram status: {response.status_code}")
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")

# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("Fetching market data...")
    data = get_all_data()

    print("Building message...")
    indices_msg = format_indices(data)
    stocks_msg  = format_stocks(data)

    print("Getting AI analysis...")
    ai_msg = get_ai_analysis(data)

    # ✅ Fresh timestamp captured RIGHT before sending
    send_time = get_ist_now().strftime("%d %b %Y | %H:%M IST")

    header = (
        f"🤖 <b>AI MARKET INTELLIGENCE</b>\n"
        f"📅 {send_time}\n"
        f"{'─' * 30}\n\n"
    )

    footer = "\n\n⚠️ <i>Education only. Not financial advice. Always use stop loss.</i>"

    full_message = header + indices_msg + stocks_msg + "\n\n" + ai_msg + footer

    print("Sending to Telegram...")
    send_telegram(full_message)
    print("✅ Done!")

if __name__ == "__main__":
    main()
    
