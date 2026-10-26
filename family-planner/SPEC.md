# Family Planner: Product Spec

Status: **Draft v0.2** (answers folded in; prototype M0 live as a shared Claude artifact, see `prototype/`)
Owners: Reash and Kathy

---

## 0. Household facts (confirmed v0.2)

**Phones:** both Android.

**Calendar today:** a shared Google Calendar owned by Kathy (`chaoticgloom@gmail.com`)
holds custody and family events. Reash's account has read-only access. The app
reads it for now and should eventually replace it.

**Children**

| Child | Age | School | Year | Parent |
|-------|-----|--------|------|--------|
| Cora | 9 | Newborough CofE Primary | Y4 | Reash |
| Oli | 10 | Northborough Primary | Y6 | Kathy |
| Poppy | 13 | Arthur Mellows Village College (AMVC) | Y8 | Kathy |
| Leo | 15 | AMVC | Y11 | Kathy |
| Eric | 15 | AMVC | Y11 | Reash |

**Custody patterns (nights with us)**

- **Oli, Poppy, Leo:** 2-2-3 on a 14-day cycle. Anchored to Mon 26 Oct 2026
  (cycle day 0): with us on days 0, 1 (Mon, Tue), 4, 5, 6 (Fri to Sun), 9, 10
  (Wed, Thu of the second week). Matches the "Kathy kids" entries in the shared
  calendar.
- **Eric:** Monday and Friday nights; goes home Saturday 5:30pm.
- **Cora:** Thursday and Friday nights; goes home Saturday 5:30pm.
- Half-terms and holidays are handled as exceptions (the calendar already
  shows entries such as "R kids half term (5.30 pick up)").
- **Handovers:** Oli, Poppy and Leo always change over at school. Reash drops
  Eric and Cora back at 5:30pm on Saturdays.

**Diet:** Poppy is pescatarian (fish, no meat). The family still has meat when
she's home: usually a veggie version of the same meal for her, sometimes fish
for everyone. No regular weekly meals.

**Accounts and Claude access:** Kathy has a free Claude account. An artifact
owner can invite someone by email as an editor (Pro/Max feature), and that
person can change the shared data. But for anyone invited from outside the
owner's own account, parts of an artifact that use Claude or connectors don't
work, even on a paid plan. So in the artifact, only Reash gets typed
messages, meal ingredients and the school scan; Kathy uses forms. This is the
main reason to move to Option B later.

**Main calendar:** this app becomes the main calendar. No writing back to
Google Calendar; the shared calendar is shown read-only during the switchover.

**School email routing:** the artifact's school scan reads the Gmail
connected to Reash's Claude account (reashninja@gmail.com, the same inbox as
reashninja@googlemail.com). Newborough and AMVC already arrive there.
Northborough is parked for now; when revisited, Kathy forwards it to that inbox.
Longer term (Option B), route all school mail to one shared inbox
(`chaoticgloom@gmail.com` or a dedicated forwarding address).

**Sharing:** strictly the two of us. No co-parent or kids' views.

**School comms:** mostly direct email. Observed senders:
`office@newborough.pdet.org.uk` (Newborough), Bromcom (`bromcomcloud.com`,
AMVC), with bookings via Arbor. Reash already has a "School Digest" Gmail
automation, which the app should eventually replace.

**Shopping:** Tesco online for the weekly shop; Aldi in person for top-ups.
The shopping list is split into those two lists, and Tesco's list can be
copied in a format suited to Tesco's multi-search.

**Hosting decision:** start with Option A (shared Claude artifact) as the
working app, not just a throwaway prototype.

---

## 1. Purpose

A shared family organiser for two parents running a household where different
children are with us on different days. It should remove the mental load of
"who's here, what's on, what do they need, what are we eating" by:

- holding one shared calendar that understands the custody split,
- letting either of us add things in plain English (typed or spoken),
- pulling important dates and actions out of school emails automatically,
- turning a weekly meal plan into a shopping list.

### Design principles

1. **Capture in under 5 seconds.** If adding something is slower than
   remembering it, we won't use it.
2. **Suggest, don't silently act.** Anything the app infers (from email or
   voice) lands as a proposal one tap away from confirmed.
3. **Who's home drives everything.** The custody schedule feeds the calendar,
   the meal headcount, packing reminders and the daily summary.
