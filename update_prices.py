#!/usr/bin/env python3
import datetime, json, os, time
import yfinance as yf
TICKERS=["AAPL","CSCO","COF","SCHD","KO","MSFT","NVDA","UAL","GOOGL","CCL","SCLX","SBAY","FDGRX","VTHRX"]
ANCHOR="2026-11-18"
def main():
    previous={}
    if os.path.exists("market_data.json"):
        try:
            with open("market_data.json",encoding="utf-8") as f: previous=json.load(f).get("quotes",{}) or {}
        except Exception: pass
    quotes={}
    for symbol in TICKERS:
        try:
            t=yf.Ticker(symbol)
            daily=t.history(period="3y",interval="1d",auto_adjust=False)
            if daily.empty: raise RuntimeError("no history returned")
            close=daily["Close"].dropna()
            price=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else price
            pct=(price/prev-1)*100 if prev else 0
            spark=close.tolist()[-18:]
            weekly=close.resample("W").last().dropna()
            anchor_return=0.0
            if symbol in {"FDGRX","VTHRX"}:
                idx=close.index.tz_localize(None) if close.index.tz is not None else close.index
                anchored=close[idx>=datetime.datetime.fromisoformat(ANCHOR)]
                if not anchored.empty: anchor_return=(price/float(anchored.iloc[0])-1)*100
            info={}
            try: info=t.fast_info or {}
            except Exception: pass
            quotes[symbol]={
                "name":symbol,"price":round(price,4 if price<.1 else 2),"chg":round(pct,2),
                "changePercent":round(pct,2),"sp":[round(float(x),4 if float(x)<.1 else 2) for x in spark],
                "sd":list(range(len(spark))),"series":{"dates":[x.strftime("%Y-%m-%d") for x in weekly.index],"prices":[round(float(x),4 if float(x)<.1 else 2) for x in weekly.tolist()]},
                "anchorReturn":round(anchor_return,4),"mcap":info.get("market_cap"),"news":[]
            }
        except Exception as e:
            print(f"Skipped {symbol}: {e}")
            if symbol in previous: quotes[symbol]=previous[symbol]
        time.sleep(.25)
    if not quotes:
        raise RuntimeError("No quotes were retrieved; existing market_data.json was not overwritten")
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open("market_data.json","w",encoding="utf-8") as f: json.dump({"updated":now,"updatedAt":now,"quotes":quotes},f,indent=2)
    print("Wrote market_data.json with",len(quotes),"tickers")
if __name__=="__main__": main()
