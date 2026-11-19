#!/usr/bin/env python3
"""
Fetches current stock quotes, intraday sparkline history, and headlines via Yahoo Finance (yfinance)
and writes market_data.json for the GitHub Pages dashboard.
"""
import datetime
import json
import yfinance as yf

TICKERS = ["AAPL", "CSCO", "COF", "SCHD", "KO", "MSFT", "NVDA", "UAL", "GOOGL", "CCL", "SCLX", "SBAY", "FDGRX", "VTHRX"]

def main():
    quotes = {}
    for symbol in TICKERS:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d", interval="1h")
            if hist.empty:
                hist = t.history(period="1mo", interval="1d")
            if hist.empty:
                continue

            closes = [round(float(x), 4 if float(x) < 0.1 else 2) for x in hist["Close"].dropna().tolist()[-18:]]
            if not closes:
                continue

            current_price = closes[-1]
            daily = t.history(period="5d", interval="1d")
            if len(daily) >= 2:
                prev_close = float(daily["Close"].dropna().iloc[-2])
            else:
                prev_close = closes[0]

            anchor_return = None
            if symbol in {"FDGRX", "VTHRX"}:
                anchor = t.history(start="2026-11-17", end="2026-11-20", interval="1d")
                if not anchor.empty:
                    anchor_price = float(anchor["Close"].dropna().iloc[0])
                    if anchor_price:
                        anchor_return = round((current_price / anchor_price - 1) * 100, 4)

            change = round(current_price - prev_close, 4 if current_price < 0.1 else 2)
            change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

            headlines = []
            try:
                news_items = t.news or []
                for item in news_items[:2]:
                    content = item.get("content", item)
                    title = content.get("title") or item.get("title")
                    provider = (content.get("provider") or {}).get("displayName") or item.get("publisher") or "Market Feed"
                    if title:
                        headlines.append({
                            "title": title,
                            "source": provider,
                            "date": datetime.datetime.now().strftime("%b %d, %Y"),
                            "snippet": content.get("summary") or "Live automated market feed update."
                        })
            except Exception:
                pass

            quotes[symbol] = {
                "price": current_price,
                "change": change,
                "changePercent": change_pct,
                "chg": change_pct,
                "history": closes,
                "sp": closes,
                "sd": list(range(len(closes))),
                "anchorReturn": anchor_return,
                "headlines": headlines
            }
        except Exception as e:
            print(f"Skipped {symbol}: {e}")

    payload = {
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "quotes": quotes
    }

    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Wrote market_data.json with", len(quotes), "tickers.")

if __name__ == "__main__":
    main()
