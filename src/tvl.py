from typing import Any
from urllib.request import urlopen

from utils import fetch_eth_price, get_previous_week_data, get_week_and_year, save_cache

CACHE_NAME = "tvl"


def fetch_yearn_tvl() -> float:
    with urlopen("https://api.llama.fi/tvl/yearn") as r:
        return float(r.read().decode())


def fetch_defi_tvl() -> float:
    import json

    with urlopen("https://api.llama.fi/v2/historicalChainTvl") as r:
        data: list[dict[str, Any]] = json.loads(r.read().decode())
        return float(data[-1]["tvl"])


def fetch_yield_aggregator_tvl() -> float:
    import json

    with urlopen("https://api.llama.fi/protocols") as r:
        data: list[dict[str, Any]] = json.loads(r.read().decode())
        return float(sum(p.get("tvl") or 0 for p in data if p.get("category") == "Yield Aggregator"))


def get_data() -> dict[str, Any]:
    week, year = get_week_and_year()
    eth_price = fetch_eth_price()

    yearn_tvl = fetch_yearn_tvl()
    defi_tvl = fetch_defi_tvl()
    ya_tvl = fetch_yield_aggregator_tvl()

    tvl_eth = yearn_tvl / eth_price

    defi_tvl_eth = defi_tvl / eth_price
    ya_tvl_eth = ya_tvl / eth_price

    prev = get_previous_week_data(CACHE_NAME, week, year)
    if prev:
        wow_usd = (yearn_tvl - prev["tvl_usd"]) / prev["tvl_usd"] * 100
        wow_eth = (tvl_eth - prev["tvl_eth"]) / prev["tvl_eth"] * 100
        defi_wow = (defi_tvl - prev["defi_tvl_usd"]) / prev["defi_tvl_usd"] * 100
        prev_ya_tvl = prev.get("ya_tvl_usd")
        ya_wow = (ya_tvl - prev_ya_tvl) / prev_ya_tvl * 100 if prev_ya_tvl else None
    else:
        wow_usd = None
        wow_eth = None
        defi_wow = None
        ya_wow = None

    save_cache(
        CACHE_NAME,
        {
            "week": week,
            "year": year,
            "tvl_usd": yearn_tvl,
            "tvl_eth": tvl_eth,
            "defi_tvl_usd": defi_tvl,
            "ya_tvl_usd": ya_tvl,
        },
    )

    prev_defi_eth = prev["defi_tvl_usd"] / eth_price if prev and "defi_tvl_usd" in prev else None
    prev_ya_eth = prev["ya_tvl_usd"] / eth_price if prev and "ya_tvl_usd" in prev else None

    return {
        "week": week,
        "year": year,
        "tvl_usd": yearn_tvl,
        "tvl_eth": tvl_eth,
        "defi_tvl_usd": defi_tvl,
        "defi_tvl_eth": defi_tvl_eth,
        "ya_tvl_usd": ya_tvl,
        "ya_tvl_eth": ya_tvl_eth,
        "yearn_share_defi": yearn_tvl / defi_tvl * 100,
        "yearn_share_ya": yearn_tvl / ya_tvl * 100,
        "prev_tvl_usd": prev["tvl_usd"] if prev else None,
        "prev_tvl_eth": prev["tvl_eth"] if prev else None,
        "prev_defi_tvl_usd": prev["defi_tvl_usd"] if prev and "defi_tvl_usd" in prev else None,
        "prev_defi_tvl_eth": prev_defi_eth,
        "prev_ya_tvl_usd": prev["ya_tvl_usd"] if prev and "ya_tvl_usd" in prev else None,
        "prev_ya_tvl_eth": prev_ya_eth,
        "wow_usd_pct": wow_usd,
        "wow_eth_pct": wow_eth,
        "defi_wow_pct": defi_wow,
        "ya_wow_pct": ya_wow,
    }
