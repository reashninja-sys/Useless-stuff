# School Email Digest

Part of a general "life automation" project. This one watches for school emails
and sends a single daily summary.

## What it does

A Claude Code Routine runs every day at **5pm UK time** and:

1. Searches Gmail for new mail from the two schools:
   - **Newborough CofE Primary School** (Cora, Year 4) — domain `newborough.pdet.org.uk`
   - **Arthur Mellows Village College / AMVC** (Eric, Year 11) — domain `bromcomcloud.com`
     (their contact address is `office@arthurmellows.org`)
2. Reads each matching email's full body and lists any attachment filenames.
3. Writes one summary email, grouped into:
   - **Needs your attention** — mentions of Cora, Year 4, Eric, Year 11, GCSEs,
     parents' evening, deadlines, forms/consent slips, payments due, or anything
     the school flags as urgent
   - Newborough — Cora (Year 4)
   - AMVC — Eric (Year 11)
   - General / whole-school FYI
4. Sends it to **reashninja@gmail.com**.
5. Labels every included email `School Digest/Processed` in Gmail so it's never
   summarized twice — this also means a missed day just rolls forward into the
   next digest instead of losing anything.

## Where it actually lives

The logic isn't code in this repo — it's the prompt stored on the Routine
itself (Claude Code Routines / CCRs), because that's what actually runs it
daily. This README is the human-readable record of what that Routine does.

- **Routine ID:** `trig_012m9fpC9dFfyCtFXttAQ4X9`
- **Schedule:** `0 16 * * *` (UTC) — currently 5pm during British Summer Time.
  UK clocks go back on the last Sunday of October, at which point this needs
  updating to `0 17 * * *` to keep firing at 5pm local time. Just ask Claude
  to fix it when that rolls around.
- **Bound to:** this Claude Code session (not a fresh session per run), because
  this org's Routines can't hand Gmail connector access to a freshly spawned
  session — only a session that already holds the connector keeps it.
- **Gmail label used for tracking:** `School Digest/Processed`

## Known limitation

The Gmail tools available to the Routine can see attachment **filenames** but
not their content — there's no PDF/document reader wired in. So newsletters
and letters that are pure attachments (no body text) get listed by filename
with a link to the original email, not actually summarized. Worth knowing
before assuming the digest caught everything inside a PDF.

## Tuning what it includes

The Routine's prompt has an `EXCLUSIONS` list. It starts empty on purpose —
first runs will over-include so you can see everything at least once. When
you notice something you don't want (e.g. "stop telling me about the school
meals provider"), just tell Claude in chat; it updates the Routine's stored
prompt directly (via `update_trigger`), and this README's summary above
should get updated to match if the change is significant enough to affect
the behaviour described here.
