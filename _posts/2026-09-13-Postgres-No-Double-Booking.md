---
layout: post
title: "PostgreSQL - Making Double Bookings Impossible"
image: /images/postgres/02-no-double-booking/01-check-then-insert-race.webp
series: "PostgreSQL"
categories: ["Databases", "PostgreSQL"]
tags: [postgres, concurrency, exclusion-constraints, range-types, data-modelling]
published: true
---

Every hotel reservation system starts with the same line of code:

```sql
SELECT 1 FROM reservation
WHERE room_id = $1 AND check_out > $2 AND check_in < $3;
-- no rows? great, book it
```

And every one of them eventually double-books a room.

The fix is not a better check. The fix is to stop checking. PostgreSQL can make an overlapping booking **impossible to store**, so the `INSERT` itself becomes the check, performed atomically, with no read-modify-write window for two sessions to slip through.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5 and DeepSeek V4.1 Flash) based on conversations exploring PostgreSQL concurrency, exclusion constraints and range-type semantics. All content has been reviewed, edited, and verified by a human author against the official PostgreSQL documentation.
{: .prompt-info }

This post walks through the whole thing: why the naive version is broken, how exclusion constraints work internally, the range-type semantics that trip people up, how to model the columns, and when a different mechanism is the right answer.

## Why check-then-insert is broken

