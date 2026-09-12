"""Checks for sources/fred.py.

Offline by default: the network is stubbed, so these run anywhere, in under a
second, with no key. The live check runs only when FRED_API_KEY is set.

    python3 -m unittest discover -s tests            # offline only
    python3 -m unittest discover -s tests -v         # with names
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config, registry

fred = registry._module("fred")

SPEC = {
    "id": "macro",
    "api_key_env": "FRED_API_KEY",
    "series": {"CPIAUCSL": "US CPI", "DFF": "Fed funds rate"},
}
CTX = SimpleNamespace(cfg={}, now=None, cutoff=None, seen=set())

TWO_OBS = json.dumps(
    {
        "observations": [
            {"date": "2026-08-01", "value": "323.456"},
            {"date": "2026-07-01", "value": "322.100"},
        ]
    }
).encode()

ONE_OBS = json.dumps({"observations": [{"date": "2026-08-01", "value": "323.456"}]}).encode()


class FredOffline(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"FRED_API_KEY": "secret-key-123"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_missing_key_reports_instead_of_raising(self):
        """A source that cannot run says so in errors. It never aborts the run."""
        with mock.patch.dict(os.environ, {"FRED_API_KEY": ""}):
            out, errors = fred.fetch(SPEC, CTX)
        self.assertEqual(out, {})
        self.assertEqual(len(errors), 1)
        self.assertIn("FRED_API_KEY", errors[0]["error"])

    def test_latest_and_previous_observation(self):
        with mock.patch.object(fred, "get", return_value=TWO_OBS):
            out, errors = fred.fetch(SPEC, CTX)
        self.assertEqual(errors, [])
        self.assertEqual(
            out["CPIAUCSL"],
            {"label": "US CPI", "value": "323.456", "date": "2026-08-01", "prev": "322.100"},
        )
        self.assertEqual(set(out), {"CPIAUCSL", "DFF"})

    def test_single_observation_leaves_prev_none(self):
        with mock.patch.object(fred, "get", return_value=ONE_OBS):
            out, _ = fred.fetch(SPEC, CTX)
        self.assertIsNone(out["CPIAUCSL"]["prev"])

    def test_one_series_failing_keeps_the_others(self):
        """Per-series isolation, the same contract the sitemap kind holds to."""

        def flaky(url, timeout=20):
            if "DFF" in url:
                raise RuntimeError("boom")
            return TWO_OBS

        with mock.patch.object(fred, "get", side_effect=flaky):
            out, errors = fred.fetch(SPEC, CTX)
        self.assertEqual(set(out), {"CPIAUCSL"})
        self.assertEqual([e["series"] for e in errors], ["DFF"])

    def test_the_key_never_reaches_an_error(self):
        """RULES.md rule 14: a secret never lands in a log, a digest or a payload.

        The key travels in the query string, so any exception carrying the url
        would carry the key into errors[], into state/candidates.json, and from
        there into whatever the agent writes.
        """

        def leaky(url, timeout=20):
            raise RuntimeError("failed fetching %s" % url)

        with mock.patch.object(fred, "get", side_effect=leaky):
            _, errors = fred.fetch(SPEC, CTX)
        self.assertTrue(errors)
        self.assertNotIn("secret-key-123", json.dumps(errors))


@unittest.skipUnless(
    (config.load_env() or os.environ.get("FRED_API_KEY")),
    "no FRED_API_KEY in .env or environment",
)
class FredLive(unittest.TestCase):
    """One real call, to catch the things a stub cannot: a moved endpoint, a
    rejected key, a changed payload shape."""

    def test_real_series_comes_back_dated(self):
        out, errors = fred.fetch(SPEC, CTX)
        self.assertNotIn("secret", json.dumps(errors).lower())
        self.assertTrue(out, "no series returned: %s" % errors)
        for sid, reading in out.items():
            self.assertRegex(reading["date"], r"^\d{4}-\d{2}-\d{2}$", sid)
            self.assertTrue(reading["label"], sid)
            # FRED writes "." for a missing observation, which is data, not an error
            self.assertTrue(reading["value"] == "." or float(reading["value"]) == float(reading["value"]))


if __name__ == "__main__":
    unittest.main()
