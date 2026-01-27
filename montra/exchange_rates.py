import os
import requests
from django.core.cache import cache

API_BASE = "https://api.exchangerate.host"
ACCESS_KEY = os.environ.get("EXCHANGERATE_API_KEY")
DEFAULT_TTL = int(os.environ.get("EXCHANGE_RATE_TTL", "43200"))

TOP_CURRENCIES = ["USD", "GBP", "CHF", "JPY", "AUD", "CAD", "SEK", "NOK", "CZK", "PLN"]

def _cache_key(base: str, symbols: list[str]) -> str:
    symbols_norm = ",".join(sorted(s.strip().upper() for s in symbols if s))
    return f"fx:live:base={base.upper()}:symbols={symbols_norm}"

def _call_live(source: str, currencies: list[str]) -> dict:
    params = {
        "source": source.upper(),
        "currencies": ",".join(c.upper() for c in currencies),
    }
    if ACCESS_KEY:
        params["access_key"] = ACCESS_KEY

    r = requests.get(f"{API_BASE}/live", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_latest_rates(base: str = "EUR", symbols: list[str] | None = None) -> dict:
    """
    Returns:
      {"base": "EUR", "rates": {"USD": 1.09, "GBP": 0.85}, "timestamp": 123..., "source": "cache|api|api_fallback"}
    Uses Redis cache to reduce external calls.
    """
    if not symbols:
        symbols = ["USD"]

    base = base.upper()
    symbols = [s.upper() for s in symbols]

    key = _cache_key(base, symbols)
    cached = cache.get(key)
    if cached is not None:
        cached["source"] = "cache"
        return cached

    # 1) Try direct base (source=base)
    data = _call_live(base, symbols)
    if data.get("success") is True and "quotes" in data:
        # quotes are like EURUSD? Actually docs show USDGBP etc. With source it should be SOURCE+TARGET
        quotes = data.get("quotes") or {}
        rates = {}
        for s in symbols:
            pair = f"{base}{s}"
            if pair in quotes:
                rates[s] = quotes[pair]

        payload = {
            "base": base,
            "rates": rates,
            "timestamp": data.get("timestamp"),
            "source": "api",
        }
        cache.set(key, payload, timeout=DEFAULT_TTL)
        return payload

    # 2) Fallback: use USD as source and compute cross rates
    # Need USD->base and USD->symbol to compute base->symbol:
    # base->sym = (USD->sym) / (USD->base)
    need = sorted(set(symbols + [base]))
    data_usd = _call_live("USD", need)

    if not (data_usd.get("success") is True and "quotes" in data_usd):
        # give a useful error back
        return {
            "base": base,
            "rates": {},
            "timestamp": data_usd.get("timestamp"),
            "source": "api_error",
            "error": data_usd.get("error") or data.get("error") or "Unknown API error",
        }

    quotes = data_usd.get("quotes") or {}
    usd_to_base = quotes.get(f"USD{base}")
    if not usd_to_base:
        return {
            "base": base,
            "rates": {},
            "timestamp": data_usd.get("timestamp"),
            "source": "api_error",
            "error": f"Missing USD{base} in quotes",
        }

    rates = {}
    for s in symbols:
        usd_to_s = quotes.get(f"USD{s}")
        if usd_to_s:
            rates[s] = usd_to_s / usd_to_base

    payload = {
        "base": base,
        "rates": rates,
        "timestamp": data_usd.get("timestamp"),
        "source": "api_fallback",
    }
    cache.set(key, payload, timeout=DEFAULT_TTL)
    return payload

def get_top_rates(base: str = "EUR") -> dict:
    return get_latest_rates(base=base, symbols=TOP_CURRENCIES)