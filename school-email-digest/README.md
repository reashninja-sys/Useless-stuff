# School Email Digest

Part of a general "life automation" project. This one watches for school emails
and sends a single daily summary.

## What it does

A Claude Code Routine runs every day at **5pm UK time** and:

1. Searches Gmail for new mail from the two schools:
   - **Newborough CofE Primary School** (Cora, Year 4) — domain `newborough.pdet.org.uk`
   - **Arthur Mellows Village College / AMVC** (Eric, Year 11) — domain `bromcomcloud.com`
     (their contact domain is `arthurmellows.org`, e.g. `office@arthurmellows.org`)
2. Reads each matching email's full body, and for any **PDF attachment**
   (newsletters, letters — the schools attach most of the real content rather
   than putting it in the email body) extracts the actual text: pulls the raw
   MIME via Gmail, decodes the attachment, and reads it with `pypdf`. Scanned
   (image-only) PDFs fall back to filename-only, since there's no OCR step.
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
- **Gmail label used for tracking:** `School Digest/Processed` (id `Label_6`)
- **Date floor:** the search always adds `after:2026/07/24`, permanently. That
  was the cutoff for the one-time historical backfill below — mail from
  before it is intentionally never pulled into a digest, so ~150 older
  newsletters sitting in the inbox from earlier in the year don't flood the
  first few runs.
- **Dependency bootstrap:** each run starts with a quiet
  `pip install pypdf cffi cryptography`. The container this Routine runs in
  isn't guaranteed to persist installed packages between days, so this is
  idempotent insurance rather than a one-off setup step. If it fails (no
  network), the run still completes — attachments just fall back to
  filename-only for that day, noted once in the digest.
- **"View original email" links:** built from each message's real
  `Message-ID` header as a Gmail `rfc822msgid:` search link
  (`https://mail.google.com/mail/u/0/#search/rfc822msgid%3A...`), not
  Gmail's own `viewUrl`/thread-id link. The `viewUrl` format hung on a
  "workspaces" redirect for this user, almost certainly a multi-Google-account
  conflict (`authuser=` fighting a different signed-in identity in the
  browser, likely a work Workspace account taking priority). The
  `rfc822msgid` format tested better; not yet fully confirmed on a
  reliable connection — ask Claude to adjust again if it turns out to
  misbehave too.

## One-time historical catch-up

Because this had never run before, a backfill covering **24 July – 24
September 2026** (~54 threads) was sent separately as one larger digest,
using the same PDF-extraction pipeline, before the daily Routine above took
over. All of those threads were labeled `School Digest/Processed` afterward,
so the daily Routine starts clean from today.

## Tuning what it includes

The Routine's prompt has an `EXCLUSIONS` list. It starts empty on purpose —
first runs will over-include so you can see everything at least once. When
you notice something you don't want (e.g. "stop telling me about the school
meals provider"), just tell Claude in chat; it updates the Routine's stored
prompt directly (via `update_trigger`), and this README's summary above
should get updated to match if the change is significant enough to affect
the behaviour described here.
