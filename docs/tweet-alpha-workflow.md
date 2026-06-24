# Collecting X Posts For Alpha Corner

This document records the current manual process for finding Yearn X posts and adding them to the newsletter generator. It is intentionally not a skill yet. Treat it as the operating checklist for future runs.

## Goal

The Alpha Corner should include recent Yearn-authored tweets and quote-tweets that are useful for newsletter readers. Keep it tight: a short blurb, then the full X link. The linked post should do most of the telling.

## Date Window

Use the start of the last full week as the lower bound unless the user gives a different date.

For example, during the May 22, 2026 run, the cutoff was May 11, 2026. Posts before that date were excluded even if they appeared in a mirror or old search result.

Always verify the post date. Do not trust profile page order alone.

## What Counts

Include:

- Full tweets from `@yearnfi`
- Quote-tweets from `@yearnfi`

Exclude:

- Vanilla retweets
- Replies that are not useful standalone newsletter items
- Posts from other accounts that merely appear because Yearn retweeted them
- Anything older than the cutoff

The important distinction is authorship. If a mirror shows `yearn retweeted`, that is not an Alpha item unless Yearn also made its own quote-tweet with commentary.

## Preferred Collection Flow

1. Ask Hermes to pull Yearn tweets and quote-tweets for the target window.
2. If Hermes cannot access X directly, record that limitation and fall back to public sources.
3. Check the Yearn profile mirror, such as `https://twstalker.com/yearnfi`, for recent visible posts.
4. Use X oEmbed for individual post verification when possible:

   ```bash
   curl -Ls --compressed -A 'Mozilla/5.0' \
     'https://publish.twitter.com/oembed?url=https://x.com/yearnfi/status/<status_id>'
   ```

5. Decode the X snowflake timestamp for each candidate status ID and compare it to the cutoff.

   ```bash
   uv run python - <<'PY'
   from datetime import datetime, timezone

   ids = [
       2054909725054239152,
   ]
   epoch = 1288834974657

   for value in ids:
       ts = ((value >> 22) + epoch) / 1000
       print(value, datetime.fromtimestamp(ts, timezone.utc).isoformat())
   PY
   ```

6. Inspect the mirror context around each candidate. Look for signs that the item is a retweet:

   ```bash
   curl -Ls --compressed -A 'Mozilla/5.0' 'https://twstalker.com/yearnfi?lang=en' -o /tmp/yearnfi.html
   rg -n 'yearn retweeted|status/<status_id>|<known text>' /tmp/yearnfi.html
   ```

7. Keep only posts that satisfy the date and authorship rules.

## Writing The Alpha Copy

Edit `src/content.py`, inside `ALPHA`.

Use this shape:

```markdown
ALPHA = """
Short punchy blurb.<br>https://x.com/yearnfi/status/<status_id>

Another short punchy blurb.<br>https://x.com/yearnfi/status/<status_id>
"""
```

Do not add a label like `From X since May 11`. The `Alpha Corner` heading is enough.

Do not rank the posts with ordered lists. Use simple paragraphs.

Do not start blurbs with `Yearn <action>` unless it is truly the cleanest sentence. It is already obvious that the section is about Yearn. Prefer direct, action-first copy:

- `Yearn avoids upgradeable proxies. Here's why.`
- `Flex is live!`
- `yvUSD crossed $10M TVL.`
- `Enso powers smoother cross-asset and cross-chain vault UX.`

The blurb should be short and useful, not a summary of the whole post.

## Current Example

The May 22, 2026 run used these Alpha items:

```markdown
Enso powers smoother cross-asset and cross-chain vault UX.<br>https://x.com/yearnfi/status/2057844782483882301

Yearn avoids upgradeable proxies. Here's why.<br>https://x.com/yearnfi/status/2057084200327737456

Flex is live!<br>https://x.com/yearnfi/status/2056737704251904373

yvUSD crossed $10M TVL.<br>https://x.com/yearnfi/status/2054909725054239152
```

Known excluded examples from that run:

- `https://x.com/yearnfi/status/2057814644572471406` was not a Yearn-authored post; it appeared through a retweet of another account.
- `https://x.com/yearnfi/status/2056414269839675484` was a Liquity post that appeared through a Yearn retweet.

## Regenerate And Verify

After editing `src/content.py`, regenerate:

```bash
uv run python src/generate.py
```

Check that the Alpha section looks right in all generated formats:

```bash
rg -n -C 1 'Alpha Corner|<status_id>|<blurb text>' \
  output.md output-x-article.html output-x-article-fragment.html output-x-article.txt
```

Before finishing a code/content change, run:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m mypy src tests
uv run ruff check .
```

Then provide the X article preview link when a local or private preview is available.
