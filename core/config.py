"""Repo root, config.json, paths, .env. Import this instead of re-deriving ROOT."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    with open(os.path.join(ROOT, "config.json")) as f:
        return json.load(f)


def path(cfg, key):
    """Resolve cfg['paths'][key] to an absolute path."""
    p = cfg["paths"][key]
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def load_env():
    """Parse .env into os.environ without overriding what is already set."""
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p):
        return
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
