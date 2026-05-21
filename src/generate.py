from pathlib import Path
from typing import Any

import content
import tvl
import vaults
import ycrv
import yyb
from utils import fmt_usd, get_week_and_year

OUTPUT_FILE = Path(__file__).parent.parent / "output.md"


def render_overview(week: int, year: int) -> str:
    return "## Overview" + content.OVERVIEW.format(week=week, year=year)


def fmt_eth(val: float) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M ETH"
    if val >= 1_000:
        return f"{val / 1_000:.0f}K ETH"
    return f"{val:,.0f} ETH"


def render_glance(tvl_data: dict[str, Any]) -> str:
    lines = ["## Yearn at a glance"]

    # Yearn TVL
    if tvl_data["wow_usd_pct"] is not None:
        direction = "increased" if tvl_data["wow_usd_pct"] > 0 else "declined"
        lines.append(
            f"Yearn TVL {direction} week-over-week by **~{abs(tvl_data['wow_usd_pct']):.0f}%**, "
            f"from **{fmt_usd(tvl_data['prev_tvl_usd'])}** (**{tvl_data['prev_tvl_eth']:,.0f} ETH**) "
            f"to **{fmt_usd(tvl_data['tvl_usd'])}** (**{tvl_data['tvl_eth']:,.0f} ETH**)."
        )
    else:
        lines.append(f"Yearn TVL: **{fmt_usd(tvl_data['tvl_usd'])}** (**{tvl_data['tvl_eth']:,.0f} ETH**)")

    # DeFi TVL
    lines.append("")
    defi_wow = tvl_data.get("defi_wow_pct")
    if defi_wow is not None and tvl_data.get("prev_defi_tvl_usd"):
        direction = "increased" if defi_wow > 0 else "declined"
        lines.append(
            f"Total DeFi TVL {direction} week-over-week by **~{abs(defi_wow):.0f}%**, "
            f"from **{fmt_usd(tvl_data['prev_defi_tvl_usd'])}** (**{fmt_eth(tvl_data['prev_defi_tvl_eth'])}**) "
            f"to **{fmt_usd(tvl_data['defi_tvl_usd'])}** (**{fmt_eth(tvl_data['defi_tvl_eth'])}**),"
        )
    else:
        lines.append(
            f"Total DeFi TVL: **{fmt_usd(tvl_data['defi_tvl_usd'])}** (**{fmt_eth(tvl_data['defi_tvl_eth'])}**),"
        )
    lines.append(f"with Yearn's share at **{tvl_data['yearn_share_defi']:.2f}%**.")

    return "\n".join(lines)


def render_vault_list(vaults: list[dict[str, Any]]) -> list[str]:
    lines = []
    for v in vaults:
        url = f"https://yearn.fi/v3/{v['chain_id']}/{v['address']}"
        lines.append(
            f"- [**{v['name']}**]({url}) ({v['chain']}): **{v['apr']:.2f}%** APY | {fmt_usd(v['tvl_usd'])} TVL"
        )
    return lines


def render_vaults(data: dict[str, Any]) -> str:
    lines = ["## Vaults"]

    if content.VAULTS.strip():
        lines.append(content.VAULTS.strip())

    top_usd = data.get("top_usd", [])
    top_crypto = data.get("top_crypto", [])

    if not top_usd and not top_crypto:
        lines.append("Coming soon!")
        return "\n".join(lines)

    if top_usd:
        lines.append("**Top Stablecoin Vaults:**")
        lines.extend(render_vault_list(top_usd))

    if top_crypto:
        lines.append("")
        lines.append("**Top Crypto Vaults:**")
        lines.extend(render_vault_list(top_crypto))

    return "\n".join(lines)


def render_ycrv(data: dict[str, Any]) -> str:
    wow = f"+{data['wow_pct']:.1f}" if data["wow_pct"] > 0 else f"{data['wow_pct']:.1f}"
    text = content.YCRV.format(
        rewards=f"{data['rewards_crvusd']:,.2f}",
        prev_rewards=f"{data['prev_rewards_crvusd']:,.2f}",
        wow=wow,
    )
    return "## yCRV" + text


def render_yyb(data: dict[str, Any]) -> str:
    if data["wow_pct"] is None or data["prev_rewards_crvusd"] is None:
        return f"## yYB\nThis week yYB stakers received **{data['rewards_crvusd']:,.2f} crvUSD** rewards."
    wow = f"+{data['wow_pct']:.1f}" if data["wow_pct"] > 0 else f"{data['wow_pct']:.1f}"
    text = content.YYB.format(
        rewards=f"{data['rewards_crvusd']:,.2f}",
        prev_rewards=f"{data['prev_rewards_crvusd']:,.2f}",
        wow=wow,
    )
    return "## yYB" + text


def render_alpha() -> str:
    return "## Alpha Corner" + content.ALPHA


def render_disclaimer() -> str:
    return "## Disclaimer" + content.DISCLAIMER


def render_sign_off() -> str:
    return content.SIGN_OFF.strip()


def generate() -> None:
    week, year = get_week_and_year()

    tvl_data = tvl.get_data()
    vaults_data = vaults.get_data()
    ycrv_data = ycrv.get_data()
    yyb_data = yyb.get_data()

    sections = [
        render_overview(week, year),
        render_glance(tvl_data),
        render_vaults(vaults_data),
        render_ycrv(ycrv_data),
        render_yyb(yyb_data),
        render_alpha(),
        render_disclaimer(),
        render_sign_off(),
    ]

    output = "\n\n".join(sections)
    OUTPUT_FILE.write_text(output)
    print(f"Newsletter generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate()
