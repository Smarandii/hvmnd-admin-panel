# app/services/tron.py
"""
Helpers for live USDT-TRC20 balances.

The TronGrid *account* endpoint is unreliable for swept / freshly-created
addresses (it often returns empty data).
Instead we derive the balance by replaying every confirmed USDT transfer
in or out of the wallet.
"""
from __future__ import annotations

import os
import decimal as _d
import functools
import logging
from typing import Final

import requests


# --------------------------------------------------------------------------- #
# constants & session
# --------------------------------------------------------------------------- #
_API_BASE:  Final = "https://api.trongrid.io"
_USDT_CONTRACT: Final = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"         # canonical

_API_KEY = os.getenv("TRON_GRID_API_KEY")
_SESSION = requests.Session()
if _API_KEY:
    _SESSION.headers.update({"TRON-PRO-API-KEY": _API_KEY})


# --------------------------------------------------------------------------- #
# core helpers
# --------------------------------------------------------------------------- #
def _fetch_page(address: str, *, fingerprint: str | None = None) -> dict:
    "Return one page of USDT transfers for **address**."
    params = {
        "contract_address": _USDT_CONTRACT,
        "only_confirmed": "true",
        "limit": 200,                  # max allowed
    }
    if fingerprint:
        params["fingerprint"] = fingerprint

    r = _SESSION.get(
        f"{_API_BASE}/v1/accounts/{address}/transactions/trc20",
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def _page_loop(address: str):
    "Yield **every** transfer row once, transparently following pagination."
    fp = None
    while True:
        body = _fetch_page(address, fingerprint=fp)
        yield from body.get("data", [])

        # TronGrid pagination: fingerprint of the *next* page (None == last page)
        fp = body.get("meta", {}).get("fingerprint")
        if not fp:
            break


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=512)                 # simple memoisation (1 run)
def usdt_balance(address: str) -> float:
    """
    Net USDT balance of **address** (incoming – outgoing) in normal units.

    • Sums *only confirmed* transfers.
    • Walks through the whole history with pagination.
    • On network / data errors falls back to 0.0 **and** logs a warning.
    """
    try:
        delta = _d.Decimal(0)
        for tx in _page_loop(address):
            raw   = _d.Decimal(tx["value"])        # integer, 6 decimals
            value = raw / _d.Decimal(1_000_000)

            if tx["to"] == address:
                delta += value
            elif tx["from"] == address:
                delta -= value                      # outgoing

        return float(delta)

    except (requests.RequestException, KeyError, ValueError) as exc:
        logging.warning("TronGrid sweep failed for %s – %s", address, exc)
        return 0.0


def total_usdt(addresses: list[str]) -> float:
    "Convenience – sum the balances of multiple wallets."
    return sum(usdt_balance(addr) for addr in addresses)


# --------------------------------------------------------------------------- #
# quick CLI test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    sample = [
        "TKxA544xD5RjnLCXkMCMQXM9SvNBCvaVBc",
        "TG5i2A2etb62NzBvmBgg7tNcwtxbCChY7U",
        "TAwDETBFEAGy354ZFTJcxZnfPeNLjArtaL",
        "TAZnnxHzwzYXEzTTnANPbCv19TfoagZAye",
        "TFK2qEgoSCdv84C9eN9ZhqFpBzgfVCGSvs",
    ]
    print(f"Total USDT: {total_usdt(sample):,.2f}")
