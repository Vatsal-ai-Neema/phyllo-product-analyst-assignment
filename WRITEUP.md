# Meridian Orders API — Findings

## Task 1: Docs vs. data

**1. Pagination signal is self-contradictory (worst issue).** Docs say to check `has_more` and only fetch another page when it's `true`. `orders_page1.json` has `has_more: false` but still ships a non-null `next_cursor`, `cur_8f2a19bd` — and per README, that exact cursor was used to fetch `orders_page2.json`, which contains two more real orders ($79.09). A client written strictly to the documented contract stops after page 1 and silently drops those orders — no error, no way to detect it client-side. This is the worst finding because it's systemic (every list call is exposed, not one bad row) and undermines the core "you got everything" guarantee the API is built on.

**2. 404 promised, 200 delivered.** Docs: `GET /v1/orders/{id}` returns `404` for a missing order. `order_ord_9999.json`, captured from a request for a non-existent order, returns HTTP `200` with `{"order": null}`. Code that checks status codes for "not found" treats this as success and crashes on `response.order.id`.

**3. "Always present" email isn't.** Docs call customer `email` "Always present." `ord_1005.customer.email` is `null`. Breaks any code that skips a null-check because the docs promised it wasn't needed.

**4. Undocumented status value.** Docs list four statuses: `pending, shipped, delivered, cancelled`. `ord_1003.status` is `"refunded"`, not in that list. Any switch/case on documented statuses has no branch for it.

**5. `total` formula breaks on `ord_1004`.** Docs: `total` always equals `subtotal+tax+shipping`. Here `6200+511+599=7310`, but `total=6810` — off by 500. Directly threatens revenue reconciliation.

## Task 2: Total revenue

Judgment calls, stated explicitly:
- **Excluded `ord_1003` (refunded)** — money was returned, so it shouldn't count as revenue. Docs don't actually say how `refunded` orders should be treated; this is an assumption.
- **`ord_1006` is in decimal dollars** (`44.0`), not integer cents like every other order. Normalized to `5362` cents to sum consistently; flagging that this could also be a wider currency-formatting bug, not a one-off.
- Used `ord_1004`'s documented `total` field as-is (6810) rather than the recomputed 7310 — can't tell from the data which one is wrong.
- Combined both pages, since page 2 genuinely exists (Task 1, finding 1) despite `has_more: false`.

**Total: $225.70** (shipped + delivered orders, both pages, refund excluded, `ord_1006` normalized).
If `ord_1004`'s components are ground truth instead of its `total` field: **$230.70**.

Can't fully resolve without knowing: (a) whether refunded orders count toward revenue, (b) which of `ord_1004`'s fields is authoritative, (c) whether `ord_1006` is a one-off entry error or a systemic unit bug.

## Task 3a: Reply to Priya

**Subject:** Re: Revenue reconciliation gap

Hi Priya,

Thanks for flagging this — I think I found the main cause. Our `/orders` endpoint tells clients whether more orders exist via a `has_more` flag. In at least one case, it reported `false` even though a further page of orders existed and was fetchable. If your integration follows our documented logic (stop when `has_more` is false), it silently misses those later orders — no error, just fewer orders than actually exist.

Separately, refunded orders appear in the same list as paid ones with no guidance on whether to include them, which could shift your number too depending on how you're summing.

I've filed both as bugs. Could you tell me roughly how many total orders your report expects for the period? That'll confirm this is the full gap and not a second issue on top of it.

## Task 3b: Bug report

**Title:** `has_more: false` returned while a further page of orders still exists

**Where:** `GET /v1/orders` — `has_more` / `next_cursor` fields

**Steps to reproduce:** Call `GET /v1/orders`. Response has `has_more: false` but a non-null `next_cursor`. Call `GET /v1/orders?starting_after=<that cursor>` — it returns a valid second page with additional real orders.

**Expected:** Per docs, `has_more: false` means no further pages exist, and `next_cursor` should be absent/null.

**Actual:** `has_more` is `false` while `next_cursor` is populated and resolves to real, fetchable data.

**Impact:** Any client following the documented contract terminates pagination early and silently under-counts orders, with no error raised. Matches the symptom in TICKET-4502.

**Suggested next step:** Check whether `has_more` is computed from a stale/cached count while `next_cursor` is generated independently — that split is the likely root cause.
