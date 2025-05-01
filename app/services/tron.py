import os
import decimal as _d
import requests
import logging

_API  = "https://api.trongrid.io/v1/accounts"
_KEY  = os.getenv("TRON_GRID_API_KEY")
_USDT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

_SESSION = requests.Session()
if _KEY:
    _SESSION.headers.update({"TRON-PRO-API-KEY": _KEY})


def usdt_balance(address: str) -> float:
    """
    Return the USDT-TRC20 balance of **address** in normal units (e.g. 12.34).
    """
    try:
        r = _SESSION.get(f"{_API}/{address}", timeout=8)
        r.raise_for_status()
        data = r.json()["data"][0].get("trc20", [])
    except Exception as exc:                         # network / JSON errors
        logging.warning("TronGrid lookup failed for %s – %s", address, exc)
        return 0.0

    for token in data:                               # each item is {"contract": "value"}
        if _USDT in token:
            raw = _d.Decimal(token[_USDT])           # integer string
            return float(raw / _d.Decimal(1_000_000))  # 6 decimals
    return 0.0


def total_usdt(addresses: list[str]) -> float:
    return sum(usdt_balance(a) for a in addresses)
