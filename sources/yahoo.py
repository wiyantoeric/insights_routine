"""Yahoo chart quotes. spec: symbols{sym:label}, range, interval, alert_sigma.
Needs the browser UA that core.http sets, or the response comes back empty."""
import json, statistics, urllib.parse
from datetime import datetime, timezone
from core.http import get


def fetch(spec, ctx):
    out, errors = {}, []
    for sym, label in spec["symbols"].items():
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=%s"
               % (urllib.parse.quote(sym), spec["range"], spec["interval"]))
        try:
            res = json.loads(get(url, timeout=20))["chart"]["result"][0]
            closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
            if len(closes) < 3:
                raise ValueError("insufficient closes")
            last, prev = closes[-1], closes[-2]
            chg = (last - prev) / prev * 100
            rets = [(closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))]
            sd = statistics.pstdev(rets)
            z = (chg - statistics.mean(rets)) / sd if sd else 0.0
            out[sym] = {
                "label": label, "price": round(last, 4), "chg_pct": round(chg, 3),
                "zscore": round(z, 2), "alert": abs(z) >= spec.get("alert_sigma", 2.0),
                "as_of": datetime.fromtimestamp(res["meta"]["regularMarketTime"], timezone.utc).isoformat(),
            }
        except Exception as e:
            errors.append({"source": spec["id"], "symbol": sym, "error": str(e)})
    return out, errors
