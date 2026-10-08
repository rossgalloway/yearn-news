from typing import Any

from utils import get_web3, load_abi

REWARD_DISTRIBUTOR_ADDRESS = "0x1d02F6A86Ed5650f93E40FCD62fa5727c32ad746"
YVCRVUSD2_ADDRESS = "0xBF319dDC2Edc1Eb6FDf9910E39b37Be221C8805F"
REWARD_DISTRIBUTOR_START_TIME = 1766071079


def get_data(reporting_week: int) -> dict[str, Any]:
    """Fetch a completed yYB reward cycle and its prior cycle."""
    w3 = get_web3("mainnet")

    # Get reward distributor data
    rd_abi = load_abi("reward_distributor")
    rd_contract = w3.eth.contract(
        address=w3.to_checksum_address(REWARD_DISTRIBUTOR_ADDRESS),
        abi=rd_abi,
    )

    prior_week = reporting_week - 1

    reward_amount = rd_contract.functions.weeklyRewardAmount(reporting_week).call()
    prev_reward_amount = rd_contract.functions.weeklyRewardAmount(prior_week).call()

    # Rewards are in yvcrvUSD-2 vault tokens (18 decimals)
    rewards_vault_tokens = reward_amount / 1e18
    prev_rewards_vault_tokens = prev_reward_amount / 1e18

    # Get pricePerShare to convert to crvUSD
    vault_abi = load_abi("vault")
    vault_contract = w3.eth.contract(
        address=w3.to_checksum_address(YVCRVUSD2_ADDRESS),
        abi=vault_abi,
    )
    price_per_share = vault_contract.functions.pricePerShare().call()
    pps = price_per_share / 1e18

    rewards_crvusd = rewards_vault_tokens * pps
    prev_rewards_crvusd = prev_rewards_vault_tokens * pps

    # Calculate WoW
    wow_pct = None
    if prev_rewards_crvusd > 0:
        wow_pct = ((rewards_crvusd - prev_rewards_crvusd) / prev_rewards_crvusd) * 100

    return {
        "rewards_crvusd": rewards_crvusd,
        "prev_rewards_crvusd": prev_rewards_crvusd,
        "wow_pct": wow_pct,
        "distributor_week": reporting_week,
    }