4. **Works with what we already use.** Sync with Google Calendar rather than
   asking everyone to abandon it.

---

## 2. Users

| User | Role | Device |
|------|------|--------|
| Reash | Parent, full admin | Android phone (TBC) |
| Kathy | Parent, full admin | TBC (Android or iPhone?) |
| Children | Possibly read-only view later | TBC |
| Co-parents (ex-partners) | Possibly limited shared view later | n/a |

---

## 3. Core features (MVP)

### 3.1 Shared calendar

- Day / week / month views. Week view is the default (it matches how custody
  and meal plans work).
- Each event has: title, date/time or all-day, which child(ren) it involves,
  who is responsible (Reash / Kathy / either / other parent), location, notes,
  optional reminder, optional checklist ("bring PE kit, £2 for cake sale").
- Colour coding per child; a strip at the top of each day showing which
  children are with us.
- Recurring events (swimming every Tuesday, term-time only).
- School term dates and INSET days as a separate layer that recurring events
  can respect ("term-time only").
- **Two-way sync with Google Calendar** (one shared "Family" calendar), so
  events also appear in our normal calendar apps and on watches.

### 3.2 Natural language + voice capture

- A single always-visible input: type or hold the mic button.
- Examples it must handle:
  - "Ella has a dentist appointment next Thursday at 3:30, Kathy's taking her"
  - "Swimming for Sam every Tuesday 5pm in term time"
  - "Swap weekends with Mark so we have the kids 14th to 16th Nov"
  - "Add eggs and bin bags to the shopping list"
  - "Spag bol on Wednesday"
  - "What's on this weekend?" (a question, answered rather than added)
- Parsing is done by an LLM (Claude) with tool/function calling into the
  app's own actions (create event, add list item, set meal, change custody,
  query).
- Result is shown as a confirmation card ("Dentist, Ella, Thu 30 Oct 15:30,
  Kathy"), with **Save / Edit / Cancel**. High-confidence simple items (e.g.
  shopping list additions) can save immediately with an Undo toast.
- Voice: on-device speech-to-text (Android SpeechRecognizer / Web Speech API)
  for speed and privacy; transcript then goes through the same parser.
- Stretch: Android home-screen widget and "Hey Google, tell Family Planner..."
  shortcut; share-sheet target (share a screenshot/text/email into the app).

### 3.3 Custody / family split

- Model each child separately, because different children can be on
  different patterns.
- **Base pattern** per child, chosen from templates or custom:
  - alternate weeks
  - alternate weekends (+ midweek night)
  - 2-2-3, 2-2-5-5, 3-4-4-3
  - fixed weekdays (e.g. every Mon/Wed + alternate weekends)
  - fully custom N-day repeating cycle
- **Handover details**: time, place, who drops/collects.
- **Exceptions layer** on top of the base pattern: swaps, holidays, half-term
  splits, Christmas/birthday arrangements. Exceptions are added via NL too.
- **Views**: "Who's here" for any day; month overview grid (child x day);
  count of nights per child per month/year (useful if arrangements are
  reviewed).
- Handover reminders, with an optional "send back to the other house"
  checklist (school jumper, inhaler, reading book).

### 3.4 School email scanning

- Watch for emails from configured senders/domains (each school, clubs,
  ParentMail-style services).
