# Yearn News Generator

Weekly newsletter generator for "The Blue Pill" - Yearn ecosystem updates.

## Running

Preferred local run:

```bash
uv run python src/generate.py
```

Historical container run from the old Claude setup:

```bash
docker exec objective_robinson bash -c "cd /projects && uv run python src/generate.py"
```

## Architecture

- `src/generate.py` - Main generator, renders all sections to Markdown
- `src/content.py` - Editable text content for each section
- `src/tvl.py` - TVL data from DefiLlama API
- `src/vaults.py` - Vault discovery and yield sourcing
- `src/ycrv.py` - yCRV rewards from RewardDistributor
- `src/yyb.py` - yYB data
- `src/utils.py` - Shared helpers (web3, multicall, caching, formatting)
- `src/abis/` - Contract ABIs
- `tests/` - Regression tests for vault sourcing behavior

## Key contracts and data sources

- Registries: `0xd40ecF29e001c76Dcc4cC0D9cd50520CE845B038`, `0xff31A1B020c868F6eA3f61Eb953344920EeCA3af`
- APR Oracle: `0x1981AD9F44F2EA9aDd2dC4AD7D075c102C70aF92`
- RewardDistributor (yCRV): `0xB226c52EB411326CdB54824a88aBaFDAAfF16D3d`
- yvcrvUSD-2 vault: `0xBF319dDC2Edc1Eb6FDf9910E39b37Be221C8805F`
- Kong vault list API: `https://kong.yearn.fi/api/rest/list/vaults`
- Katana reward service used by fallback path: `https://katana-apr.yearn.fi/api/vaults`
- DeFiLlama: `https://api.llama.fi/`

## Current vault sourcing rules

- Newsletter vault rows should use Kong as the primary source.
- Kong APY for output should prefer `performance.estimated.apy` when present, then fall back to `performance.oracle.netAPY`.
- For Katana vaults without `performance.estimated.apy`, add reward components on top of the oracle-derived base.
- Show Kong `performance.historical.monthlyNet` as the separate Historical APY value, falling back to `performance.historical.net` only when monthly net is missing.
- For Katana vault Historical APY, add reward components on top of the Kong historical base, mirroring the estimated APY fallback behavior.
- Do not use Kong top-level `apy.net` or `performance.historical` for sorting or the primary vault row APY display.
- If Kong is unavailable or a vault is missing usable Kong APY/TVL data, fall back to the direct query path in `src/vaults.py`.
- Vault row text in the generated article should say `APY`, not `APR`.

## Filtering expectations

Keep the newsletter vault list scoped to:

- `v3 == true`
- `isHighlighted == true`, except the yvUSD and Locked yvUSD addresses are explicitly allowed
- `kind == "Multi Strategy"`
- `origin == "yearn"`
- names matching the current editorial scope in `src/vaults.py`

## Caching

Data is cached in `data/` with week/year tracking for WoW comparisons:

- `tvl_cache.json`
- `ycrv_cache.json`
- `yyb_cache.json`

## Output

Generates:

- `output.md` - Markdown source for archival/editing
- `output-x-article.html` - rich-text browser view with a copy button for X Articles
- `output-x-article-fragment.html` - body-only HTML for paste automation
- `output-x-article.txt` - Markdown-free plain text fallback
- `output-yearn-glance-banner.svg` - 600x120 Yearn at a Glance banner for X Articles
- `output-yearn-glance-banner-review.html` - browser review page for the generated banner

## Alpha Corner workflow

Use `docs/tweet-alpha-workflow.md` when refreshing Alpha Corner.

Current expectations:

- Use the start of the last full week as the lower bound unless the user gives a different date.
- Include Yearn-authored tweets and quote-tweets only.
- Exclude vanilla retweets, low-context replies, and posts older than the cutoff.
- Prefer short punchy blurbs plus raw X links.
- If Hermes, `xurl`, or public mirrors are unavailable, keep Alpha conservative and note the limitation.

## Preview workflow

At the end of a turn that changes generated output or docs, provide a working preview link when one is available.

This repo can be served as static files from the repo root, for example:

```bash
python3 -m http.server 4212 --bind 127.0.0.1
```

Then verify and share the relevant local or private preview URLs for the files being reviewed, usually:

- `output-x-article.html`
- `output-yearn-glance-banner.svg`
- `output-yearn-glance-banner-review.html`

## Development workflow

Before finishing changes:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m mypy src tests
uv run ruff check .
```

Use Python 3.12 and keep the implementation simple and explicit.
