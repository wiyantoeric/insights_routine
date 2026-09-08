"""Discover sources/*.json, dispatch each spec to its implementation.

Spec contract (sources/<id>.json):
  id        unique, defaults to the filename
  role      "content" -> list of candidate items    "tape" -> dict of market readings
  kind      "sitemap" (built in)  or  the name of sources/<kind>.py exposing fetch(spec, ctx)
  enabled   default true
  ...       anything else the implementation needs

fetch(spec, ctx) -> (result, errors). ctx has .cfg .cutoff .seen .now
"""
import glob, importlib.util, json, os

from core.config import ROOT
from core import sitemap

SOURCES_DIR = os.path.join(ROOT, "sources")
BUILTIN = {"sitemap": sitemap.collect}


def load_specs():
    specs = []
    for p in sorted(glob.glob(os.path.join(SOURCES_DIR, "*.json"))):
        with open(p) as f:
            spec = json.load(f)
        spec.setdefault("id", os.path.splitext(os.path.basename(p))[0])
        spec.setdefault("enabled", True)
        if "role" not in spec or "kind" not in spec:
            raise ValueError("%s: spec needs role and kind" % p)
        specs.append(spec)
    return specs


def _module(kind):
    path = os.path.join(SOURCES_DIR, kind + ".py")
    if not os.path.exists(path):
        raise ValueError("no built-in kind %r and no sources/%s.py" % (kind, kind))
    s = importlib.util.spec_from_file_location("sources." + kind, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def run(spec, ctx):
    fn = BUILTIN.get(spec["kind"]) or _module(spec["kind"]).fetch
    return fn(spec, ctx)