- For each email, extract with an LLM:
  - events and dates (non-uniform day, parents' evening, trip)
  - deadlines and actions (return form by Fri, pay £12 on ParentPay)
  - things to bring (costume, packed lunch, wellies)
  - which child it relates to (by school / class / name)
- Results land in an **Inbox / "To review"** queue: each suggestion links to
  the source email and can be accepted (creates event/task), edited or
  dismissed.
- Weekly digest: "This week from school: 3 events, 2 forms, 1 payment".
- Privacy: only matching emails are read; nothing else in the mailbox is
  processed or stored. Store the extracted items plus a link, not full email
  bodies.
- Technical options (see section 6): Gmail API with a read-only scope and a
  sender filter, **or** a Gmail filter that auto-forwards school emails to a
  dedicated app inbox (simpler, more private, works for any email provider).

### 3.5 Meal planning + shopping list

- Weekly grid (Mon to Sun, dinner by default; optional breakfast/lunch/packed
  lunch rows).
- Headcount per meal **auto-filled from the custody schedule** (and adjustable
  for guests / someone out).
- Recipe library: title, ingredients with quantities, servings, tags (quick,
  veggie, kid-approved), link/photo. Import a recipe from a URL or a photo of
  a cookbook page via the LLM.
- "Plan my week" assistant: suggests meals based on favourites, what's
  quick on busy days (calendar-aware: swimming night = 20 min meal), and
  dietary needs.
- Shopping list:
  - generated from the week's meals, scaled to headcount, merged and
    de-duplicated ("2 onions + 1 onion = 3 onions")
  - plus manual items and recurring staples (milk, bread)
  - "already have it" tick-off before shopping, pantry staples remembered
  - grouped by supermarket aisle/category
  - shared and live-updating so one of us can shop while the other adds
  - ticked items stay visible (greyed) until the list is cleared

---

## 4. Additional feature ideas (post-MVP backlog)

Ranked roughly by value-for-effort.

1. **Morning briefing** push notification: "Today: Sam with us, PE kit,
   swimming 5pm (Kathy). Dinner: fajitas. Ella handover 6pm at Mark's."
2. **Kit / packing reminders** derived from recurring events (PE on Tue, swim
   bag Thu, library book Fri) shown the night before.
3. **Pickup / drop-off rota**: who is doing each run, with a nudge if nobody
   is assigned.
4. **Birthdays and parties**: kids' friends' parties from invites, with a
   "buy present" task a week before, and a gift-idea list per child.
5. **Shared to-do lists**: household jobs, admin (renew passport, book
   dentist), with due dates and an owner.
6. **Co-parent sharing**: a limited, read-only link for each ex-partner
   showing only their child's school events and handover plan. Reduces
   "did you see the email about...?" messages.
7. **Kids' info hub**: clothing/shoe sizes, GP/dentist, allergies, school
   login details location, passport expiry, club membership numbers.
8. **Chores and pocket money** tracker for the kids, with a kid-friendly view.
9. **Shared expenses** between parents (and optionally with co-parents):
   school trips, uniform, clubs; running balance.
10. **Leftovers and batch cooking**: mark a meal as "makes 2 nights" or
    "freeze half", track what's in the freezer.
11. **Online grocery hand-off**: export the list in an order that's quick to
    enter on the supermarket site/app (true basket integration is unlikely,
    UK supermarkets don't offer public APIs).
12. **Kitchen display mode**: a big-screen week view for an old tablet on the
    fridge.
13. **Garmin glance widget**: today's who's-here and next event on the watch
    (reuses what we built for the Cupra battery widget).
14. **Holiday planner**: school holidays highlighted, custody split for the
    holiday, packing list templates.
15. **Homework / reading log** and parents' evening notes per child.

---

## 5. Data model (first pass)

```
Household     id, name, timezone (Europe/London)
Member        id, household_id, name, role (parent|child|coparent), colour,
              school_id?, dob?
School        id, name, sender_domains[], term_dates[]
CustodyPlan   id, child_id, pattern_type, cycle_start, cycle_days[],
              handover_time, handover_place
CustodyException id, child_id, date_from, date_to, with_us (bool), note
Event         id, title, start, end, all_day, recurrence_rule, term_time_only,
              child_ids[], responsible_id, location, notes, checklist[],
              source (manual|voice|email|gcal), source_ref, gcal_id
Suggestion    id, source_email_ref, extracted_json, status
              (pending|accepted|dismissed), created_event_id?
Recipe        id, title, servings, ingredients[{name, qty, unit, category}],
              tags[], url, photo
MealPlanEntry id, date, slot (breakfast|lunch|dinner|packed_lunch),
              recipe_id? | free_text, headcount
ShoppingItem  id, name, qty, unit, category, checked, source
              (meal|manual|staple), added_by
```

---

## 6. Hosting and platform options

### Option A: Shared Claude Artifact (fastest prototype)

A single web page hosted on claude.ai, shared between us, using the artifact
shared database for calendar/meal/shopping data and the microphone capability
for voice.

- **Pros:** can be built in an afternoon; no servers, no app store; shared
  live state; Claude is right there for natural-language parsing.
- **Cons:** no background jobs, so email scanning can't run on its own
  schedule; no push notifications; opens in a browser rather than as a
  proper app; no Google Calendar sync; tied to claude.ai accounts.
- **Best for:** validating the UX (does NL capture + custody view actually get
  used?) before investing in a real build.

**As built (M0):** the artifact uses a shared database for events, meals,
shopping, custody exceptions and email suggestions; Claude (on the viewer's
own account) to read messages and school emails; the viewer's Google Calendar
connector to show the shared calendar; and the viewer's Gmail connector for an
on-demand "Check now" school scan. Voice works through the Android keyboard's
mic. Claude usage per message is small (one quick request); a school scan is
one larger request.

### Option B: Progressive Web App + managed backend (recommended)

A web app that installs to the home screen on both Android and iPhone, backed
by a hosted database such as **Supabase** or **Firebase**.

- Frontend: React/Svelte PWA, offline cache, home-screen icon.
- Backend: Supabase (Postgres + auth + realtime + scheduled edge functions)
  or Firebase (Firestore + Cloud Functions + FCM).
- Claude API for NL parsing, email extraction, recipe import.
- Scheduled function every 15 to 30 minutes to process school emails and send
  the morning briefing.
- **Pros:** works on any phone, one codebase, realtime sync between us, push
  notifications (Android fully; iPhone supported once installed to home
  screen), free tier likely covers a family, easy to iterate.
- **Cons:** no home-screen widget; voice relies on the browser's speech API
  (fine on Chrome/Android, patchier on iOS Safari).
- **Running cost estimate:** hosting £0 (free tiers); Claude API a few pounds
  a month at family volumes.

### Option C: Native Android app (Kotlin + Jetpack Compose)

- **Pros:** best voice experience, home-screen widgets, Google Assistant
  shortcuts, share-sheet integration, rock-solid notifications, can talk to
  the Garmin watch directly.
- **Cons:** Android only (a problem if Kathy has an iPhone); still needs a
  backend for shared data and email scanning; slower to build and change;
  sideload APK or a Play Store developer account (one-off $25).

### Option D: Cross-platform native (Flutter or React Native/Expo)

- Same benefits as C but one codebase for Android and iPhone.
- iPhone distribution needs an Apple Developer account (~£79/year) or
  TestFlight.
- A sensible step up from B if we outgrow the PWA.

### Option E: Self-hosted

Run the backend on a home machine (Raspberry Pi, NAS, or the Termux setup
already in this repo) with the PWA as frontend.

- **Pros:** data never leaves home; no vendor accounts.
- **Cons:** we become the ops team (backups, uptime, remote access via
  Tailscale/Cloudflare Tunnel); email scanning and notifications still need
  internet-facing pieces.

### Recommendation

1. **Week 1:** Option A prototype as a shared artifact to prove the core
   loop (NL capture, custody view, meal plan to list).
2. **Then:** build Option B (PWA + Supabase + Claude API + Google Calendar
   sync + email forwarding inbox) as the real app.
3. **Later, if needed:** wrap in Flutter/Capacitor for widgets and better
   voice.

### Email ingestion approach (applies to B to E)

| Approach | How | Notes |
|----------|-----|-------|
| Forwarding inbox (recommended) | Gmail filter forwards school senders to e.g. `school@family.ourdomain` (Cloudflare Email Workers, Postmark or Mailgun inbound) which POSTs to the backend | Only school mail ever leaves the mailbox; works for both our accounts and any provider; no Google app verification |
| Gmail API | OAuth with `gmail.readonly`, query by sender, poll on a schedule | Reads directly, but the restricted scope needs Google verification for a public app, and personal "testing" mode apps have refresh tokens that expire every 7 days |

---

### How Claude features are billed in Option B

The web app's server calls the Claude API with an API key from an Anthropic
Console account. It is pay-as-you-go (prepaid credits, with a monthly spend
limit you set), billed per token, and separate from any Claude Pro/Max
subscription. Neither of us needs a Claude account to use the app; the key
never reaches the phones.

Per-token prices (October 2026, per million tokens, input / output):
Claude Haiku 5.5 $0.10 / $0.50; Claude Sonnet 5.5 $2 / $10; Claude Opus 5.5
$4 / $20.

Rough estimate for our use: a typed message is about 3,000 tokens in and 300
out (Haiku: well under 0.1p; Sonnet: about 1p). A daily school-email check is
about 12,000 in and 1,000 out on Sonnet (about 3p). Twenty messages a day on
Haiku plus a daily Sonnet email check comes to roughly £1 to £2 a month.

## 7. Architecture sketch (Option B)

```
 Phones (PWA)  <--realtime-->  Supabase (Postgres, Auth, Realtime)
     |                               ^      ^
     | NL text / voice transcript    |      | scheduled functions
     v                               |      |
 Edge function "parse" --Claude API--+      +-- "ingest-email" <-- inbound email webhook
                                     |      +-- "morning-briefing" --> push notifications
                                     +--------- "gcal-sync" <--> Google Calendar
```

---

## 8. Non-functional requirements

- **Speed:** capture to confirmation card in under 2 seconds for typed input.
- **Sync:** changes visible on the other phone within 2 seconds.
- **Offline:** view calendar and shopping list offline; queue edits.
- **Privacy:** data limited to our household; school email bodies not
  retained beyond extraction; LLM calls send only the minimum text needed.
- **Security:** Google sign-in for both of us; row-level security per
  household; co-parent links are scoped, revocable and read-only.
- **Backups:** daily database backup; export to ICS/CSV.
- **Locale:** UK dates (DD/MM), Europe/London timezone, metric quantities,
  UK school terminology (INSET, half-term, non-uniform day).

---

## 9. Open questions

### Still open after v0.2

1. Import future events from the shared Google Calendar into the app once,
   then stop showing the calendar overlay?
2. Which inbox should Reash's Claude Gmail connector read: keep
   `reashninja@googlemail.com` (Kathy forwards to it) or switch it to the shared
   `chaoticgloom@gmail.com`?
3. When should we start Option B, given Kathy can't use the Claude features in
   the artifact?

### Original v0.1 questions (answered in section 0)

**Phones and accounts**
1. What phones do you and Kathy have? (If either is an iPhone, that rules out
   Android-only.)
2. Do you both use Gmail / Google Calendar today? Is there already a shared
   family calendar?

**Children and custody**
3. How many children, roughly what ages, and how many different schools?
4. What are the patterns? e.g. "child A alternate weeks with handover Monday
   after school, child B every Wed + alternate weekends".
5. How often do swaps/exceptions happen, and how are holidays split?
6. Would you want any view shared with the other parents, or strictly
   private to the two of you?
7. Should the kids have their own view (older ones especially)?

**School emails**
8. Which email address(es) do the schools write to: yours, Kathy's, both?
9. Do schools also use apps (ParentMail, Arbor, Class Dojo, ParentPay,
   Seesaw, Tapestry)? Some of those only notify by email, some only in-app.
10. Are you comfortable with the forwarding-inbox approach, or would you
    prefer direct Gmail access?

**Meals and shopping**
11. Which supermarket(s), and online delivery or in-person?
12. Any dietary needs, fussy eaters, or meals tied to custody days (e.g.
    pizza Friday when everyone's home)?
13. Do you already have a stash of recipes somewhere (Paprika, website
    bookmarks, cookbooks)?

**Build and budget**
14. Are you happy to start with the Claude Artifact prototype, then move to
    the PWA?
15. Running cost comfort level (likely £0 to £10/month)?
16. Do you want to build it yourself with help, or have me build it with you
    reviewing?

---

## 10. Milestones (draft)

| # | Milestone | Contents |
|---|-----------|----------|
| M0 | Prototype (**live**) | Artifact: week view, custody strip, NL add, meal grid, Tesco/Aldi lists, on-demand school email scan, shared calendar overlay |
| M1 | Real app foundation | PWA, auth for both of us, Supabase schema, calendar CRUD, realtime sync |
| M2 | Capture | NL parser with Claude tool calling, voice input, confirmation cards |
| M3 | Custody | Patterns, exceptions, who's-here views, handover reminders |
| M4 | Meals | Recipes, weekly plan with auto headcount, shopping list generation |
| M5 | School email | Forwarding inbox, extraction, review queue, weekly digest |
| M6 | Integrations | Google Calendar two-way sync, morning briefing push |
| M7 | Backlog | Items from section 4, by priority |
