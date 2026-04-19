import os
import requests
import yfinance as yf
from groq import Groq
from datetime import datetime

def get_data(name, ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if not hist.empty:
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
            vol = hist['Volume'].iloc[-1]
            return {
                "name": name,
                "price": round(current, 2),
                "change": round(change, 2),
                "pct": round(pct, 2),
                "rsi": round(rsi, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "volume": int(vol)
            }
    except Exception as e:
        return {"name": name, "error": str(e)}

def get_all_data():
    targets = {
        # INDICES
        "NIFTY 50":       "^NSEI",
        "BANK NIFTY":     "^NSEBANK",
        "SENSEX":         "^BSESN",
        "FIN NIFTY":      "NIFTY_FIN_SERVICE.NS",
        "NIFTY IT":       "^CNXIT",
        "NIFTY AUTO":     "^CNXAUTO",
        "NIFTY PHARMA":   "^CNXPHARMA",
        "NIFTY MIDCAP":   "^NSEMDCP50",
        "INDIA VIX":      "^INDIAVIX",
        # TOP STOCKS
        "RELIANCE":       "RELIANCE.NS",
        "TCS":            "TCS.NS",
        "HDFC BANK":      "HDFCBANK.NS",
        "INFOSYS":        "INFY.NS",
        "ICICI BANK":     "ICICIBANK.NS",
        "BHARTI AIRTEL":  "BHARTIARTL.NS",
        "ITC":            "ITC.NS",
        "KOTAK BANK":     "KOTAKBANK.NS",
        "LT":             "LT.NS",
        "AXIS BANK":      "AXISBANK.NS",
        "BAJAJ FINANCE":  "BAJFINANCE.NS",
        "SBI":            "SBIN.NS",
        "WIPRO":          "WIPRO.NS",
        "HCL TECH":       "HCLTECH.NS",
        "MARUTI":         "MARUTI.NS",
        "TITAN":          "TITAN.NS",
        "ADANI PORTS":    "ADANIPORTS.NS",
        "TATA MOTORS":    "TATAMOTORS.NS",
        "TATA STEEL":     "TATASTEEL.NS",
        "ONGC":           "ONGC.NS"
    }
    results = {}
    for name, ticker in targets.items():
        results[name] = get_data(name, ticker)
    return results

def signal(pct, rsi):
    if pct > 0.5 and rsi < 70:
        return "🟢 BULLISH"
    elif pct < -0.5 and rsi > 30:
        return "🔴 BEARISH"
    else:
        return "🟡 NEUTRAL"

def format_indices(data):
    indices = ["NIFTY 50","BANK NIFTY","SENSEX","FIN NIFTY",
               "NIFTY IT","NIFTY AUTO","NIFTY PHARMA","NIFTY MIDCAP","INDIA VIX"]
    msg = "📊 <b>INDICES</b>\n"
    for name in indices:
        d = data.get(name, {})
        if "error" not in d and "price" in d:
            arrow = "📈" if d['pct'] >= 0 else "📉"
            sig = signal(d['pct'], d.get('rsi', 50)) if name != "INDIA VIX" else ""
            msg += f"{arrow} <b>{name}</b>: {d['price']:,} ({d['pct']:+.2f}%) {sig}\n"
            msg += f"   H: {d['high']} | L: {d['low']} | RSI: {d.get('rsi','N/A')}\n"
    return msg

def format_stocks(data):
    stocks = ["RELIANCE","TCS","HDFC BANK","INFOSYS","ICICI BANK",
              "BHARTI AIRTEL","ITC","KOTAK BANK","LT","AXIS BANK",
              "BAJAJ FINANCE","SBI","WIPRO","HCL TECH","MARUTI",
              "TITAN","ADANI PORTS","TATA MOTORS","TATA STEEL","ONGC"]
    msg = "\n🏢 <b>TOP STOCKS</b>\n"
    for name in stocks:
        d = data.get(name, {})
        if "error" not in d and "price" in d:
            arrow = "📈" if d['pct'] >= 0 else "📉"
            msg += f"{arrow} <b>{name}</b>: ₹{d['price']:,} ({d['pct']:+.2f}%) | RSI: {d.get('rsi','N/A')}\n"
    return msg

def get_ai_analysis(data):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    nifty = data.get("NIFTY 50", {})
    bank = data.get("BANK NIFTY", {})
    fin = data.get("FIN NIFTY", {})
    vix = data.get("INDIA VIX", {})
    
    prompt = f"""You are an expert Indian stock market analyst. 
Based on this data give a sharp market analysis:

Nifty 50: {nifty.get('price')} | Change: {nifty.get('pct')}% | RSI: {nifty.get('rsi')}
Bank Nifty: {bank.get('price')} | Change: {bank.get('pct')}% | RSI: {bank.get('rsi')}
Fin Nifty: {fin.get('price')} | Change: {fin.get('pct')}% | RSI: {fin.get('rsi')}
India VIX: {vix.get('price')} | Change: {vix.get('pct')}%

Respond in this EXACT format:

🧠 <b>AI VERDICT</b>
Overall Market: [BULLISH/BEARISH/NEUTRAL]
Volatility: [LOW/MEDIUM/HIGH] (VIX based)

🎯 <b>KEY LEVELS TODAY</b>
Nifty Support: [level] | Resistance: [level]
BankNifty Support: [level] | Resistance: [level]

📋 <b>STRATEGY</b>
[2 clear sentences on what traders should do today]

⭐ <b>STOCKS TO WATCH</b>
[Name 2-3 stocks with brief reason]

Keep language simple. No jargon."""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content

def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # Split if message too long
    max_len = 4000
    parts = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    
    for part in parts:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload)

def main():
    print("Fetching all market data...")
    data = get_all_data()
    
    now = datetime.now().strftime("%d %b %Y | %H:%M IST")
    
    print("Building message...")
    header = f"""🤖 <b>AI MARKET INTELLIGENCE</b>
📅 {now}
━━━━━━━━━━━━━━━━━━━━

"""
    indices_msg = format_indices(data)
    stocks_msg = format_stocks(data)
    
    print("Getting AI analysis...")
    ai_msg = "\n" + get_ai_analysis(data)
    
    footer = """
━━━━━━━━━━━━━━━━━━━━
⚠️ <i>For education only. Not financial advice.
Always use stop loss. Trade responsibly.</i>"""
    
    full_message = header + indices_msg + stocks_msg + ai_msg + footer
    
    print("Sending to Telegram...")
    send_telegram(full_message)
    print("Done! ✅")

if __name__ == "__main__":
    main()
