import hashlib
import html
import re
from pathlib import Path
from typing import Any

import content
import tvl
import vaults
import ycrv
import yyb
from utils import fmt_usd, format_report_period, get_report_monday, get_week_and_year

OUTPUT_FILE = Path(__file__).parent.parent / "output.md"
X_ARTICLE_HTML_FILE = Path(__file__).parent.parent / "output-x-article.html"
X_ARTICLE_FRAGMENT_FILE = Path(__file__).parent.parent / "output-x-article-fragment.html"
X_ARTICLE_TEXT_FILE = Path(__file__).parent.parent / "output-x-article.txt"
GLANCE_BANNER_SVG_FILE = Path(__file__).parent.parent / "output-yearn-glance-banner.svg"
GLANCE_BANNER_REVIEW_FILE = Path(__file__).parent.parent / "output-yearn-glance-banner-review.html"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
ORDERED_ITEM_RE = re.compile(r"\d+\.\s+(.+)")


def render_overview(period: str, week: int, year: int) -> str:
    overview = content.OVERVIEW.format(period=period, week=week, year=year).strip()
    return overview.splitlines()[0]


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
    for i, v in enumerate(vaults, start=1):
        url = f"https://yearn.fi/v3/{v['chain_id']}/{v['address']}"
        historical_apy = v.get("historical_apy")
        historical_apy_text = f"{historical_apy:.2f}%" if isinstance(historical_apy, (int, float)) else "N/A"
        lines.append(
            f"{i}. [**{v['name']}**]({url}) ({v['chain']})<br>"
            f"    **{v['apr']:.2f}%** APY | **{historical_apy_text}** Historical APY | {fmt_usd(v['tvl_usd'])} TVL"
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


def get_first_vault(data: dict[str, Any], key: str) -> dict[str, Any] | None:
    vaults_for_key = data.get(key, [])
    if not isinstance(vaults_for_key, list):
        return None
    for vault in vaults_for_key:
        if isinstance(vault, dict):
            return vault
    return None


def format_banner_vault(vault: dict[str, Any] | None) -> tuple[str, str]:
    if not vault:
        return "N/A", "Coming soon"
    name = str(vault["name"]).replace(" yVault", "")
    chain = str(vault["chain"]).title()
    return f"{vault['apr']:.2f}%", f"{name} ({chain})"


def render_glance_banner_svg(week: int, year: int, tvl_data: dict[str, Any], vaults_data: dict[str, Any]) -> str:
    stable_apy, stable_label = format_banner_vault(get_first_vault(vaults_data, "top_usd"))
    volatile_apy, volatile_label = format_banner_vault(get_first_vault(vaults_data, "top_crypto"))

    return f"""<svg width="600" height="120" viewBox="0 0 600 120" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="600" height="120" fill="url(#bg)"/>
<line x1="178.25" y1="0" x2="178.25" y2="120" stroke="white" stroke-width="1.5"/>
<text x="20" y="46.5" fill="white" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="800">Yearn TVL</text>
<text x="20" y="81" fill="white" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="800">{html.escape(fmt_usd(tvl_data["tvl_usd"]))}</text>
<text x="195" y="46.5" fill="white" font-family="Inter, Arial, sans-serif" font-size="17">
  <tspan font-weight="800">Top Stable Vault: </tspan><tspan font-weight="800">{html.escape(stable_label)}</tspan><tspan font-weight="800"> | {html.escape(stable_apy)}</tspan>
</text>
<text x="195" y="81" fill="white" font-family="Inter, Arial, sans-serif" font-size="17">
  <tspan font-weight="800">Top Volatile Vault: </tspan><tspan font-weight="800">{html.escape(volatile_label)}</tspan><tspan font-weight="800"> | {html.escape(volatile_apy)}</tspan>
</text>
<defs>
<linearGradient id="bg" x1="0" y1="60" x2="600" y2="60" gradientUnits="userSpaceOnUse">
<stop stop-color="#0675F9"/>
<stop offset="1" stop-color="#0052B4"/>
</linearGradient>
</defs>
</svg>
"""


def render_glance_banner_review_html(svg_cache_key: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Yearn Banner Review</title>
  <style>
    body {{ margin:0; background:#f2f2f2; font-family:Arial, sans-serif; color:#111; overflow-x:auto; }}
    main {{ padding:48px 62px; }}
    h1 {{ font-size:40px; font-style:italic; margin:0 0 18px; }}
    .row {{ display:flex; align-items:center; gap:28px; }}
    .banner {{ width:600px; height:120px; overflow:visible; background:white; outline:1px solid rgba(0,0,0,.08); }}
    .banner img {{ display:block; width:600px; height:120px; }}
    .mark {{ color:#168b2b; font-size:112px; line-height:1; width:120px; text-align:center; }}
    .note {{ margin:0 0 28px 72px; color:#555; font-size:16px; }}
  </style>
</head>
<body>
  <main>
    <h1>generated</h1>
    <p class="note">This page loads the same standalone SVG file shown at output-yearn-glance-banner.svg.</p>
    <div class="row">
      <div class="banner"><img src="output-yearn-glance-banner.svg?v={svg_cache_key}" alt="Generated Yearn at a glance banner"></div>
      <div class="mark">✓</div>
    </div>
  </main>
</body>
</html>
"""


def render_liquid_locker_row(name: str, data: dict[str, Any]) -> str:
    rewards = f"{data['rewards_crvusd']:,.2f}"
    if data.get("wow_pct") is None or data.get("prev_rewards_crvusd") is None:
        return f"**{name}:** This week {name} stakers received **{rewards} crvUSD** rewards"

    wow_pct = data["wow_pct"]
    wow = f"+{wow_pct:.1f}" if wow_pct > 0 else f"{wow_pct:.1f}"
    prev_rewards = f"{data['prev_rewards_crvusd']:,.2f}"
    return (
        f"**{name}:** This week {name} stakers received **{rewards} crvUSD** rewards, compared to "
        f"**{prev_rewards} crvUSD** in the prior week, for a week-over-week change of **{wow}%**"
    )


def render_liquid_lockers(ycrv_data: dict[str, Any], yyb_data: dict[str, Any]) -> str:
    lines = ["## Liquid Lockers"]
    lines.append(render_liquid_locker_row("yCRV", ycrv_data))
    lines.append("")
    lines.append(render_liquid_locker_row("yYB", yyb_data))
    return "\n".join(lines)


def render_alpha() -> str:
    return "## Alpha Corner" + content.ALPHA


def render_disclaimer() -> str:
    return "## Disclaimer" + content.DISCLAIMER


def render_sign_off() -> str:
    return content.SIGN_OFF.strip()


def render_inline_html(text: str) -> str:
    link_tokens: list[tuple[str, str, str]] = []

    def extract_link(match: re.Match[str]) -> str:
        token = f"@@YEARN_NEWS_LINK_{len(link_tokens)}@@"
        link_tokens.append((token, match.group(1), match.group(2)))
        return token

    escaped = html.escape(LINK_RE.sub(extract_link, text), quote=False)
    escaped = escaped.replace("&lt;br&gt;", "<br>")
    escaped = BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = ITALIC_RE.sub(r"<em>\1</em>", escaped)

    for token, label, url in link_tokens:
        escaped = escaped.replace(
            token,
            f'<a href="{html.escape(url, quote=True)}">{render_inline_html(label)}</a>',
        )
    return escaped


def render_inline_text(text: str) -> str:
    text = text.replace("<br>", "\n")
    text = LINK_RE.sub(r"\1 (\2)", text)
    text = BOLD_RE.sub(r"\1", text)
    return ITALIC_RE.sub(r"\1", text)


def markdown_blocks(markdown: str) -> list[tuple[str, str | list[str]]]:
    blocks: list[tuple[str, str | list[str]]] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph)))
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items:
            blocks.append((list_kind or "unordered_list", list_items.copy()))
            list_items.clear()
            list_kind = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        if line == "---":
            flush_paragraph()
            flush_list()
            blocks.append(("hr", ""))
            continue
        if line.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(("subheading", line[4:].strip()))
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(("heading", line[3:].strip()))
            continue
        if line.startswith("- "):
            flush_paragraph()
            if list_kind != "unordered_list":
                flush_list()
                list_kind = "unordered_list"
            list_items.append(line[2:].strip())
            continue
        ordered_match = ORDERED_ITEM_RE.match(line)
        if ordered_match:
            flush_paragraph()
            if list_kind != "ordered_list":
                flush_list()
                list_kind = "ordered_list"
            list_items.append(ordered_match.group(1).strip())
            continue

        flush_list()
        paragraph.append(line)

    flush_paragraph()
    flush_list()
    return blocks


def render_x_article_fragment(markdown: str, glance_banner_url: str | None = None) -> str:
    lines: list[str] = []
    for kind, value in markdown_blocks(markdown):
        if kind == "heading":
            heading = str(value)
            lines.append(f"<h2>{render_inline_html(heading)}</h2>")
            if heading == "Yearn at a glance" and glance_banner_url:
                lines.append(
                    '<figure class="glance-banner">'
                    f'<img src="{html.escape(glance_banner_url, quote=True)}" alt="Yearn at a glance banner">'
                    "</figure>"
                )
        elif kind == "subheading":
            lines.append(f"<h3>{render_inline_html(str(value))}</h3>")
        elif kind == "paragraph":
            lines.append(f"<p>{render_inline_html(str(value))}</p>")
        elif kind == "unordered_list":
            items = value if isinstance(value, list) else []
            lines.append("<ul>")
            lines.extend(f"<li>{render_inline_html(item)}</li>" for item in items)
            lines.append("</ul>")
        elif kind == "ordered_list":
            items = value if isinstance(value, list) else []
            lines.append("<ol>")
            lines.extend(f"<li>{render_inline_html(item)}</li>" for item in items)
            lines.append("</ol>")
        elif kind == "hr":
            lines.append("<hr>")
    return "\n".join(lines)


def render_x_article_text(markdown: str) -> str:
    lines: list[str] = []
    for kind, value in markdown_blocks(markdown):
        if kind == "heading":
            lines.append(render_inline_text(str(value)))
            lines.append("")
        elif kind == "subheading":
            lines.append(render_inline_text(str(value)))
            lines.append("")
        elif kind == "paragraph":
            lines.append(render_inline_text(str(value)))
            lines.append("")
        elif kind == "unordered_list":
            items = value if isinstance(value, list) else []
            lines.extend(f"- {render_inline_text(item)}" for item in items)
            lines.append("")
        elif kind == "ordered_list":
            items = value if isinstance(value, list) else []
            lines.extend(f"{i}. {render_inline_text(item)}" for i, item in enumerate(items, start=1))
            lines.append("")
        elif kind == "hr":
            lines.append("")

    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def render_x_article_html(title: str, article_fragment: str, article_text: str) -> str:
    escaped_title = html.escape(title, quote=False)
    escaped_text = html.escape(article_text)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    :root {{ color-scheme: light; --fg:#111; --muted:#525252; --border:#d4d4d4; --bg:#fff; --soft:#f5f5f5; --link:#1d4ed8; }}
    body {{ margin:0; color:var(--fg); background:var(--bg); font:17px/1.58 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width:820px; margin:0 auto; padding:32px 20px 64px; }}
    header {{ border-bottom:1px solid var(--border); margin-bottom:28px; padding-bottom:20px; }}
    h1 {{ font-size:2rem; line-height:1.12; margin:0 0 14px; letter-spacing:0; }}
    .actions {{ align-items:center; display:flex; flex-wrap:wrap; gap:10px; }}
    button {{ background:#111; border:1px solid #111; color:#fff; cursor:pointer; font:600 0.95rem/1 ui-sans-serif, system-ui; padding:10px 14px; }}
    .hint {{ color:var(--muted); font-size:0.92rem; margin:0; }}
    article {{ word-wrap:break-word; }}
    article h2 {{ font-size:1.45rem; line-height:1.22; margin:34px 0 12px; letter-spacing:0; }}
    article h3 {{ font-size:1.08rem; line-height:1.3; margin:22px 0 6px; letter-spacing:0; }}
    article p {{ margin:0 0 16px; }}
    article .glance-banner {{ margin:0 0 18px; }}
    article .glance-banner img {{ display:block; height:auto; max-width:100%; }}
    article ul {{ margin:0 0 18px 1.3rem; padding:0; }}
    article li {{ margin:0 0 8px; }}
    article a {{ color:var(--link); text-decoration:underline; }}
    article hr {{ border:0; border-top:1px solid var(--border); margin:32px 0; }}
    details {{ border-top:1px solid var(--border); margin-top:36px; padding-top:18px; }}
    summary {{ cursor:pointer; font-weight:700; }}
    pre {{ background:var(--soft); overflow:auto; padding:16px; white-space:pre-wrap; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{escaped_title}</h1>
      <div class="actions">
        <button id="copy-rich" type="button">Copy rich article body</button>
        <p class="hint">Pastes as rich text into X Articles. Use the title above separately.</p>
      </div>
    </header>
    <article id="article-body">
{article_fragment}
    </article>
    <details>
      <summary>Plain text fallback</summary>
      <pre>{escaped_text}</pre>
    </details>
  </main>
  <script>
    const button = document.querySelector("#copy-rich");
    const article = document.querySelector("#article-body");
    button.addEventListener("click", async () => {{
      const htmlBlob = new Blob([article.innerHTML], {{ type: "text/html" }});
      const textBlob = new Blob([article.innerText], {{ type: "text/plain" }});
      await navigator.clipboard.write([new ClipboardItem({{ "text/html": htmlBlob, "text/plain": textBlob }})]);
      button.textContent = "Copied";
      window.setTimeout(() => {{ button.textContent = "Copy rich article body"; }}, 1400);
    }});
  </script>
</body>
</html>
"""


def generate() -> None:
    week, year = get_week_and_year()
    period = format_report_period(get_report_monday())

    tvl_data = tvl.get_data()
    vaults_data = vaults.get_data()
    ycrv_data = ycrv.get_data()
    yyb_data = yyb.get_data()

    sections = [
        render_overview(period, week, year),
        render_glance(tvl_data),
        render_vaults(vaults_data),
        render_liquid_lockers(ycrv_data, yyb_data),
        render_alpha(),
        render_disclaimer(),
        render_sign_off(),
    ]

    output = "\n\n".join(sections)
    title = f"The Blue Pill - {period}"
    glance_banner_svg = render_glance_banner_svg(week, year, tvl_data, vaults_data)
    svg_cache_key = hashlib.sha256(glance_banner_svg.encode()).hexdigest()[:12]
    glance_banner_url = f"output-yearn-glance-banner.svg?v={svg_cache_key}"

    x_article_fragment = render_x_article_fragment(output, glance_banner_url=glance_banner_url)
    x_article_text = render_x_article_text(output)
    x_article_html = render_x_article_html(title, x_article_fragment, x_article_text)

    GLANCE_BANNER_SVG_FILE.write_text(glance_banner_svg)
    GLANCE_BANNER_REVIEW_FILE.write_text(render_glance_banner_review_html(svg_cache_key))
    OUTPUT_FILE.write_text(output)
    X_ARTICLE_FRAGMENT_FILE.write_text(x_article_fragment)
    X_ARTICLE_TEXT_FILE.write_text(x_article_text)
    X_ARTICLE_HTML_FILE.write_text(x_article_html)
    print(f"Newsletter generated: {OUTPUT_FILE}")
    print(f"X Article HTML generated: {X_ARTICLE_HTML_FILE}")
    print(f"Glance banner SVG generated: {GLANCE_BANNER_SVG_FILE}")
    print(f"Glance banner review generated: {GLANCE_BANNER_REVIEW_FILE}")


if __name__ == "__main__":
    generate()
