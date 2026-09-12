"""FRED observations. spec: series{id:label}, api_key_env. Latest and previous value per series."""
import json, os
from core.http import get


def fetch(spec, ctx):
    key = os.environ.get(spec["api_key_env"], "")
    if not key:
        return {}, [{"source": spec["id"], "error": "%s not set" % spec["api_key_env"]}]
    out, errors = {}, []
    for sid, label in spec["series"].items():
        url = ("https://api.stlouisfed.org/fred/series/observations"
               "?series_id=%s&api_key=%s&file_type=json&sort_order=desc&limit=2" % (sid, key))
        try:
            obs = json.loads(get(url, timeout=20))["observations"]
            out[sid] = {"label": label, "value": obs[0]["value"], "date": obs[0]["date"],
                        "prev": obs[1]["value"] if len(obs) > 1 else None}
        except Exception as e:
            # the key rides in the query string, so an exception quoting the url
            # would carry it into candidates.json and anything downstream of it
            errors.append({"source": spec["id"], "series": sid,
                           "error": str(e).replace(key, "***")})
    return out, errors
