import json, os, datetime as dt
import yfinance as yf

HIST_FOR = ["NVDA"]  # tickers that keep 1 year of daily closes (used for auto-invest estimates)
tickers = json.load(open("tickers.json"))
now = dt.datetime.now(dt.timezone.utc)
today = now.date()

old = {}
if os.path.exists("market_data.json"):
    try:
        old = json.load(open("market_data.json"))
    except Exception:
        pass
out = {"updated": now.isoformat(timespec="seconds"), "quotes": old.get("quotes", {}), "hist": old.get("hist", {})}


def num(x, d=2):
    try:
        x = float(x)
        return None if x != x else round(x, d)
    except Exception:
        return None


def news(t):
    res = []
    for n in (t.news or [])[:4]:
        c = n.get("content", n)
        url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or n.get("link")
        if c.get("title") and url:
            res.append({"t": c["title"], "u": url})
    return res[:3]


def earnings(t):
    prev = nxt = None
    try:
        for d in t.get_earnings_dates(limit=12).index:
            day = d.date()
            if day > today:
                nxt = min(nxt, day) if nxt else day
            else:
                prev = max(prev, day) if prev else day
    except Exception:
        pass
    if not nxt:
        try:
            for d in (t.calendar or {}).get("Earnings Date", []):
                if d >= today:
                    nxt = d
                    break
        except Exception:
            pass
    return (str(nxt) if nxt else None), (str(prev) if prev else None)


for s in tickers:
    try:
        t = yf.Ticker(s)
        h = t.history(period="1y" if s in HIST_FOR else "3mo", interval="1d")["Close"].dropna()
        fi = t.fast_info
        price, prev_close = float(fi["last_price"]), float(fi["previous_close"])
        try:
            info = t.info
        except Exception:
            info = {}
        dy = info.get("trailingAnnualDividendYield")
        nxt, prv = earnings(t)
        tail = h.tail(30)
        out["quotes"][s] = {
            "name": info.get("shortName") or info.get("longName") or s,
            "price": num(price, 4),
            "chg": num((price / prev_close - 1) * 100),
            "mcap": info.get("marketCap"),
            "pe": num(info.get("trailingPE")),
            "dy": num(dy * 100) if dy else None,
            "sp": [num(v) for v in tail],
            "sd": [d.strftime("%b %d") for d in tail.index],
            "news": news(t),
            "earn": nxt,
            "ep": prv,
        }
        if s in HIST_FOR:
            out["hist"][s] = {d.strftime("%Y-%m-%d"): num(v) for d, v in h.items()}
    except Exception as e:
        print("skip", s, e)

json.dump(out, open("market_data.json", "w"), separators=(",", ":"))
