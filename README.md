# Yearn News

Weekly generator for **The Blue Pill**, covering Yearn protocol metrics, vault yields, liquid-locker rewards, and editorial updates.

## Quick start

Requirements:

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/)
- RPC endpoints for Ethereum mainnet, Arbitrum, Base, and Katana
- Internet access to Kong, Katana reward services, and DeFiLlama

```bash
git clone https://github.com/rossgalloway/yearn-news.git
cd yearn-news
uv sync
cp .env.example .env
```

Fill in `.env`:

```dotenv
RPC_MAINNET="https://..."
RPC_ARBITRUM="https://..."
RPC_BASE="https://..."
RPC_KATANA="https://..."
```

`RPC_MAINNET` is required for liquid-locker rewards. The other RPCs provide complete onchain vault fallback coverage when Kong data is unavailable or incomplete.

## Check readiness

Run the read-only preflight before generating:

```bash
uv run python src/preflight.py
```

It checks required HTTP sources, RPC connectivity, expected chain IDs, and optional fallback services. It does not modify caches or generated output.

## Generate

Follow the complete weekly checklist in [`docs/weekly-generation-workflow.md`](docs/weekly-generation-workflow.md), then run:

```bash
uv run python src/generate.py
```

Generated output:

- `output.md` — Markdown source for archival and editing
- `output-x-article.html` — browser review with rich-text copy support
- `output-x-article-fragment.html` — body-only HTML for paste automation
- `output-x-article.txt` — plain-text fallback
- `output-yearn-glance-banner.svg` — 600×120 Yearn at a Glance banner
- `output-yearn-glance-banner-review.html` — banner review page

Generation updates `data/tvl_cache.json`, which supplies the prior-week TVL comparison. On a fresh clone without a preceding weekly entry, the first article displays current values without a week-over-week comparison.

## Review locally

Serve the repository root:

```bash
python3 -m http.server 4212 --bind 127.0.0.1
```

Then review:

- `http://127.0.0.1:4212/output-x-article.html`
- `http://127.0.0.1:4212/output-yearn-glance-banner-review.html`
- `http://127.0.0.1:4212/output-yearn-glance-banner.svg`

## Validate changes

```bash
uv run ruff format . --check
uv run ruff check .
uv run python -m mypy src tests
uv run python -m unittest discover -s tests -v
```

To apply formatting:

```bash
uv run ruff format .
```

The same checks run in CI.
