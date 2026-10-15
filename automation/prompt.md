Generate this week's Yearn News / The Blue Pill draft for editor review.
This is an unattended Thursday run in the existing remote checkout.

Read AGENTS.md, docs/weekly-generation-workflow.md, and docs/tweet-alpha-workflow.md.
Follow their entire research, editorial, generation, and QA workflow. Preflight has
already passed, and the runner has backed up the current content, cache, and output.

Find the immediately prior published newsletter and verify its actual publication
timestamp. Search strictly after it through the current generation time. Record
the prior publication URL, cutoff timestamp, and search end time. Never derive the
cutoff from the title Monday or from the local draft. Inspect the current draft
to avoid repeating covered items. Refresh ALPHA in src/content.py. Preserve the
existing OVERVIEW wording; the generator fills in its reporting-period placeholder.
Include only dated, verified Yearn-authored tweets and quote-tweets. Use the
available Hermes CLI (read its talk-to-hermes skill if using it), web search,
X oEmbed, public mirrors, and primary sources as appropriate. Do not contact people.

If publication cutoff or source coverage cannot be verified, explicitly report
the limitation. Omit unverifiable candidates; do not claim absence of news from
incomplete access. Do not silently reuse stale Alpha text. A conservative draft
may be generated, but identify it as NEEDS EDITOR REVIEW in your final report.
If required live metrics fail, stop and report the failure rather than inventing data.

Use the generator's existing APY, TVL, and closed reward-week rules. Run
uv run python src/generate.py, inspect all output formats, and run the four
validation commands required by AGENTS.md. Make no generator code changes or
dependency changes. Do not commit, push, create a PR, publish to X, or send messages.
Preserve unrelated local changes. Only edit src/content.py, generated output files,
data/tvl_cache.json, and dated editorial source notes under docs/.

The runner serves copies of the generated article and banner through an existing
private Tailscale static route after validation. Do not launch preview servers or
modify Tailscale routes. Do not include private URLs in tracked files or GitHub.
In the final report include the issue week, source window, Alpha links, live data
summary, validation outcomes, and any editorial limitations. This report is saved
to the private review page. Keep it readable without access to this conversation.
