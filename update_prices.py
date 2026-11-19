#!/usr/bin/env python3
import datetime, json, os
import yfinance as yf
TICKERS=["AAPL","CSCO","COF","SCHD","KO","MSFT","NVDA","UAL","GOOGL","CCL","SCLX","SBAY","FDGRX","VTHRX"]
ANCHOR="2026-11-18"
def main():
    previous={}
    if os.path.exists("market_data.json"):
        try:
            with open("market_data.json","r",encoding="utf-8") as f:
                previous=json.load(f).get("quotes",{}) or {}
        except Exception:
            previous={}
    quotes={}
    for symbol in TICKERS:
        try:
            t=yf.Ticker(symbol)
            hist=t.history(period="5d",interval="1h")
            daily=t.history(period="3y",interval="1d")
            if daily.empty: continue
            close=daily["Close"].dropna()
            price=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else price
            pct=(price/prev-1)*100 if prev else 0
            spark=[round(float(x),4 if float(x)<.1 else 2) for x in (hist["Close"].dropna().tolist()[-18:] if not hist.empty else close.tolist()[-18:])]
            ser=close.resample("W").last().dropna()
            dates=[x.strftime("%Y-%m-%d") for x in ser.index]
            prices=[round(float(x),4 if float(x)<.1 else 2) for x in ser.tolist()]
            ar=0
            if symbol in {"FDGRX","VTHRX"}:
                a=close[close.index.tz_localize(None)>=datetime.datetime.fromisoformat(ANCHOR)]
                if not a.empty and float(a.iloc[0]): ar=(price/float(a.iloc[0])-1)*100
            quotes[symbol]={"price":round(price,4 if price<.1 else 2),"chg":round(pct,2),"changePercent":round(pct,2),"sp":spark,"sd":list(range(len(spark))),"series":{"dates":dates,"prices":prices},"anchorReturn":round(ar,4),"news":[]}
        except Exception as e:
            print("Skipped",symbol,e)
            if symbol in previous:
                quotes[symbol]=previous[symbol]
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open("market_data.json","w",encoding="utf-8") as f: json.dump({"updated":now,"updatedAt":now,"quotes":quotes},f,indent=2)
    print("Wrote market_data.json with",len(quotes),"tickers")
if __name__=="__main__": main()
