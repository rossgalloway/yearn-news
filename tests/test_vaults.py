import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import generate
import utils
import vaults


class VaultsKongSourcingTests(unittest.TestCase):
    def test_katana_kong_apy_and_historical_add_rewards_on_top_of_base_apy(self) -> None:
        kong_vault = {
            "name": "AUSD yVault",
            "address": "0x93Fec6639717b6215A48E5a72a162C50DCC40d68",
            "chainId": 747474,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "isHighlighted": True,
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
        self.assertAlmostEqual(result["historical_apy"], 46.65715, places=6)
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
            "isHighlighted": True,
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
        self.assertAlmostEqual(result["historical_apy"], 2.78, places=6)
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
            "isHighlighted": True,
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
                "historical": {"monthlyNet": 0.0268, "net": 0.0198},
            },
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 4.94, places=6)
        self.assertAlmostEqual(result["historical_apy"], 5.68, places=6)
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
            "isHighlighted": True,
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
            "isHighlighted": True,
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
            "isHighlighted": True,
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

    def test_build_vault_from_kong_requires_highlighted_flag_for_non_yvusd_vaults(self) -> None:
        kong_vault = {
            "name": "USDT-1 yVault",
            "address": "0x310B7Ea7475A0B449Cfd73bE81522F1B88eFAFaa",
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "isHighlighted": False,
            "asset": {"symbol": "USDT"},
            "tvl": 7_179_754.15,
            "isHidden": False,
            "isRetired": False,
            "performance": {"estimated": {"apy": 0.0514}},
        }

        self.assertIsNone(vaults.build_vault_from_kong(kong_vault, fallback_by_address={}))

    def test_build_vault_from_kong_skips_non_v3_or_non_multi_strategy_vaults(self) -> None:
        kong_vault = {
            "name": "Curve RSR-FRAXBP Factory yVault",
            "address": "0x8Aa95B71D8e0e1C7949bd84223E0C7911D85171C",
            "chainId": 1,
            "kind": "Legacy",
            "type": "Automated Yearn Vault",
            "v3": False,
            "origin": "yearn",
            "isHighlighted": True,
            "asset": {"symbol": "RSRcrvFRAX-f"},
            "tvl": 0,
            "isHidden": False,
            "isRetired": False,
            "performance": {"oracle": {"netAPY": 999999.0}},
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNone(result)

    def test_build_vault_from_kong_requires_highlighted_flag(self) -> None:
        base_vault = {
            "name": "USDT-1 yVault",
            "address": "0x310B7Ea7475A0B449Cfd73bE81522F1B88eFAFaa",
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "asset": {"symbol": "USDT"},
            "tvl": 7_179_754.15,
            "isHidden": False,
            "isRetired": False,
            "performance": {"estimated": {"apy": 0.0514}},
        }

        self.assertIsNone(vaults.build_vault_from_kong({**base_vault, "isHighlighted": False}, fallback_by_address={}))
        self.assertIsNone(vaults.build_vault_from_kong(base_vault, fallback_by_address={}))

    def test_build_vault_from_kong_accepts_highlighted_vaults(self) -> None:
        kong_vault = {
            "name": "USDT-1 yVault",
            "address": "0x310B7Ea7475A0B449Cfd73bE81522F1B88eFAFaa",
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "isHighlighted": True,
            "asset": {"symbol": "USDT"},
            "tvl": 7_179_754.15,
            "isHidden": False,
            "isRetired": False,
            "performance": {"estimated": {"apy": 0.0514}},
        }

        result = vaults.build_vault_from_kong(kong_vault, fallback_by_address={})

        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result["apr"], 5.14, places=6)

    def test_get_data_does_not_append_unboosted_onchain_fallbacks_when_kong_is_available(self) -> None:
        address = "0x310B7Ea7475A0B449Cfd73bE81522F1B88eFAFaa"
        kong_vault = {
            "name": "USDT-1 yVault",
            "address": address,
            "chainId": 1,
            "kind": "Multi Strategy",
            "type": "Yearn Vault",
            "v3": True,
            "origin": "yearn",
            "isHighlighted": False,
            "asset": {"symbol": "USDT"},
            "tvl": 7_179_754.15,
            "isHidden": False,
            "isRetired": False,
            "performance": {"estimated": {"apy": 0.0514}},
        }
        fallback = {
            "name": "USDT-1 yVault",
            "chain": "mainnet",
            "chain_id": 1,
            "address": address,
            "apr": 5.14,
            "tvl_usd": 7_179_754.15,
            "bucket": "usd",
        }

        with patch("vaults.fetch_kong_vaults", return_value=[kong_vault]), patch(
            "vaults.collect_onchain_vaults", return_value=([fallback], [])
        ):
            result = vaults.get_data()

        self.assertEqual(result, {"top_usd": [], "top_crypto": []})

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
    def test_format_report_period_uses_monday_date(self) -> None:
        monday = utils.get_report_monday(date(2026, 5, 22))

        self.assertEqual(monday, date(2026, 5, 18))
        self.assertEqual(utils.format_report_period(monday), "Week of May 18, 2026")

    def test_render_overview_uses_only_intro_sentence_without_heading(self) -> None:
        overview = generate.render_overview("Week of April 20, 2026", 17, 2026)

        self.assertEqual(
            overview,
            "Welcome to **The Blue Pill** for *Week of April 20, 2026*. A weekly update covering what's been happening across the Yearn ecosystem.",
        )
        self.assertNotIn("## Overview", overview)
        self.assertNotIn("Week 17, 2026", overview)
        self.assertNotIn("This newsletter is meant", overview)

    def test_render_glance_banner_svg_includes_exact_stats(self) -> None:
        svg = generate.render_glance_banner_svg(
            20,
            2026,
            {"tvl_usd": 243_200_000.0, "tvl_eth": 113_637.0},
            {
                "top_usd": [
                    {
                        "name": "vbUSDT yVault",
                        "chain": "katana",
                        "apr": 8.81,
                        "tvl_usd": 5_400_000.0,
                    }
                ],
                "top_crypto": [
                    {
                        "name": "SKY-1 yVault",
                        "chain": "mainnet",
                        "apr": 4.71,
                        "tvl_usd": 48_400.0,
                    }
                ],
            },
        )

        self.assertIn("Yearn TVL", svg)
        self.assertIn("Top Stable Vault", svg)
        self.assertIn("Top Volatile Vault", svg)
        self.assertIn("$243.2M", svg)
        self.assertIn("vbUSDT", svg)
        self.assertIn("8.81%", svg)
        self.assertIn("SKY-1", svg)
        self.assertIn("4.71%", svg)
        self.assertNotIn("(Katana)", svg)
        self.assertNotIn("(Mainnet)", svg)
        self.assertIn('width="600" height="120"', svg)
        self.assertIn('x1="178.25"', svg)
        self.assertNotIn("Top Vault APY", svg)
        self.assertNotIn("113,637 ETH", svg)
        self.assertNotIn("Week 20, 2026", svg)

    def test_render_glance_banner_svg_uses_compact_wide_layout(self) -> None:
        svg = generate.render_glance_banner_svg(
            20,
            2026,
            {"tvl_usd": 245_900_000.0, "tvl_eth": 113_637.0},
            {
                "top_usd": [{"name": "vbUSDT yVault", "chain": "katana", "apr": 8.50, "tvl_usd": 5_400_000.0}],
                "top_crypto": [{"name": "Very Long Volatile yVault", "chain": "mainnet", "apr": 12.09, "tvl_usd": 1.0}],
            },
        )
        root = ET.fromstring(svg)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        text_nodes = root.findall("svg:text", namespace)
        row_nodes = [node for node in text_nodes if node.findall("svg:tspan", namespace)]

        self.assertEqual(root.attrib["width"], "600")
        self.assertEqual(root.attrib["height"], "120")
        self.assertEqual(len(row_nodes), 2)
        self.assertEqual(row_nodes[0].attrib["x"], "195")
        self.assertEqual(row_nodes[1].attrib["x"], "195")
        self.assertEqual(
            [tspan.text for tspan in row_nodes[0].findall("svg:tspan", namespace)],
            ["Top Stable Vault: ", "vbUSDT", " | 8.50%"],
        )
        self.assertEqual(
            [tspan.text for tspan in row_nodes[1].findall("svg:tspan", namespace)],
            ["Top Volatile Vault: ", "Very Long Volatile", " | 12.09%"],
        )
        self.assertLess(float(row_nodes[0].attrib["y"]), float(row_nodes[1].attrib["y"]))

    def test_render_glance_banner_review_references_generated_svg(self) -> None:
        review_html = generate.render_glance_banner_review_html("abc123")

        self.assertIn('src="output-yearn-glance-banner.svg?v=abc123"', review_html)
        self.assertNotIn("<svg", review_html)
        self.assertIn("loads the same standalone SVG file", review_html)

    def test_render_vault_list_uses_apy_label(self) -> None:
        rows = generate.render_vault_list(
            [
                {
                    "name": "AUSD yVault",
                    "chain": "katana",
                    "chain_id": 747474,
                    "address": "0x93Fec6639717b6215A48E5a72a162C50DCC40d68",
                    "apr": 0.10258,
                    "historical_apy": 1.2345,
                    "tvl_usd": 1_638_954.52,
                }
            ]
        )

        self.assertEqual(
            rows[0],
            "1. [**AUSD yVault**](https://yearn.fi/v3/747474/0x93Fec6639717b6215A48E5a72a162C50DCC40d68) (katana)<br>    **0.10%** APY | **1.23%** Historical APY | $1.6M TVL",
        )

    def test_render_liquid_lockers_uses_inline_locker_labels(self) -> None:
        section = generate.render_liquid_lockers(
            {"rewards_crvusd": 42_221.94, "prev_rewards_crvusd": 31_513.39, "wow_pct": 34.0},
            {"rewards_crvusd": 0.0, "prev_rewards_crvusd": 109.4, "wow_pct": -100.0},
        )

        self.assertEqual(
            section,
            "## Liquid Lockers\n"
            "**yCRV:** This week yCRV stakers received **42,221.94 crvUSD** rewards, compared to **31,513.39 crvUSD** "
            "in the prior week, for a week-over-week change of **+34.0%**\n"
            "\n"
            "**yYB:** This week yYB stakers received **0.00 crvUSD** rewards, compared to **109.40 crvUSD** "
            "in the prior week, for a week-over-week change of **-100.0%**",
        )

    def test_render_x_article_fragment_converts_markdown_subheadings(self) -> None:
        fragment = generate.render_x_article_fragment("## Liquid Lockers\n### yCRV\nRewards copy.\n")

        self.assertIn("<h2>Liquid Lockers</h2>", fragment)
        self.assertIn("<h3>yCRV</h3>", fragment)

    def test_render_x_article_fragment_converts_markdown_to_rich_html(self) -> None:
        fragment = generate.render_x_article_fragment(
            "## Overview\n"
            "Welcome to **The Blue Pill** - *Week 17, 2026*.\n\n"
            "- [**AUSD yVault**](https://yearn.fi/v3/747474/0xabc) (katana): **5.69%** APY\n"
        )

        self.assertIn("<h2>Overview</h2>", fragment)
        self.assertIn("<p>Welcome to <strong>The Blue Pill</strong> - <em>Week 17, 2026</em>.</p>", fragment)
        self.assertIn('<a href="https://yearn.fi/v3/747474/0xabc"><strong>AUSD yVault</strong></a>', fragment)
        self.assertNotIn("##", fragment)
        self.assertNotIn("**", fragment)

    def test_render_x_article_fragment_places_banner_after_glance_heading(self) -> None:
        fragment = generate.render_x_article_fragment(
            "## Yearn at a glance\nYearn TVL: **$245.9M**.\n",
            glance_banner_url="output-yearn-glance-banner.svg?v=abc123",
        )

        self.assertIn(
            '<h2>Yearn at a glance</h2>\n'
            '<figure class="glance-banner"><img src="output-yearn-glance-banner.svg?v=abc123" '
            'alt="Yearn at a glance banner"></figure>\n'
            "<p>Yearn TVL: <strong>$245.9M</strong>.</p>",
            fragment,
        )

    def test_render_x_article_fragment_converts_ordered_markdown_lists(self) -> None:
        fragment = generate.render_x_article_fragment(
            "## Vaults\n"
            "1. [**AUSD yVault**](https://yearn.fi/v3/747474/0xabc) (katana)<br>**5.69%** APY\n"
            "2. [**USDC yVault**](https://yearn.fi/v3/1/0xdef) (mainnet)<br>**4.20%** APY\n"
        )

        self.assertIn("<ol>", fragment)
        self.assertIn("</ol>", fragment)
        self.assertIn('<a href="https://yearn.fi/v3/1/0xdef"><strong>USDC yVault</strong></a>', fragment)
        self.assertIn("<br><strong>4.20%</strong> APY", fragment)
        self.assertNotIn("<ul>", fragment)

    def test_render_x_article_fragment_escapes_url_attributes_once(self) -> None:
        fragment = generate.render_x_article_fragment("Read [the docs](https://example.com?a=1&b=2).")

        self.assertIn('href="https://example.com?a=1&amp;b=2"', fragment)
        self.assertNotIn("&amp;amp;", fragment)

    def test_render_x_article_text_removes_markdown_without_wrapping_paragraphs(self) -> None:
        text = generate.render_x_article_text(
            "## Yearn at a glance\n"
            "Total DeFi TVL declined week-over-week by **~17%**,\n"
            "with Yearn's share at **0.27%**.\n\n"
            "All data is available [here](https://github.com/johnnyonline/yearn-news).\n"
        )

        self.assertIn(
            "Total DeFi TVL declined week-over-week by ~17%, with Yearn's share at 0.27%.",
            text,
        )
        self.assertIn("here (https://github.com/johnnyonline/yearn-news)", text)
        self.assertNotIn("**", text)
        self.assertNotIn("[here]", text)


if __name__ == "__main__":
    unittest.main()
