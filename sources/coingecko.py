"""CoinGecko simple price. spec: ids[], vs. Free tier, no key, one call for all ids."""
import json
from core.http import get


def fetch(spec, ctx):
    url = ("https://api.coingecko.com/api/v3/simple/price?ids=%s&vs_currencies=%s&include_24hr_change=true"
           % (",".join(spec["ids"]), spec["vs"]))
    data = json.loads(get(url, timeout=20))
    out = {k: {"price": v.get(spec["vs"]), "chg_24h_pct": v.get(spec["vs"] + "_24h_change")}
           for k, v in data.items()}
    return out, []
