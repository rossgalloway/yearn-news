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
- Do not use Kong top-level `apy.net` or `performance.historical` for the vault row APY display.
- If Kong is unavailable or a vault is missing usable Kong APY/TVL data, fall back to the direct query path in `src/vaults.py`.
- Vault row text in the generated article should say `APY`, not `APR`.

## Filtering expectations

Keep the newsletter vault list scoped to:

- `v3 == true`
- `kind == "Multi Strategy"`
- `origin == "yearn"`
- names matching the current editorial scope in `src/vaults.py`

## Caching

Data is cached in `data/` with week/year tracking for WoW comparisons:

- `tvl_cache.json`
- `ycrv_cache.json`
- `yyb_cache.json`

## Output

Generates `output.md` in Markdown format for copy-paste to the publication platform.

## Development workflow

Before finishing changes:

```bash
python -m unittest discover -s tests -v
python -m mypy src tests
ruff check .
```

Use Python 3.12 and keep the implementation simple and explicit.
