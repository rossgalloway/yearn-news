# Weekly Yearn News Generation

Use this checklist to produce a weekly issue without relying on knowledge from a previous run.

## 1. Choose the reporting window

- Use the Monday of the current report week for the article title.
- Use the start of the last full week as the default lower bound for editorial sources.
- Record a different cutoff in your working notes if the editor requests one.
- Verify publication dates directly; do not rely only on search-result or profile ordering.

The generator derives its title date automatically. Alpha-specific date and authorship rules live in [`tweet-alpha-workflow.md`](tweet-alpha-workflow.md).

## 2. Check local readiness

Install locked dependencies and configure the four RPC variables from `.env.example`:

```bash
uv sync
uv run python src/preflight.py
```

Resolve every required `FAIL` before generating. Optional `WARN` results mean generation may still succeed, but onchain fallback coverage is reduced.

The preflight is read-only. It does not update weekly caches or article files.

## 3. Collect editorial candidates

Check official or primary sources first:

- Yearn-authored and quoted posts from `@yearnfi`
- Yearn governance and forum discussions
- Yearn organization repositories, releases, and merged changes
- Yearn documentation and product surfaces
- Announcements from integration partners, verified against a Yearn-owned or primary technical source

Collect candidate URLs with their publication dates and one sentence explaining why each item matters.

Include items that are:

- Published inside the reporting window
- Authored by Yearn or independently verifiable through a primary source
- Material to users, vault depositors, governance participants, or integrators
- Specific enough to summarize without speculation

Exclude:

- Vanilla retweets
- Low-context replies
- Repeated announcements without a meaningful update
- Rumors, unattributed claims, or items that cannot be dated
- Routine repository activity without user or protocol impact

If Hermes, X access, or public mirrors are unavailable, keep the section conservative and record the limitation in the handoff.

## 4. Edit article content

Edit [`../src/content.py`](../src/content.py):

- `OVERVIEW` is the single introductory sentence.
- `VAULTS` is optional editorial context shown before the generated vault rankings.
- `ALPHA` contains short blurbs followed by raw X URLs.
- `DISCLAIMER` and `SIGN_OFF` contain the closing copy.

Vault rankings, TVL metrics, liquid-locker rewards, dates, and the banner are generated from live data.

Do not manually edit generated files as the source of truth. Regeneration overwrites them.

## 5. Generate once

```bash
uv run python src/generate.py
```

Generation reads live APIs and onchain data, writes all publication formats, and updates `data/tvl_cache.json` for the current week.

The yCRV and yYB week-over-week comparison comes directly from the RewardDistributor contracts. `data/ycrv_cache.json` and `data/yyb_cache.json` are legacy snapshots and are not part of the current generation path.

## 6. Review the article

Check the Markdown and plain-text output:

```bash
rg -n '^## |https://x.com/|APY|Historical APY|TVL|week-over-week' \
  output.md output-x-article.txt
```

Serve the repository:

```bash
python3 -m http.server 4212 --bind 127.0.0.1
```

Review:

- `output-x-article.html`
- `output-yearn-glance-banner-review.html`
- `output-yearn-glance-banner.svg`

Confirm:

- The title and reporting Monday are correct.
- Every editorial item is within the chosen date window.
- Raw X links point to the intended Yearn-authored or quote-tweeted post.
- Vault rows say `APY`, include Historical APY, and link to the correct chain and address.
- TVL and liquid-locker comparisons read naturally when prior data is unavailable or zero.
- The banner is legible at 600×120 and matches the article's top vaults and Yearn TVL.
- The rich-copy button works in a secure browser context.

## 7. Run validation

```bash
uv run ruff format . --check
uv run ruff check .
uv run python -m mypy src tests
uv run python -m unittest discover -s tests -v
```

Do not publish while any command fails.

## 8. Handoff

Provide:

- The working article preview
- The banner preview
- The reporting window and editorial cutoff
- Any unavailable sources or degraded preflight checks
- A note if the current issue has no valid prior-week TVL cache

Do not put private Tailscale URLs in GitHub issues, commits, pull requests, or PR descriptions.
