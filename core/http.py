"""One HTTP GET for every source. Browser UA (Yahoo returns empty without it), gzip, one retry."""
import gzip, time, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 insights_routine/1.0"


def get(url, timeout=30, retries=1):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2)
