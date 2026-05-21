import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import generate
import vaults


class VaultsKongSourcingTests(unittest.TestCase):
    def test_katana_kong_apy_adds_kat_rewards_on_top_of_oracle_net_apy(self) -> None:
        kong_vault = {
            "name": "AUSD yVault",
            "address": "0x93Fec6639717b6215A48E5a72a162C50DCC40d68",
            "chainId": 747474,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "yvAUSD",
            "asset": {"symbol": "AUSD"},
            "tvl": 1_638_954.52,
            "isHidden": False,
            "isRetired": False,
            "performance": {
                "oracle": {"netAPY": 0.0010258},
                "estimated": {
                    "components": {
                        "katanaNativeYield": 0.0888600217,
                        "katanaAppRewardsAPR": 0.0,
                        "fixedRateKatanaRewards": 0.0323715,
                    }
                },
                "historical": {"net": 0.4342},
            },
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 3.33973, places=6)
        self.assertEqual(result["chain"], "katana")

    def test_non_katana_kong_apy_uses_estimated_apy_before_oracle_net_apy(self) -> None:
        kong_vault = {
            "name": "USDT-1 yVault",
            "address": "0x310B7Ea7475A0B449Cfd73bE81522F1B88eFAFaa",
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "yvUSDT-1",
            "asset": {"symbol": "USDT"},
            "tvl": 7_179_754.15,
            "isHidden": False,
            "isRetired": False,
            "performance": {
                "estimated": {"apy": 0.0514},
                "oracle": {"netAPY": 0.0392, "apy": 0.0437, "netAPR": 0.0387},
                "historical": {"net": 0.0278},
            },
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 5.14, places=6)
        self.assertEqual(result["chain"], "mainnet")

    def test_katana_kong_apy_uses_estimated_apy_when_present_without_double_counting_rewards(self) -> None:
        kong_vault = {
            "name": "vbUSDT yVault",
            "address": "0x9A6bd7B6Fd5C4F87eb66356441502fc7dCdd185B",
            "chainId": 747474,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "yvvbUSDT",
            "asset": {"symbol": "USDT"},
            "tvl": 8_700_000.0,
            "isHidden": False,
            "isRetired": False,
            "performance": {
                "estimated": {
                    "apy": 0.0494,
                    "components": {
                        "katanaAppRewardsAPR": 0.0100,
                        "fixedRateKatanaRewards": 0.0200,
                    },
                },
                "oracle": {"netAPY": 0.0050},
            },
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 4.94, places=6)
        self.assertEqual(result["chain"], "katana")

    def test_build_vault_from_kong_uses_onchain_fallback_when_kong_apy_missing(self) -> None:
        kong_vault = {
            "name": "WETH-1 yVault",
            "address": "0xc56413869c6CDf96496f2b1eF801fEDBdFA7dDB0",
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "yvWETH-1",
            "asset": {"symbol": "WETH"},
            "tvl": 9_000_000.0,
            "isHidden": False,
            "isRetired": False,
            "performance": {"estimated": {}, "oracle": {}},
        }
        fallback = {
            str(kong_vault["address"]).lower(): {
                "name": "WETH-1 yVault",
                "chain": "mainnet",
                "chain_id": 1,
                "address": kong_vault["address"],
                "apr": 1.77,
                "tvl_usd": 9_000_000.0,
            }
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address=fallback)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 1.77, places=6)
        self.assertAlmostEqual(result["tvl_usd"], 9_000_000.0, places=6)

    def test_build_vault_from_kong_includes_yvusd_variants_even_though_kind_is_none(self) -> None:
        unlocked = {
            "name": "yvUSD",
            "address": "0x696d02Db93291651ED510704c9b286841d506987",
            "chainId": 1,
            "kind": "None",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "yvUSD",
            "asset": {"symbol": "USDC"},
            "tvl": 4_226_656.79,
            "isHidden": False,
            "isRetired": False,
            "performance": {
                "oracle": {"netAPY": 0.04219886312452559},
                "estimated": {"apy": 0.04306628045504346},
            },
        }
        locked = {
            "name": "Locked yvUSD",
            "address": "0xAaaFEa48472f77563961Cdb53291DEDfB46F9040",
            "chainId": 1,
            "kind": "None",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "symbol": "Locked yvUSD",
            "asset": {"symbol": "yvUSD"},
            "tvl": 2_538_959.03,
            "isHidden": False,
            "isRetired": False,
            "performance": {
                "oracle": {"netAPY": 0.010377669588454097},
                "estimated": {"apy": 0.05553174142860273},
            },
        }

        unlocked_result = vaults.build_vault_from_kong(unlocked, fallback_by_address={})
        locked_result = vaults.build_vault_from_kong(locked, fallback_by_address={})

        self.assertIsNotNone(unlocked_result)
        self.assertIsNotNone(locked_result)
        assert unlocked_result is not None
        assert locked_result is not None
        self.assertAlmostEqual(unlocked_result["apr"], 4.306628045504346, places=6)
        self.assertAlmostEqual(locked_result["apr"], 5.553174142860273, places=6)

    def test_get_vault_bucket_treats_yvusd_variants_as_stablecoin(self) -> None:
        self.assertEqual(vaults.get_vault_bucket("Locked yvUSD", "yvUSD", None), "usd")
        self.assertEqual(vaults.get_vault_bucket("yvUSD", "USDC", None), "usd")

    def test_build_vault_from_kong_skips_non_v3_or_non_multi_strategy_vaults(self) -> None:
        kong_vault = {
            "name": "Curve RSR-FRAXBP Factory yVault",
            "address": "0x8Aa95B71D8e0e1C7949bd84223E0C7911D85171C",
            "chainId": 1,
            "kind": "Legacy",
            "type": "Automated Yearn Vault",
            "v3": False,
            "origin": "yearn",
            "asset": {"symbol": "RSRcrvFRAX-f"},
            "tvl": 0,
            "isHidden": False,
            "isRetired": False,
            "performance": {"oracle": {"netAPY": 999999.0}},
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNone(result)

    def test_get_data_falls_back_to_onchain_when_kong_fetch_fails(self) -> None:
        fallback_payload = {
            "top_usd": [{"name": "USDT-1 yVault", "apr": 5.14, "tvl_usd": 1000.0}],
            "top_crypto": [{"name": "WETH-1 yVault", "apr": 1.77, "tvl_usd": 2000.0}],
        }

        with patch("vaults.fetch_kong_vaults", side_effect=RuntimeError("kong down")), patch(
            "vaults.get_data_onchain", return_value=fallback_payload
        ):
            result = vaults.get_data()

        self.assertEqual(result, fallback_payload)


class GenerateFormattingTests(unittest.TestCase):
    def test_render_vault_list_uses_apy_label(self) -> None:
        rows = generate.render_vault_list(
            [
                {
                    "name": "AUSD yVault",
                    "chain": "katana",
                    "chain_id": 747474,
                    "address": "0x93Fec6639717b6215A48E5a72a162C50DCC40d68",
                    "apr": 0.10258,
                    "tvl_usd": 1_638_954.52,
                }
            ]
        )

        self.assertEqual(
            rows[0],
            "- [**AUSD yVault**](https://yearn.fi/v3/747474/0x93Fec6639717b6215A48E5a72a162C50DCC40d68) (katana): **0.10%** APY | $1.6M TVL",
        )


if __name__ == "__main__":
    unittest.main()
