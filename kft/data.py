"""Data layer: daily OHLCV via the Yahoo Finance chart API.

Uses a plain requests session with the cookie+crumb handshake (works behind
TLS-reterminating proxies where curl_cffi-based clients fail). Results are
cached to CSV so repeated runs are offline-friendly.
"""

from __future__ import annotations

import os
import time

import pandas as pd
import requests

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_CA = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE") or True


class YahooDaily:
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._sess: requests.Session | None = None
        self._crumb: str | None = None

    def _session(self) -> tuple[requests.Session, str]:
        if self._sess is None:
            s = requests.Session()
            s.headers.update({"User-Agent": _UA})
            s.verify = _CA
            # Any hit on fc.yahoo.com sets the auth cookie (the 404 is expected).
            s.get("https://fc.yahoo.com", timeout=30)
            crumb = s.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=30
            ).text
            self._sess, self._crumb = s, crumb
        return self._sess, self._crumb

    def fetch(self, symbol: str, start: str = "2010-01-01") -> pd.DataFrame:
        cache = os.path.join(
            self.cache_dir, symbol.replace("^", "_").replace("=", "_") + ".csv"
        )
        if os.path.exists(cache):
            df = pd.read_csv(cache, index_col=0, parse_dates=True)
            return df[df.index >= start]

        sess, crumb = self._session()
        p0 = int(pd.Timestamp(start).timestamp())
        p1 = int(time.time())
        for attempt in range(4):
            r = sess.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={
                    "period1": p0,
                    "period2": p1,
                    "interval": "1d",
                    "events": "div,splits",
                    "crumb": crumb,
                },
                timeout=60,
            )
            if r.status_code == 200:
                break
            time.sleep(2 ** (attempt + 1))
        r.raise_for_status()
        res = r.json()["chart"]["result"][0]
        q = res["indicators"]["quote"][0]
        adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
        df = pd.DataFrame(
            {
                "Open": q["open"],
                "High": q["high"],
                "Low": q["low"],
                "Close": q["close"],
                "Volume": q["volume"],
            },
            index=pd.to_datetime(res["timestamp"], unit="s", utc=True).normalize(),
        )
        if adj is not None:
            # Rescale OHLC by the adjustment factor so levels stay consistent.
            f = pd.Series(adj, index=df.index) / df["Close"]
            for col in ("Open", "High", "Low", "Close"):
                df[col] = df[col] * f
        df.index = df.index.tz_localize(None)
        df.index.name = "Date"
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        df = df[~df.index.duplicated(keep="last")].sort_index()
        # Guard against zero-range bars (holidays / bad prints).
        df = df[(df["High"] - df["Low"]) > 0]
        df.to_csv(cache)
        return df
