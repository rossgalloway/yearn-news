import json
from typing import Any
from urllib.request import urlopen

from utils import (
    APR_ORACLE_ADDRESS,
    CHAINS,
    REGISTRY_ADDRESSES,
    fetch_btc_price,
    fetch_eth_price,
    fetch_sky_price,
    fetch_yyb_price,
    get_web3,
    load_abi,
    multicall,
)

KONG_VAULTS_API = "https://kong.yearn.fi/api/rest/list/vaults"
KATANA_APR_API = "https://katana-apr.yearn.fi/api/vaults"

MULTI_STRATEGY_TYPE = 1
KATANA_CHAIN_ID = 747474
YVUSD_UNLOCKED_ADDRESS = "0x696d02db93291651ed510704c9b286841d506987"
YVUSD_LOCKED_ADDRESS = "0xaaafea48472f77563961cdb53291dedfb46f9040"
YBOLD_ADDRESS = "0x9f4330700a36b29952869fac9b33f45eedd8a3d8"
YSYBOLD_ADDRESS = "0x23346b04a7f55b8760e5860aa5a77383d63491cd"

CHAIN_NAMES = {
    1: "mainnet",
    42161: "arbitrum",
    8453: "base",
    KATANA_CHAIN_ID: "katana",
}

STABLECOIN_SYMBOLS = {
    "USDC",
    "USDT",
    "DAI",
    "FRAX",
    "LUSD",
    "TUSD",
    "USDE",
    "SUSDE",
    "GHO",
    "CRVUSD",
    "USD0",
    "PYUSD",
    "USDP",
    "SDAI",
    "AUSD",
    "BOLD",
    "USDS",
    "USDAF",
    "YVUSD",
}

WETH_ADDRESSES = {
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "0x4200000000000000000000000000000000000006",
    "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    "0xee7d8bcfb72bc1880d0cf19822eb0a2e6577ab62",
}

WBTC_ADDRESSES = {
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",
    "0x0555e30da8f98308edb960aa94c0db47230d2b9c",
    "0x0913da6da4b42f538b445599b46bb4622342cf52",
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
}

SKY = "0x56072c95faa701256059aa122697b133aded9279"
YYB = "0x22222222aea0076fca927a3f44dc0b4fdf9479d6"
CRYPTO_TOKENS = WETH_ADDRESSES | WBTC_ADDRESSES | {SKY, YYB}

EXCLUDED_VAULTS = {
    "0x252b965400862d94bda35fecf7ee0f204a53cc36",
}


def fetch_json_value(url: str) -> Any:
    with urlopen(url) as response:
        return json.loads(response.read().decode())


def normalize_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def is_yvusd_address(address: str) -> bool:
    return address in {YVUSD_UNLOCKED_ADDRESS, YVUSD_LOCKED_ADDRESS}


def should_include_vault_name(name: str) -> bool:
    normalized = name.strip().lower()
    if normalized in {"yvusd", "locked yvusd"}:
        return True
    return any(token in name for token in ("yVault", "BOLD", "USDaf")) and "Liquid Locker Compounder" not in name


def get_chain_name(chain_id: int | None) -> str | None:
    if chain_id is None:
        return None
    return CHAIN_NAMES.get(chain_id)


def get_vault_bucket(name: str, asset_symbol: str | None, fallback: dict[str, Any] | None) -> str:
    if fallback and fallback.get("bucket") in {"usd", "crypto"}:
        return str(fallback["bucket"])
    normalized_asset = (asset_symbol or "").upper()
    if normalized_asset in STABLECOIN_SYMBOLS:
        return "usd"
    upper_name = name.upper()
    if any(symbol in upper_name for symbol in STABLECOIN_SYMBOLS):
        return "usd"
    return "crypto"


def resolve_kong_preferred_apy_pct(kong_vault: dict[str, Any]) -> tuple[float | None, str | None]:
    performance = kong_vault.get("performance", {}) or {}
    estimated = performance.get("estimated", {}) or {}
    estimated_apy = normalize_number(estimated.get("apy"))
    if estimated_apy is not None:
        return estimated_apy * 100, "estimated.apy"

    oracle = performance.get("oracle", {}) or {}
    oracle_net_apy = normalize_number(oracle.get("netAPY"))
    if oracle_net_apy is None:
        return None, None
    return oracle_net_apy * 100, "oracle.netAPY"


