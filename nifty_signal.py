from datetime import datetime
import pytz, sys

# Weekend check — stops the bot on Sat & Sun
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

if now.weekday() >= 5:
    print("Weekend — skipping")
    sys.exit(0)

print(f"Running at {now.strftime('%H:%M IST')}")
import os
import requests
import yfinance as yf
from groq import Groq
from datetime import datetime

def get_data(name, ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist is None or hist.empty:
            return {"name": name, "error": "No data"}
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change = current - prev
        pct = (change / prev) * 100
        delta = hist['Close'].diff()
        gain = delta.clip(lower=0).mean()
        loss = (-delta.clip(upper=0)).mean()
        rs = gain / loss if loss != 0 else 100
        rsi = 100 - (100 / (1 + rs))
        high = hist['High'].iloc[-1]
        low = hist['Low'].iloc[-1]
        return {
            "name": name,
            "price": round(float(current), 2),
            "change": round(float(change), 2),
            "pct": round(float(pct), 2),
            "rsi": round(float(rsi), 2),
            "high": round(float(high), 2),
            "low": round(float(low), 2),
        }
    except Exception as e:
        return {"name": name, "error": str(e)}

def get_all_data():
    targets = {
        # INDICES
        "NIFTY 50":      "^NSEI",
        "BANK NIFTY":    "^NSEBANK",
        "SENSEX":        "^BSESN",
        "NIFTY IT":      "^CNXIT",
        "NIFTY AUTO":    "^CNXAUTO",
        "NIFTY PHARMA":  "^CNXPHARMA",
        "NIFTY MIDCAP":  "^NSEMDCP50",
        "INDIA VIX":     "^INDIAVIX",
        # TOP STOCKS
        "RELIANCE":      "RELIANCE.NS",
        "TCS":           "TCS.NS",
        "HDFC BANK":     "HDFCBANK.NS",
        "INFOSYS":       "INFY.NS",
        "ICICI BANK":    "ICICIBANK.NS",
        "AIRTEL":        "BHARTIARTL.NS",
        "ITC":           "ITC.NS",
        "KOTAK BANK":    "KOTAKBANK.NS",
        "LT":            "LT.NS",
        "AXIS BANK":     "AXISBANK.NS",
        "BAJAJ FINANCE": "BAJFINANCE.NS",
        "SBI":           "SBIN.NS",
        "WIPRO":         "WIPRO.NS",
        "HCL TECH":      "HCLTECH.NS",
        "MARUTI":        "MARUTI.NS",
        "TITAN":         "TITAN.NS",
        "ADANI PORTS":   "ADANIPORTS.NS",
        "TATA MOTORS":   "M&M.NS",
        "TATA STEEL":    "TATASTEEL.NS",
        "ONGC":          "ONGC.NS",
        "NIFTYFIN.NS":     "NIFTYFIN.NS",
        "FINNIFTY":      "NIFTY_FIN_SERVICE.NS",
    }
    results = {}
    for name, ticker in targets.items():
        d = get_data(name, ticker)
        results[name] = d if d is not None else {"name": name, "error": "None returned"}
    return results

def signal(pct, rsi):
    if pct > 0.5 and rsi < 70:
        return "🟢 BULLISH"
    elif pct < -0.5 and rsi > 30:
        return "🔴 BEARISH"
    else:
        return "🟡 NEUTRAL"

def format_indices(data):
    indices = ["NIFTY 50","BANK NIFTY","SENSEX","FINNIFTY",
               "NIFTY IT","NIFTY AUTO","NIFTY PHARMA",
               "NIFTY MIDCAP","INDIA VIX"]
    msg = "📊 <b>INDICES</b>\n"
    for name in indices:
        d = data.get(name, {})
        if d and "error" not in d and "price" in d:
            arrow = "📈" if d['pct'] >= 0 else "📉"
            sig = signal(d['pct'], d.get('rsi', 50)) if name != "INDIA VIX" else ""
            msg += f"{arrow} <b>{name}</b>: {d['price']:,} ({d['pct']:+.2f}%) {sig}\n"
            msg += f"   H:{d['high']} L:{d['low']} RSI:{d.get('rsi','N/A')}\n"
        else:
            msg += f"⚪ <b>{name}</b>: Data unavailable\n"
    return msg

def format_stocks(data):
    stocks = ["RELIANCE","TCS","HDFC BANK","INFOSYS",
              "ICICI BANK","AIRTEL","ITC","KOTAK BANK",
              "LT","AXIS BANK","BAJAJ FINANCE","SBI",
              "WIPRO","HCL TECH","MARUTI","TITAN",
              "ADANI PORTS","TATA MOTORS","TATA STEEL","ONGC"]
    msg = "\n🏢 <b>TOP STOCKS</b>\n"
    for name in stocks:
        d = data.get(name, {})
        if d and "error" not in d and "price" in d:
            arrow = "📈" if d['pct'] >= 0 else "📉"
            msg += f"{arrow} <b>{name}</b>: ₹{d['price']:,} ({d['pct']:+.2f}%) RSI:{d.get('rsi','N/A')}\n"
        else:
            msg += f"⚪ <b>{name}</b>: Unavailable\n"
    return msg

def get_ai_analysis(data):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    nifty = data.get("NIFTY 50", {})
    bank = data.get("BANK NIFTY", {})
    vix = data.get("INDIA VIX", {})

    prompt = f"""You are an expert Indian stock market analyst.
Based on this data give sharp analysis:

Nifty 50: {nifty.get('price','N/A')} | Change: {nifty.get('pct','N/A')}% | RSI: {nifty.get('rsi','N/A')}
Bank Nifty: {bank.get('price','N/A')} | Change: {bank.get('pct','N/A')}% | RSI: {bank.get('rsi','N/A')}
India VIX: {vix.get('price','N/A')} | Change: {vix.get('pct','N/A')}%

Respond in this EXACT format:

🧠 <b>AI VERDICT</b>
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

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    max_len = 4000
    parts = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    for part in parts:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML"
        })

def main():
    print("Fetching market data...")
    data = get_all_data()
    now = datetime.now().strftime("%d %b %Y | %H:%M IST")
    header = f"🤖 <b>AI MARKET INTELLIGENCE</b>\n📅 {now}\n━━━━━━━━━━━━━━━━━━━━\n\n"
    print("Building message...")
    indices_msg = format_indices(data)
    stocks_msg = format_stocks(data)
    print("Getting AI analysis...")
    ai_msg = "\n" + get_ai_analysis(data)
    footer = "\n━━━━━━━━━━━━━━━━━━━━\n⚠️ <i>Education only. Not financial advice. Always use stop loss.</i>"
    full_message = header + indices_msg + stocks_msg + ai_msg + footer
    print("Sending to Telegram...")
    send_telegram(full_message)
    print("Done! ✅")

if __name__ == "__main__":
    main()