Under `READ COMMITTED` (PostgreSQL's default isolation level) every statement takes its own snapshot, and neither session can see the other's uncommitted row. Two people booking the same room for overlapping dates at the same moment both see an empty result set, and both proceed.

![Two sessions racing through a check-then-insert window](/images/postgres/02-no-double-booking/01-check-then-insert-race.webp)
_Neither session did anything wrong. The check was simply answered before the other write existed._

The window is small, which is exactly what makes it dangerous: it survives code review, it survives staging, and it shows up in production at 200 requests per second on a bank holiday.

> If the isolation-level mechanics behind that diagram are unfamiliar, the earlier post on [PostgreSQL isolation levels](/Postgres-Isolation-Model/) covers snapshots and MVCC (multi-version concurrency control) in detail. Everything below assumes the default `READ COMMITTED`.
{: .prompt-tip }

## Model the stay as a range, not two columns

A `UNIQUE` constraint cannot help here. Two bookings conflict when their date *intervals* intersect, and intersection is not an equality test.

PostgreSQL has a first-class type for intervals (`daterange`) and an intersection operator, `&&`.

Use half-open bounds, written `[)`: check-in inclusive, check-out exclusive. That is exactly hotel semantics: the guest checking out on the 15th does not block the guest checking in on the 15th.

![Half-open date ranges over a calendar of nights](/images/postgres/02-no-double-booking/02-half-open-nights.webp)
_A booking owns nights, not days. Two stays that merely touch at a boundary share nothing._

`Mar 10 → Mar 12` ends exactly where the booking starts, and `Mar 15 → Mar 18` starts exactly where it ends. Neither shares a night, so neither conflicts. Getting this wrong in either direction produces a system that either double-books or refuses perfectly valid same-day turnovers.

## The schema

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;   -- lets GiST index scalar = on room_id

CREATE TABLE reservation (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_id     bigint      NOT NULL REFERENCES room(id),
    guest_id    bigint      NOT NULL,
    stay        daterange   NOT NULL,
    status      text        NOT NULL DEFAULT 'confirmed',
    created_at  timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT status_valid   CHECK (status IN ('held','confirmed','cancelled')),
    CONSTRAINT stay_not_empty CHECK (NOT isempty(stay)),

    CONSTRAINT reservation_no_overlap
        EXCLUDE USING gist (room_id WITH =, stay WITH &&)
        WHERE (status <> 'cancelled')
);
```

### Reading the EXCLUDE clause

An `EXCLUDE` constraint is the generalisation of `UNIQUE`. Where `UNIQUE (x)` says "no two rows may have the same value", `EXCLUDE` says "no two rows may satisfy **all** of these comparisons at once".

![Anatomy of the EXCLUDE clause, line by line](/images/postgres/02-no-double-booking/03-exclude-anatomy.webp)
_The comma between the two tests is an AND, and the whole conjunction is what gets forbidden._

Concretely, for a candidate row and an existing row in room 101:

```
violation  <=>  new.room_id = old.room_id  AND  new.stay && old.stay
```

If either test returns false (different room, or disjoint dates) the pair is fine and the insert proceeds.

### Three details that matter

**`btree_gist` is required.** GiST (generalised search tree) is the index method that understands the `&&` overlap operator, but on its own it has no idea how to index a `bigint` with `=`. An exclusion constraint builds *one* index covering both columns, so both operators must live in the same access method. Drop the extension and `CREATE TABLE` fails with *data type bigint has no default operator class for access method "gist"*.

**`WHERE (status <> 'cancelled')` makes it a partial index.** Cancelling is `UPDATE ... SET status='cancelled'`, and the dates free up the instant that commits: no delete, no lost history. The predicate must be `IMMUTABLE`, so you cannot write `WHERE expires_at > now()`.

**`isempty` closes a real hole.** That one gets its own section below, because it is where most hand-rolled implementations quietly fail.

Writing a booking is now a single statement with no read-modify-write at all:

```sql
INSERT INTO reservation (room_id, guest_id, stay)
VALUES ($1, $2, daterange($3::date, $4::date, '[)'))
RETURNING id;
```

## Why this is safe at READ COMMITTED

This is the part worth internalising, and it is the reason the whole approach works without raising the isolation level.

The short version is that the constraint check does **not** use your MVCC snapshot. That statement invites an obvious objection, though, and the objection is worth taking seriously: *an index is just another structure on disk describing the same rows, so how can reading it give a different answer from reading the table?*

The answer is that it does not, because an index cannot give an answer about visibility at all.

### An index has no idea what a transaction is

Heap tuples and index tuples do not carry the same metadata, and the difference is not a detail.

![The heap tuple header carries xmin and xmax; the index tuple carries neither](/images/postgres/02-no-double-booking/05-heap-vs-index-tuple.webp)
_23 bytes of bookkeeping against 8. The missing 15 are the entire reason this post works._

A heap tuple header keeps `t_xmin` and `t_xmax`: the transaction that created this row version and the one that deleted it. That pair *is* MVCC. An index tuple is a `t_tid` pointing at a heap tuple plus a `t_info` holding flags and a length, and that is the whole structure. No transaction id, no command id, nothing.

So an index entry cannot tell you whether it is visible to you, whether its transaction committed, or even whether it is dead. It tells you *where to look*. You have almost certainly met the consequences already: index-only scans need the visibility map precisely because the index alone cannot prove a row is visible, and dead index entries linger until `VACUUM` because nothing in them records that they died.

> The index is not "dirty". It has no opinion on visibility whatsoever, which is exactly why an opinion has to be supplied from outside, and why a *different* opinion can be supplied.
{: .prompt-tip }

### The same scan, a different snapshot

Because the index holds no visibility data, every index scan in PostgreSQL is two steps: walk the index to collect candidate TIDs, then fetch each heap tuple and apply a visibility rule to it. The index access method never sees the rule. It is an argument, handed in at the top:

```c
index_beginscan(heap, index, snapshot, ...);
```

Your availability query passes its MVCC snapshot. The exclusion constraint calls `InitDirtySnapshot` and passes `SnapshotDirty`. Same index, same entries, same code path: only the third argument differs.

![The same index scan under two different snapshots](/images/postgres/02-no-double-booking/04-snapshot-vs-index.webp)
_Both sides find A's index entry. Only the visibility rule applied to the heap tuple behind it differs._

An index entry is written the moment the inserting backend writes it, long before that transaction commits, which is what makes the conflict *detectable* at all. Under an MVCC snapshot the heap tuple behind it is invisible, because its `xmin` belongs to a transaction still in progress, so the row drops out of your result set. Under `SnapshotDirty`, in-progress is exactly the case you want to catch, so it counts.

### It never acts on uncommitted data

Reading an uncommitted row sounds like a dirty read, and PostgreSQL does not permit those at any isolation level. The escape is that the constraint does not *decide* anything on that basis.

`SnapshotDirty` is also an output parameter. When it matches a tuple whose inserting transaction is still running, it writes that transaction id back into the snapshot struct, and the constraint check reads it straight back out to work out whom to block on:

```c
xwait = TransactionIdIsValid(DirtySnapshot.xmin)
        ? DirtySnapshot.xmin : DirtySnapshot.xmax;
...
XactLockTableWait(xwait, heap, &ctid_wait, XLTW_RecheckExclusionConstr);
goto retry;
```

Session B does not spin and does not poll: it sleeps on A's transaction ID lock, and on waking it restarts the scan from scratch. So the uncommitted read is used for exactly one thing: identifying who to wait for. The verdict always comes from committed state. If A committed, the conflict is real and B gets `23P01`; if A rolled back, the retry finds nothing and B succeeds.

> **You already rely on this.** `UNIQUE` follows the same protocol (ignore MVCC visibility, wait on the conflicting transaction, then decide), and nobody finds it surprising that two concurrent inserts of the same primary key cannot both succeed at `READ COMMITTED`. An exclusion constraint is that protocol with `&&` in place of `=`.
{: .prompt-tip }

One last inversion, because it explains the retry. The heap tuple and its index entries are written *before* the conflict scan runs: the check is genuinely insert-then-check, which is why the scan has to recognise and skip its own entry by TID. PostgreSQL performs the read-modify-write you were trying to write by hand; it just holds the right locks while doing it.

> **The cost of that design is an occasional deadlock.** If two backends insert conflicting rows at almost the same instant, each can write its index entry, then scan, then find the other's in-progress tuple and wait on it. The deadlock detector breaks the cycle, so one session gets `40P01` instead of `23P01`. This is acknowledged in the `execIndexing.c` source comment as harmless (one of them was going to fail anyway), but it does mean a booking endpoint should treat `40P01` as retryable rather than as a 500.
{: .prompt-warning }

## Turning the conflict into your error

The SQLSTATE (the five-character error code PostgreSQL returns) is `23P01` (`exclusion_violation`), and the constraint name comes back in the error, so you can distinguish "room taken" from any other constraint failure. Map it to HTTP 409.

Go, with pgx v5:

```go
_, err := tx.Exec(ctx, insertReservation, roomID, guestID, checkIn, checkOut)

var pgErr *pgconn.PgError
if errors.As(err, &pgErr) &&
    pgErr.Code == pgerrcode.ExclusionViolation &&
    pgErr.ConstraintName == "reservation_no_overlap" {
    return ErrRoomUnavailable   // -> 409 Conflict
}
```

> Always match on the constraint *name*, not just the SQLSTATE. The moment you add a second exclusion constraint (a cleaning buffer, a maintenance blackout), a bare `23P01` check starts reporting the wrong thing to the user.
{: .prompt-warning }

Or keep it in the database:

```sql
CREATE FUNCTION book_room(p_room bigint, p_guest bigint, p_in date, p_out date)
RETURNS bigint LANGUAGE plpgsql AS $$
DECLARE v_id bigint;
BEGIN
    INSERT INTO reservation (room_id, guest_id, stay)
    VALUES (p_room, p_guest, daterange(p_in, p_out, '[)'))
    RETURNING id INTO v_id;
    RETURN v_id;
EXCEPTION WHEN exclusion_violation THEN
    RAISE EXCEPTION 'room % is not available from % to %', p_room, p_in, p_out
        USING ERRCODE = '23P01';
END $$;
```

The `EXCEPTION` block opens a subtransaction on every call. Fine at booking volumes, bad inside a tight loop over thousands of rows.

If you would rather branch on a row count than catch an exception:

```sql
INSERT INTO reservation (room_id, guest_id, stay)
VALUES ($1, $2, daterange($3, $4, '[)'))
ON CONFLICT DO NOTHING
RETURNING id;
```

Zero rows returned means unavailable. `ON CONFLICT DO NOTHING` works with exclusion constraints; `ON CONFLICT ... DO UPDATE` does not: that requires a unique index as the arbiter. The tradeoff is that a bare `DO NOTHING` also swallows primary-key and idempotency-key conflicts, so you lose the ability to tell *why* nothing was inserted.

### The availability query is for the UI, not for correctness

```sql
SELECT r.id, r.number
FROM room r
WHERE r.hotel_id = $1
  AND NOT EXISTS (
      SELECT 1 FROM reservation b
      WHERE b.room_id = r.id
        AND b.status <> 'cancelled'
        AND b.stay && daterange($2::date, $3::date, '[)')
  );
```

Treat this as advisory. It powers the search page; the constraint is the authority. The `&&` predicate is index-assisted by the same GiST index the constraint created, so you get the query for free.

## The part everyone gets wrong: empty ranges

### Where `empty` lives

`empty` is not a keyword, a sentinel, or something your schema declares. Every range value is a varlena with a trailing flags byte, and one bit in that byte means "this range is empty". When it is set, no bound values are stored at all.

![The in-memory layout of a range value and its flags byte](/images/postgres/02-no-double-booking/06-range-value-layout.webp)
_`isempty()` is not a computation. It is a single bit test, and every range operator performs it first._

That is why `lower('empty'::daterange)` returns `NULL`: there is nothing there to return. The text form `'empty'` is just the input/output representation of the bit, so `'empty'::daterange` and `'empty'::tstzrange` both parse.

`isempty` is a built-in polymorphic function:

```sql
\df isempty
--  Name    | Result  | Argument
--  isempty | boolean | anyrange
```

One definition covers `daterange`, `tstzrange`, `int4range`, `numrange`, and any custom range type.

> `isempty` is strict, so `isempty(NULL)` is `NULL`, and a `CHECK` that evaluates to `NULL` **passes**. The `stay daterange NOT NULL` on the column is what closes that door. This pattern recurs: every `NULL`-producing expression in a `CHECK` is a hole.
{: .prompt-warning }

### Why it breaks the constraint

Every range operator checks that bit *before* touching any bounds. The overlap operator's rule is: **if either range is empty, return false.**

So a zero-night booking sails straight past the exclusion constraint: `&&` short-circuits and never compares dates at all.

| Expression | Result | Why |
|---|---|---|
| `isempty('empty'::daterange)` | `true` | the bit is set |
| `'empty' && anything` | `false` | overlaps nothing |
| `'empty' && 'empty'` | `false` | not even itself |
| `anything @> 'empty'` | **`true`** | every range contains the empty set |
| `'empty' @> anything` | `false` | contains nothing |
| `'empty' = 'empty'` | `true` | equal to itself |
| <code>'empty' -&#124;- anything</code> | `false` | not adjacent to anything |
| `lower('empty')`, `upper('empty')` | `NULL` | no bounds stored |

The `@>` row is the one that bites people writing availability logic by hand: `booked @> requested` returns true for an empty request, which reads as "yes, already covered".

> **Without the `isempty` guard, ghost rows accumulate without limit.** Every pair of empty rows evaluates `empty && empty` to false, so the constraint never fires. They are invisible to every availability query, and `lower(stay)` and `upper(stay)` read back `NULL`, which breaks every report, invoice and housekeeping list that touches them. There is no natural upper bound on how many you can accumulate.
{: .prompt-danger }

## Equal check-in and check-out dates

What happens when someone submits the same date twice? Nothing is ever silently discarded: PostgreSQL either transforms the value, raises an error, or inserts the row. Which of those you get depends entirely on the bound token.

![The four bound tokens, and what happens when both dates are equal](/images/postgres/02-no-double-booking/07-bounds-and-empty.webp)
_Because `date` is a discrete type, PostgreSQL canonicalises everything to `[)` on input. Your `'[]'` does not survive; it gets rewritten._

Two takeaways, and they are the whole reason this section exists.

> **The `'[]'` branch is a semantics bug, not a constraint bug.** Someone submitting the same date twice almost certainly means "zero nights" and instead gets a confirmed one-night booking that blocks the 12th for everyone else. PostgreSQL did nothing wrong; the bounds token said the day was included.
{: .prompt-warning }

**The two guards are not interchangeable.** Once a value reaches a `daterange` column, `daterange('2026-03-12','2026-03-12','[]')` and `daterange('2026-03-12','2026-03-13','[)')` are byte-identical. The information about what the caller typed is destroyed by canonicalisation, so no column-level check can recover it. `isempty` catches three of the four cases; only `check_out > check_in` on the raw scalars catches all four.

That is a strong argument for hardcoding the bounds token in the DDL and guarding on raw scalar columns, which brings us to column modelling.

## Modelling the columns: three shapes

The real question is: which columns are the source of truth, and which are derived?

![Three ways to model the stay, and where the range physically lives](/images/postgres/02-no-double-booking/08-column-shapes.webp)
_The shapes differ mainly in **where the range lives**: the heap, or only the index._

### Option 1: range only

```sql
stay daterange NOT NULL,
CONSTRAINT stay_not_empty CHECK (NOT isempty(stay)),
```

The dates are still there, just wrapped:

```sql
SELECT lower(stay) AS check_in, upper(stay) AS check_out FROM reservation;
```

Because `[)` canonicalisation guarantees an exclusive upper bound, `upper(stay)` *is* the check-out date exactly, with no off-by-one. For an arrivals index, use an expression index: `CREATE INDEX ON reservation (lower(stay))`.

The friction is at the edges: range types do not map cleanly through JDBC, GORM, ActiveRecord, or most BI tools without a custom type handler, and CSV exports come out as `[2026-03-12,2026-03-15)`.

### Option 2: two date columns, generated range

```sql
check_in  date NOT NULL,
check_out date NOT NULL,
stay      daterange GENERATED ALWAYS AS
          (daterange(check_in, check_out, '[)')) STORED,

CONSTRAINT stay_positive CHECK (check_out > check_in),
CONSTRAINT reservation_no_overlap
    EXCLUDE USING gist (room_id WITH =, stay WITH &&)
    WHERE (status <> 'cancelled')
```

`GENERATED ALWAYS AS (expr) STORED` (PG 12+) computes the column on every insert and update and physically stores it. You cannot write to it:

```sql
INSERT INTO reservation (..., stay) VALUES (..., daterange(...));
-- ERROR: cannot insert a non-DEFAULT value into column "stay"
```

That refusal is the entire value proposition: the two dates are the only writable truth, and `stay` cannot disagree with them.

> **The `STORED` keyword is not optional, and its meaning changed in PG 18.** On PG 12-17 the grammar required it and omitting it was rejected outright. On PG 18, `VIRTUAL` became the default when neither keyword is written, and virtual generated columns cannot be indexed, so `EXCLUDE ... (stay WITH &&)` will simply refuse to be created. DDL that used to fail loudly now changes your storage model quietly. Write `STORED` explicitly.
{: .prompt-danger }

Two more constraints to know: the expression must be `IMMUTABLE` and may only reference columns of the same row, and adding a stored generated column to an existing table rewrites the whole table, so plan the migration window.

> **One sharp edge.** Stored generated columns are computed *before* check constraints are evaluated. If `check_out < check_in`, the `daterange()` constructor blows up first with a raw `22000` data exception, and your carefully named `stay_positive` check never produces the friendly `23514`. Equal dates are fine: they produce `empty`, and the check catches it.
{: .prompt-warning }

### Option 3: two date columns, expression in the constraint

You do not need a third column at all. Exclusion constraints accept expressions, exactly like `CREATE INDEX`:

```sql
CONSTRAINT reservation_no_overlap
    EXCLUDE USING gist (
        room_id WITH =,
        daterange(check_in, check_out, '[)') WITH &&
    ) WHERE (status <> 'cancelled')
```

The computed range lives only inside the GiST index. No extra bytes in the heap, nothing to keep in sync, and the table is two plain `date` columns that every tool understands.

It also fixes the sharp edge above. With no generated column, PostgreSQL runs your `CHECK (check_out > check_in)` *before* index tuples are built, so an inverted booking fails with a clean `23514` and never reaches the range constructor.

The cost: `SELECT stay` does not exist, and your availability query must repeat the expression verbatim or the planner will not match the index. Wrap it in a view if that bothers you; views are inlined, so the index still matches:

```sql
CREATE VIEW reservation_v AS
SELECT r.*, daterange(check_in, check_out, '[)') AS stay FROM reservation r;
```

### The shape to avoid

Writing all three columns from application code. Nothing in the database stops it, and nothing detects the drift.

![One row with two disagreeing truths and no constraint that compares them](/images/postgres/02-no-double-booking/09-dual-write-drift.webp)
_Both constraints are satisfied. Both readers are correct. The row is still wrong._

> **This is the worst failure mode in the post**, because it produces no error at any point and no query will surface it. Every other bug here announces itself with a SQLSTATE; this one just quietly bills the wrong guest.
{: .prompt-danger }

If you are stuck with a legacy dual-write table, at least bolt on the missing invariant:

```sql
ALTER TABLE reservation ADD CONSTRAINT stay_matches_dates
    CHECK (stay = daterange(check_in, check_out, '[)'));
```

At which point you have reimplemented a generated column the hard way.

### Which to pick

| | Option 1 (range only) | Option 2 (dates + generated) | Option 3 (dates only) |
|---|---|---|---|
| Source of truth | `stay` | the two dates | the two dates |
| Drift possible | no | no (write refused) | no |
| Heap cost | range only | dates + range | dates only |
| ORM (object-relational mapper) / BI friendliness | poor | good | good |
| `SELECT stay` works | yes | yes | via a view |
| Inverted dates error | `22000` | `22000`, bypasses your check | `23514`, clean |
| Arrivals index | expression index | plain btree | plain btree |

> My default is **option 3**. The API almost always arrives carrying two dates, so make those the stored truth and keep the derived range where it is actually needed: inside the index.
{: .prompt-tip }

### Where each error is raised

The `22000` versus `23514` distinction in that table is not arbitrary. It falls directly out of the order PostgreSQL does things on the way in.

![The INSERT path, with the SQLSTATE raised at each stage](/images/postgres/02-no-double-booking/10-insert-error-pipeline.webp)
_A `CHECK` always runs before the index is touched, which is exactly why option 3 gets the clean error and option 2 does not._

### Why the scalar columns earn their place

Mostly indexes. A GiST range index is excellent at "does anything overlap this window" and poor at "whose lower bound equals today". Different access patterns, different indexes:

```
  is room 101 free Mar 12-15?  ----->  gist (room_id, stay)   [free with the constraint]
  who checks in today?         ----->  btree (check_in)
  who checks out today?        ----->  btree (check_out)
```

## Hourly bookings: `tstzrange`

Meeting rooms, spa slots, day-use rooms. `isempty` is `anyrange`, so the call is identical:

```sql
CONSTRAINT slot_not_empty CHECK (NOT isempty(slot))   -- slot tstzrange
```

What changes is *when* a value becomes empty, because `tstzrange` is **continuous** and has no canonical function. Values are stored exactly as written.

| Input (`t` = one instant) | `daterange` analogue | `tstzrange` result | `isempty` |
|---|---|---|---|
| `(t, t, '[)')` | empty | `empty` | true |
| `(t, t, '(]')` | empty | `empty` | true |
| `(t, t, '()')` | empty | `empty` | true |
| `(t, t, '[]')` | one day | `["t","t"]` | **false** |
| `(t, t+1µs, '()')` | empty | `("t","t+1µs")` | **false** |

> **`tstzrange(t, t, '[]')` is a zero-duration slot that `isempty` happily accepts**, and it overlaps any booking containing `t`. A "0-minute meeting" can block a real one, and the guard you copied from the `daterange` schema will not catch it.
{: .prompt-warning }

The fix is to stop relying on `isempty` alone. Watch the trap: `upper(slot) > lower(slot)` is `NULL` for an empty range, and a `NULL` `CHECK` passes. You need both conjuncts:

```sql
CONSTRAINT slot_positive CHECK (
    NOT isempty(slot)
    AND upper(slot) > lower(slot)
)
```

Or enforce a real minimum duration, which subsumes both:

```sql
CHECK (NOT isempty(slot) AND upper(slot) - lower(slot) >= interval '15 minutes')
```

If unbounded slots are possible in your API, add `NOT lower_inf(slot) AND NOT upper_inf(slot)`. `NOT NULL` on the column does not stop `[t,)`, and one such row blocks the room forever.

Everything else transfers unchanged: `btree_gist`, the `EXCLUDE USING gist` syntax, the partial `WHERE`, and the `23P01` error code. The GiST `range_ops` operator class covers all range types.

## When the exclusion constraint is the wrong tool

Real hotel property-management systems often sell a *room type* with N physical rooms, not a specific room. Then the invariant is a count per night, not a non-overlap, and an exclusion constraint cannot express it.

![Choosing between declarative constraints and explicit locks](/images/postgres/02-no-double-booking/11-mechanism-decision.webp)
_Only the top two are declarative. The bottom two are correct only if every code path cooperates._

### Inventory counter

```sql
CREATE TABLE room_inventory (
    hotel_id     bigint NOT NULL,
    room_type_id bigint NOT NULL,
    stay_date    date   NOT NULL,
    total_rooms  int    NOT NULL,
    booked_rooms int    NOT NULL DEFAULT 0,
    PRIMARY KEY (hotel_id, room_type_id, stay_date),
    CONSTRAINT not_oversold CHECK (booked_rooms BETWEEN 0 AND total_rooms)
);

UPDATE room_inventory
SET booked_rooms = booked_rooms + 1
WHERE hotel_id = $1 AND room_type_id = $2
  AND stay_date >= $3 AND stay_date < $4
  AND booked_rooms < total_rooms;
-- if affected rows <> (check_out - check_in) -> ROLLBACK, sold out
```

This is safe at `READ COMMITTED` for a subtle reason. When two sessions target the same row, the second blocks on the row lock, and on waking PostgreSQL re-evaluates the `WHERE` against the *new* row version rather than the stale snapshot: the EvalPlanQual mechanism. The `CHECK` is your backstop if anyone ever writes the update without the `booked_rooms < total_rooms` guard.

### Row lock on the room

```sql
BEGIN;
SELECT 1 FROM room WHERE id = $1 FOR UPDATE;   -- serialize all bookers for this room
-- arbitrary validation: minimum stay, blackout dates, rate rules
INSERT INTO reservation ...;
COMMIT;
```

Correct, but only if *every* code path takes the lock. Keep the exclusion constraint underneath as a safety net: a declarative guarantee costs nothing and does not depend on the discipline of the next person to touch the codebase.

### Advisory lock

```sql
SELECT pg_advisory_xact_lock(hashtextextended('room:' || $1, 0));
```

Transaction-scoped, released automatically at commit or rollback. Hash collisions cause unnecessary serialization, never incorrectness.

### SERIALIZABLE

Makes the naive `SELECT`-then-`INSERT` correct via predicate locks, at the cost of `40001` serialization failures and a retry loop in every caller. Rarely worth it when an exclusion constraint gives the same guarantee with no retries at all.

## Practical extras

**Cleaning buffer.** If housekeeping needs two hours between guests, switch to `tstzrange` and pad the upper bound: `tstzrange(check_in, check_out + interval '2 hours', '[)')`. The constraint enforces the buffer for free.

**Holds with a TTL (time to live).** Insert with `status = 'held'`: it participates in the same partial index, so a held room is genuinely reserved. The index predicate cannot reference `now()`, so expire them with a reaper (`pg_cron` or a worker):

```sql
UPDATE reservation SET status = 'cancelled'
WHERE status = 'held' AND expires_at < now();
```

**Idempotency.** Add `idempotency_key text UNIQUE`. A double-clicked Book button then returns the original reservation instead of a spurious 409 against itself.

**Multi-room bookings.** Lock and insert in a deterministic order (`ORDER BY room_id`) in one transaction, or you trade double bookings for deadlocks.

> **Partitioning has a version cliff.** Before PG 17, exclusion constraints are not supported on partitioned tables at all, only on individual leaf partitions. PG 17 allows them provided the constraint includes every partition key column compared with `=`. Check your version before partitioning by hotel or by month.
{: .prompt-warning }

**Index maintenance.** GiST pages degrade under heavy churn. Schedule a periodic `REINDEX CONCURRENTLY` if you have high cancellation volume.

## Watch it work

The walkthrough below uses the `stay daterange` schema from earlier because it is the most readable; the behaviour is identical under option 3.

```sql
CREATE TABLE room (id bigint PRIMARY KEY);
INSERT INTO room VALUES (101);

-- 1. baseline booking
INSERT INTO reservation (room_id, guest_id, stay)
VALUES (101, 1, daterange('2026-03-12','2026-03-15','[)'));   -- OK

-- 2. overlaps nights 13 and 14
INSERT INTO reservation (room_id, guest_id, stay)
VALUES (101, 2, daterange('2026-03-13','2026-03-16','[)'));   -- 23P01

-- 3. checks in the day the first guest checks out
INSERT INTO reservation (room_id, guest_id, stay)
VALUES (101, 3, daterange('2026-03-15','2026-03-18','[)'));   -- OK

-- 4. zero nights
INSERT INTO reservation (room_id, guest_id, stay)
VALUES (101, 4, daterange('2026-03-20','2026-03-20','[)'));   -- 23514

-- 5. cancel #1, then rebook the same dates
UPDATE reservation SET status = 'cancelled' WHERE guest_id = 1;
INSERT INTO reservation (room_id, guest_id, stay)
VALUES (101, 5, daterange('2026-03-12','2026-03-15','[)'));   -- OK
```

And the range semantics on their own:

```sql
SELECT daterange('2026-03-12','2026-03-15');            -- [2026-03-12,2026-03-15)
SELECT daterange('2026-03-12','2026-03-15','[]');       -- [2026-03-12,2026-03-16)
SELECT upper(daterange('2026-03-12','2026-03-15','[]'));-- 2026-03-16
SELECT daterange('2026-03-12','2026-03-12','[)');       -- empty
SELECT daterange('2026-03-12','2026-03-12','[]');       -- [2026-03-12,2026-03-13)
SELECT 'empty'::daterange && 'empty'::daterange;        -- f
SELECT daterange('2026-01-01','2026-12-31') @> 'empty'::daterange;  -- t
```

Run `\d reservation` afterwards and you will see the GiST index PostgreSQL built for the constraint, with its `WHERE` predicate attached. That index is both the enforcement mechanism and the thing your availability query uses.

## Takeaways

1. Do not check whether the room is free. Make an overlapping booking unrepresentable and let the `INSERT` be the check.
2. `EXCLUDE USING gist (room_id WITH =, stay WITH &&)` is correct at `READ COMMITTED` because index entries carry no visibility information at all. The constraint runs the same index scan your query does, under `SnapshotDirty` instead of your MVCC snapshot, and waits on the conflicting transaction rather than ignoring it.
3. `23P01` is your 409. The constraint name is in the error: match on it, not just the SQLSTATE.
4. `empty` is a flag bit, and `empty && anything` is always false. Guard against it or you accumulate invisible ghost reservations.
5. `'[]'` with equal dates is a real one-night booking, not a no-op. Hardcode the bounds token in the DDL and guard on `check_out > check_in`.
6. Pick one source of truth for the dates. Never dual-write the range and the scalars: it is the one failure here that raises no error at all.

### References

1. [PostgreSQL Documentation: Range Types](https://www.postgresql.org/docs/current/rangetypes.html)
2. [PostgreSQL Documentation: Constraints: Exclusion Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION)
3. [PostgreSQL Documentation: CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)
4. [PostgreSQL Documentation: Generated Columns](https://www.postgresql.org/docs/current/ddl-generated-columns.html)
5. [PostgreSQL Documentation: Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
6. [PostgreSQL Documentation: Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
7. [PostgreSQL source: `src/backend/executor/execIndexing.c`](https://github.com/postgres/postgres/blob/master/src/backend/executor/execIndexing.c) (the wait-and-retry protocol, and the deadlock note)
8. [PostgreSQL source: `src/include/access/itup.h`](https://github.com/postgres/postgres/blob/master/src/include/access/itup.h) and [`htup_details.h`](https://github.com/postgres/postgres/blob/master/src/include/access/htup_details.h) (index vs heap tuple layout)