def resolve_kong_historical_apy_pct(kong_vault: dict[str, Any]) -> float | None:
    performance = kong_vault.get("performance", {}) or {}
    historical = performance.get("historical", {}) or {}
    monthly_net = normalize_number(historical.get("monthlyNet"))
    if monthly_net is not None:
        return monthly_net * 100

    net = normalize_number(historical.get("net"))
    if net is not None:
        return net * 100
    return None


def resolve_katana_reward_pct(kong_vault: dict[str, Any]) -> float:
    performance = kong_vault.get("performance", {}) or {}
    estimated = performance.get("estimated", {}) or {}
    components = estimated.get("components", {}) or {}
    reward_parts = [
        normalize_number(components.get("katanaAppRewardsAPR")),
        normalize_number(components.get("fixedRateKatanaRewards")),
        normalize_number(components.get("FixedRateKatanaRewards")),
    ]
    return sum(part for part in reward_parts if part is not None) * 100


def resolve_kong_performance_source(
    kong_vault: dict[str, Any], kong_by_address: dict[str, dict[str, Any]] | None
) -> dict[str, Any]:
    address = str(kong_vault.get("address", "")).lower()
    if address == YBOLD_ADDRESS and kong_by_address:
        return kong_by_address.get(YSYBOLD_ADDRESS, kong_vault)
    return kong_vault


def should_include_kong_vault(kong_vault: dict[str, Any]) -> bool:
    address = str(kong_vault.get("address", "")).lower()
    is_yvusd = is_yvusd_address(address)
    if not is_yvusd and kong_vault.get("isHighlighted") is not True:
        return False
    if kong_vault.get("v3") is not True:
        return False
    if str(kong_vault.get("origin") or "") != "yearn":
        return False
    if is_yvusd:
        return True
    if str(kong_vault.get("kind") or "") != "Multi Strategy":
        return False
    return True


