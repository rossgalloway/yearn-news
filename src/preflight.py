"""Read-only readiness checks for newsletter generation."""

from dataclasses import dataclass
from typing import Any, Callable

from utils import CHAINS, fetch_json_data, get_web3

KONG_VAULTS_API = "https://kong.yearn.fi/api/rest/list/vaults"
KATANA_APR_API = "https://katana-apr.yearn.fi/api/vaults"
YEARN_TVL_API = "https://api.llama.fi/tvl/yearn"
DEFI_TVL_API = "https://api.llama.fi/v2/historicalChainTvl"
PROTOCOLS_API = "https://api.llama.fi/protocols"
ETH_PRICE_API = "https://coins.llama.fi/prices/current/coingecko:ethereum"
BTC_PRICE_API = "https://coins.llama.fi/prices/current/coingecko:bitcoin"
SKY_PRICE_API = "https://coins.llama.fi/prices/current/ethereum:0x56072C95FAA701256059aa122697B133aDEd9279"
YYB_PRICE_API = "https://coins.llama.fi/prices/current/ethereum:0x22222222aEA0076fCA927a3f44dc0B4FdF9479D6"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    required: bool


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def check_http(
    name: str,
    url: str,
    validator: Callable[[Any], bool],
    *,
    required: bool,
) -> CheckResult:
    try:
        payload = fetch_json_data(url, source=name)
        if not validator(payload):
            return CheckResult(name, "unavailable", f"unexpected {type(payload).__name__} response", required)
        return CheckResult(name, "ready", "reachable and returned the expected response shape", required)
    except Exception as exc:
        return CheckResult(name, "unavailable", str(exc), required)


def check_rpc(chain: str, *, required: bool) -> CheckResult:
    name = f"{chain} RPC"
    if not CHAINS[chain]["rpc"]:
        return CheckResult(name, "unavailable", "RPC URL is not configured", required)

    try:
        web3 = get_web3(chain)
        chain_id = web3.eth.chain_id
        expected_chain_id = CHAINS[chain]["chain_id"]
        if chain_id != expected_chain_id:
            return CheckResult(
                name, "unavailable", f"expected chain ID {expected_chain_id}, received {chain_id}", required
            )
        return CheckResult(name, "ready", f"connected to chain ID {chain_id}", required)
    except Exception as exc:
        return CheckResult(name, "unavailable", str(exc), required)


def run_checks() -> list[CheckResult]:
    checks = [
        check_http("DeFiLlama Yearn TVL", YEARN_TVL_API, is_number, required=True),
        check_http("DeFiLlama total DeFi TVL", DEFI_TVL_API, is_non_empty_list, required=True),
        check_http("DeFiLlama protocol list", PROTOCOLS_API, is_non_empty_list, required=True),
        check_http("DeFiLlama ETH price", ETH_PRICE_API, is_dict, required=True),
        check_http("DeFiLlama BTC price", BTC_PRICE_API, is_dict, required=True),
        check_http("DeFiLlama SKY price", SKY_PRICE_API, is_dict, required=True),
        check_http("DeFiLlama yYB price", YYB_PRICE_API, is_dict, required=True),
        check_http("Kong vault list", KONG_VAULTS_API, is_non_empty_list, required=False),
        check_http("Katana reward service", KATANA_APR_API, is_dict, required=False),
        check_rpc("mainnet", required=True),
        check_rpc("arbitrum", required=False),
        check_rpc("base", required=False),
        check_rpc("katana", required=False),
    ]
    return checks


def main() -> int:
    results = run_checks()
    required_failures = [result for result in results if result.required and result.status != "ready"]
    optional_failures = [result for result in results if not result.required and result.status != "ready"]

    print("Yearn News preflight")
    for result in results:
        marker = "OK" if result.status == "ready" else ("FAIL" if result.required else "WARN")
        print(f"[{marker}] {result.name}: {result.detail}")

    if required_failures:
        print(f"\nNot ready: {len(required_failures)} required check(s) failed.")
        return 1
    if optional_failures:
        print(f"\nReady with reduced fallback coverage: {len(optional_failures)} optional check(s) failed.")
        return 0

    print("\nReady to generate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
