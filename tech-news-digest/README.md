# Tech & AI News Digest

Part of the general "life automation" project (see `../school-email-digest/`
for the sibling routine and the shared setup notes). This one is a curated
daily briefing for work, not an inbox digest — there's no inbox to trawl,
it goes and finds the news itself.

## What it does

A Claude Code Routine runs every **weekday at 7am UK time** and:

1. Runs a set of web searches across four areas tuned to the owner's role
   (Principal Tech Director / enterprise architect, CTO department, large UK
   public sector engineering organisation):
   - Cloud (AWS / Azure / GCP / public-sector cloud)
   - AI generally
   - AI-assisted software development (coding agents, LLM engineering, dev tooling)
   - Enterprise architecture & UK public sector digital transformation
2. Verifies anything that looks significant by fetching the actual source
   article — never links or summarizes from a search snippet alone.
3. **Curates rather than includes everything** — this is the opposite
   instinct from the school digest. News is unbounded, so the routine
   selects roughly 8-15 of the best, most substantive stories a day rather
   than reporting everything it finds. Content-farm listicles, pure opinion
   pieces, marketing fluff, and anything not genuinely relevant to the role
   get left out.
4. Sends one email, grouped into: Cloud / AI & AI-Assisted Software
   Development / Enterprise Architecture & Public Sector Tech / Also worth a
   glance. Each story: headline linked to the real source, publication name,
   what happened, and *why it specifically matters to this role* — not
   generic filler.
5. Sends it to **reashninja@gmail.com**.

No Gmail label bookkeeping here (unlike the school digest) — there's no
inbox being tracked, so nothing to mark as processed. Overlap day-to-day is
naturally limited by only covering roughly the last 24-48 hours.

## Where it actually lives

Same pattern as the school digest: the logic is the prompt stored on the
Routine, not code in this repo. This README is the human-readable record.

- **Routine ID:** `trig_01N9MbtSJDCqQGWkSfxuZfj3`
- **Schedule:** `0 6 * * 1-5` (UTC, Mon-Fri) — currently 7am during British
  Summer Time. Needs updating to `0 7 * * 1-5` once UK clocks go back
  (last Sunday of October) to keep firing at 7am local time — same caveat
  as the school digest, and worth fixing both at the same time.
- **Bound to:** this Claude Code session, for the same reason as the school
  digest — this org can't hand connector (Gmail, web search) access to a
  freshly spawned session, only a session that already holds it keeps it.
- **Weekdays only** — deliberately skips weekends, since this is a work
  briefing.

## Tuning what it includes

Same mechanism as the school digest: the Routine's prompt has an
EXCLUSIONS/STEERING list, empty to start. Tell Claude things like "stop
including pure funding-round news" or "I want more on Kubernetes/platform
engineering" and it updates the Routine's stored prompt directly.