def build_vault_from_kong(
    kong_vault: dict[str, Any],
    fallback_by_address: dict[str, dict[str, Any]],
    kong_by_address: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    address = str(kong_vault.get("address", "")).lower()
    fallback = fallback_by_address.get(address)
    if not should_include_kong_vault(kong_vault):
        return None
    name = str(kong_vault.get("name") or (fallback or {}).get("name") or "").strip()
    if not name or not should_include_vault_name(name):
        return fallback
    if kong_vault.get("isHidden") or kong_vault.get("isRetired"):
        return None

    chain_id_raw = kong_vault.get("chainId")
    chain_id = int(chain_id_raw) if isinstance(chain_id_raw, int) else normalize_number(chain_id_raw)
    normalized_chain_id = int(chain_id) if chain_id is not None else (fallback or {}).get("chain_id")
    chain_name = get_chain_name(normalized_chain_id) or (fallback or {}).get("chain")
    if normalized_chain_id is None or chain_name is None:
        return fallback

    performance_source = resolve_kong_performance_source(kong_vault, kong_by_address)
    apr_pct, apy_source = resolve_kong_preferred_apy_pct(performance_source)
    if apr_pct is not None and normalized_chain_id == KATANA_CHAIN_ID and apy_source != "estimated.apy":
        apr_pct += resolve_katana_reward_pct(performance_source)
    historical_apy_pct = resolve_kong_historical_apy_pct(performance_source)
    if historical_apy_pct is not None and normalized_chain_id == KATANA_CHAIN_ID:
        historical_apy_pct += resolve_katana_reward_pct(performance_source)

    if apr_pct is None and fallback:
        apr_pct = normalize_number(fallback.get("apr"))
    tvl_usd = normalize_number(kong_vault.get("tvl"))
    if tvl_usd is None and fallback:
        tvl_usd = normalize_number(fallback.get("tvl_usd"))

    if apr_pct is None or tvl_usd is None:
        return fallback

    return {
        "name": name,
        "chain": chain_name,
        "chain_id": normalized_chain_id,
        "address": kong_vault.get("address") or (fallback or {}).get("address"),
        "apr": apr_pct,
        "historical_apy": historical_apy_pct,
        "tvl_usd": tvl_usd,
    }


def fetch_kong_vaults() -> list[dict[str, Any]]:
    payload = fetch_json_value(KONG_VAULTS_API)
    if not isinstance(payload, list):
        raise ValueError("Kong vault payload was not a list")
    return [item for item in payload if isinstance(item, dict)]


def fetch_katana_aprs() -> dict[str, float]:
    try:
        data = fetch_json_value(KATANA_APR_API)
        aprs = {}
        for addr, vault_data in data.items():
            if not isinstance(vault_data, dict):
                continue
            extra = vault_data.get("apr", {}).get("extra", {})
            katana_app_rewards = normalize_number(extra.get("katanaAppRewardsAPR")) or 0.0
            fixed_rate_rewards = (
                normalize_number(extra.get("fixedRateKatanaRewards"))
                or normalize_number(extra.get("FixedRateKatanaRewards"))
                or 0.0
            )
            native_yield = normalize_number(extra.get("katanaNativeYield")) or 0.0
            total_apr = katana_app_rewards + fixed_rate_rewards + native_yield
            aprs[str(addr).lower()] = total_apr * 100
        return aprs
    except Exception:
        return {}


def collect_onchain_vaults() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    usd_vaults: list[dict[str, Any]] = []
    crypto_vaults: list[dict[str, Any]] = []

    eth_price = fetch_eth_price()
    btc_price = fetch_btc_price()
    sky_price = fetch_sky_price()
    yyb_price = fetch_yyb_price()
    katana_aprs = fetch_katana_aprs()

    registry_abi = load_abi("registry")
    vault_abi = load_abi("vault")
    apr_oracle_abi = load_abi("apr_oracle")

    for chain_name, chain_info in CHAINS.items():
        try:
            w3 = get_web3(chain_name)
        except ValueError:
            continue

        vault_addresses: list[str] = []
        registry_for_vault: dict[str, str] = {}

        for registry_addr in REGISTRY_ADDRESSES:
            registry = w3.eth.contract(address=w3.to_checksum_address(registry_addr), abi=registry_abi)
            try:
                all_vaults = registry.functions.getAllEndorsedVaults().call()
                for sublist in all_vaults:
                    for addr in sublist:
                        if addr not in registry_for_vault:
                            vault_addresses.append(addr)
                            registry_for_vault[addr] = registry_addr
            except Exception:
                continue

        if not vault_addresses:
            continue

        vault_contract = w3.eth.contract(abi=vault_abi)
        apr_oracle = w3.eth.contract(address=w3.to_checksum_address(APR_ORACLE_ADDRESS), abi=apr_oracle_abi)

        info_calls = []
        for addr in vault_addresses:
            checksum_addr = w3.to_checksum_address(addr)
            reg_addr = registry_for_vault[addr]
            registry = w3.eth.contract(address=w3.to_checksum_address(reg_addr), abi=registry_abi)
            info_calls.append((reg_addr, registry.encode_abi("vaultInfo", args=[checksum_addr])))

        info_results = multicall(w3, info_calls)

        multi_strategy_vaults = []
        for i, addr in enumerate(vault_addresses):
            if addr.lower() in EXCLUDED_VAULTS:
                continue
            success, data = info_results[i]
            if not success:
                continue
            decoded = w3.codec.decode(["address", "uint96", "uint64", "uint128", "uint64", "string"], data)
            vault_type = decoded[2]
            if vault_type == MULTI_STRATEGY_TYPE:
                multi_strategy_vaults.append(addr)

        if not multi_strategy_vaults:
            continue

        is_katana = chain_name == "katana"
        calls = []
        for addr in multi_strategy_vaults:
            checksum_addr = w3.to_checksum_address(addr)
            calls.append((addr, vault_contract.encode_abi("name")))
            calls.append((addr, vault_contract.encode_abi("asset")))
            calls.append((addr, vault_contract.encode_abi("totalAssets")))
            calls.append((addr, vault_contract.encode_abi("decimals")))
            if not is_katana:
                calls.append((APR_ORACLE_ADDRESS, apr_oracle.encode_abi("getStrategyApr", args=[checksum_addr, 0])))

        results = multicall(w3, calls)
        calls_per_vault = 4 if is_katana else 5

        for i, addr in enumerate(multi_strategy_vaults):
            base_idx = i * calls_per_vault
            name_success, name_data = results[base_idx]
            asset_success, asset_data = results[base_idx + 1]
            total_assets_success, total_assets_data = results[base_idx + 2]
            decimals_success, decimals_data = results[base_idx + 3]

            if not all([name_success, asset_success, total_assets_success, decimals_success]):
                continue

            name = w3.codec.decode(["string"], name_data)[0]
            if not should_include_vault_name(name):
                continue

            asset = w3.codec.decode(["address"], asset_data)[0].lower()
            total_assets = w3.codec.decode(["uint256"], total_assets_data)[0]
            decimals = w3.codec.decode(["uint8"], decimals_data)[0]

            if is_katana:
                apr_pct = katana_aprs.get(addr.lower(), 0.0)
            else:
                apr_success, apr_data = results[base_idx + 4]
                apr_pct = 0.0
                if apr_success:
                    apr_raw = w3.codec.decode(["uint256"], apr_data)[0]
                    apr_pct = (apr_raw / 1e18) * 100

            amount = total_assets / (10**decimals)
            if asset in WETH_ADDRESSES:
                tvl_usd = amount * eth_price
            elif asset in WBTC_ADDRESSES:
                tvl_usd = amount * btc_price
            elif asset == SKY:
                tvl_usd = amount * sky_price
            elif asset == YYB:
                tvl_usd = amount * yyb_price
            else:
                tvl_usd = amount

            vault = {
                "name": name,
                "chain": chain_name,
                "chain_id": chain_info["chain_id"],
                "address": addr,
                "apr": apr_pct,
                "tvl_usd": tvl_usd,
                "bucket": "crypto" if asset in CRYPTO_TOKENS else "usd",
            }

            if vault["bucket"] == "crypto":
                crypto_vaults.append(vault)
            else:
                usd_vaults.append(vault)

    return usd_vaults, crypto_vaults


def sort_and_slice_vaults(usd_vaults: list[dict[str, Any]], crypto_vaults: list[dict[str, Any]]) -> dict[str, Any]:
    usd_vaults.sort(key=lambda x: x["apr"], reverse=True)
    crypto_vaults.sort(key=lambda x: x["apr"], reverse=True)
    return {"top_usd": usd_vaults[:5], "top_crypto": crypto_vaults[:5]}


def get_data_onchain() -> dict[str, Any]:
    usd_vaults, crypto_vaults = collect_onchain_vaults()
    return sort_and_slice_vaults(usd_vaults, crypto_vaults)


def index_fallback_vaults(*vault_groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    fallback_by_address: dict[str, dict[str, Any]] = {}
    for vault_group in vault_groups:
        for vault in vault_group:
            fallback_by_address[str(vault["address"]).lower()] = vault
    return fallback_by_address


def get_data() -> dict[str, Any]:
    try:
        kong_vaults = fetch_kong_vaults()
    except Exception:
        return get_data_onchain()

    usd_fallbacks, crypto_fallbacks = collect_onchain_vaults()
    fallback_by_address = index_fallback_vaults(usd_fallbacks, crypto_fallbacks)
    kong_by_address = {str(vault.get("address", "")).lower(): vault for vault in kong_vaults}

    usd_vaults: list[dict[str, Any]] = []
    crypto_vaults: list[dict[str, Any]] = []
    for kong_vault in kong_vaults:
        built_vault = build_vault_from_kong(kong_vault, fallback_by_address, kong_by_address)
        if built_vault is None:
            continue
        address = str(built_vault["address"]).lower()
        fallback = fallback_by_address.get(address)
        asset = kong_vault.get("asset", {}) if isinstance(kong_vault.get("asset"), dict) else {}
        bucket = get_vault_bucket(built_vault["name"], asset.get("symbol"), fallback)
        built_vault["bucket"] = bucket
        if bucket == "crypto":
            crypto_vaults.append(built_vault)
        else:
            usd_vaults.append(built_vault)

    return sort_and_slice_vaults(usd_vaults, crypto_vaults)
