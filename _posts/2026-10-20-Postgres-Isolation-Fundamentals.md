---
layout: post
title: "PostgreSQL - Why Isolation Levels Behave the Way They Do"
image: /images/postgres/03-isolation-fundamentals/01-row-history.webp
date: 2026-10-20 01:00:00 +0530
series: "PostgreSQL"
categories: ["Databases", "PostgreSQL"]
tags: [postgres, isolation-levels, mvcc, concurrency, transactions]
published: true
---

When two transactions work on the same data at the same time, PostgreSQL has to answer two questions: what is each transaction allowed to see, and what happens when both try to change the same row? The isolation level decides the answers. Postgres has three levels that behave differently: READ COMMITTED, the default; REPEATABLE READ; and SERIALIZABLE, the strictest.

Most explanations teach these levels as a list of rules. Say another transaction has just changed the row your `UPDATE` wants to change. Under READ COMMITTED, your `UPDATE` waits for the other transaction to finish, re-checks its `WHERE` clause against the new version of the row, and carries on. Under REPEATABLE READ, it waits the same way, but if the other transaction committed, yours is aborted with error `40001` and your application has to retry it from the start. SERIALIZABLE goes further and keeps track of what each transaction read, so it can abort one when the combined result couldn't have happened if the transactions had run one at a time.

Each of those rules is correct. Learned as a list, though, they're hard to remember and even harder to apply to a situation the list doesn't cover, because nothing says why each level behaves the way it does.

If you'd like to see the levels in action first, the [earlier post on isolation levels](/Postgres-Isolation-Model/) walks through each one with examples. This post explains why they work that way.

{% include series-nav.html %}

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5.5 and DeepSeek V4.1 Flash) based on conversations exploring PostgreSQL isolation levels and MVCC. All content has been reviewed, edited, and verified against the official PostgreSQL documentation.
{: .prompt-info }

## Two ingredients behind every rule

The rules aren't arbitrary. Every one of them follows from two ingredients:

1. **Three facts about how Postgres stores rows.** They're the same at every isolation level.
2. **One promise per isolation level** about what a transaction is allowed to see.

Put the two together, and in each situation there's only one behavior that keeps the level's promise without breaking a storage fact. That's the behavior Postgres picks. So instead of memorizing the rules, this post derives them one situation at a time: a read meeting another read, a read meeting a write that hasn't committed yet, two writes to the same row, and a write that makes an earlier read out of date. By the end, you should be able to work out what Postgres will do in a case you haven't seen before.

## Ingredient 1: Three storage facts (same at every isolation level)

The examples follow a single row, F12, through its versions.

**Fact 1: Rows are never overwritten.** An `UPDATE` writes a new version of the row and leaves the old version in place. VACUUM removes old versions later, once no transaction can still need them.
{: #fact-1}

**Fact 2: A reader picks one version, using its snapshot.** A snapshot is a list of which transactions' work you're allowed to see. To read a row, Postgres walks its versions and returns the one your snapshot permits. A read changes no data and leaves no record of who read the row. (A `SELECT` may still tidy the page, setting hint bits or pruning dead versions, but nothing it writes names the reader.)
{: #fact-2}

**Fact 3: Each row has a single, linear history.** A new version can only be added after the row's latest version. History can't branch, so two transactions can't both add a version after the same latest version. Writers to one row have to take turns.
{: #fact-3}

![Row F12 has versions 6, 7 and 8 in a chain, with version 8 as the latest version. A reader with an older snapshot picks version 7, a reader with a newer snapshot picks version 8, and a writer at any isolation level can only append after the latest version.](/images/postgres/03-isolation-fundamentals/01-row-history.webp)

The above picture is the central idea: readers can pick any point in a row's history, but writers can only add after the latest version.

## Ingredient 2: Each level is a promise about what you see

- **READ COMMITTED:** Each statement sees data that was committed before that statement started.
- **REPEATABLE READ:** The whole transaction sees one fixed snapshot, taken at its first statement.
- **SERIALIZABLE:** The final result is the same as if the transactions had run one at a time.

No level promises that you see the latest data. Every level promises a consistent snapshot of data that was already committed. That one point explains why reads never wait.

## Deriving each case

### Read meets read

Reads change no data ([Fact 2](#fact-2)), so no promise is at risk. There's nothing to do, at any level.

### Read meets an uncommitted write

T1 is updating row F12 and hasn't committed. T2 reads F12.

- The old version is still there ([Fact 1](#fact-1)).
- T2's snapshot excludes uncommitted work ([Fact 2](#fact-2)), so T2 picks the old version.
- T2 doesn't wait and never sees T1's uncommitted change.

Waiting would only make sense if T2 had been promised the latest data, and no level promises that. The result is the same at all three levels.

### Write meets write

This is the only case where storage itself forces a reaction, because only one transaction at a time can add the next version of a row ([Fact 3](#fact-3)).

**Why T2 waits, at every level.** T1 has written v8 after v7 but hasn't finished. T2 can't append yet, because which version is the latest depends on T1's outcome: if T1 commits, v8 is the latest version; if T1 rolls back, v7 still is. T2 has to wait until that's settled.

**Why the levels split after T1 commits.** T2 now has to write on top of v8, but v8 was created after T2's snapshot. The storage rule and the snapshot promise point in opposite directions:

![Storage requires T2 to write on top of version 8, but T2's snapshot only shows version 7. READ COMMITTED's per-statement promise allows using version 8, so it re-checks the WHERE clause and continues. REPEATABLE READ's one-snapshot promise and SERIALIZABLE's as-if-serial promise would break, so they abort with error 40001. Waiting cannot help because their snapshot never moves.](/images/postgres/03-isolation-fundamentals/02-write-write-dilemma.webp)

The reasoning, level by level:

**READ COMMITTED** only promised each statement a new snapshot of committed data. Letting this one `UPDATE` use the newest committed version of F12 (v8) breaks no promise. So that's what it does: it re-checks the `WHERE` against v8, then either applies the change or skips the row. Aborting here would be stricter than the promise requires.

**REPEATABLE READ** promised one fixed snapshot for the whole transaction. Writing on top of v8, which isn't in that snapshot, would make the transaction's result depend on data it officially can't see. Waiting won't help: the snapshot is frozen, so v8 will never become visible to it. That leaves two options, break the promise or give up, and Postgres gives up. It fails with `ERROR: could not serialize access due to concurrent update` (SQLSTATE `40001`), and you retry the whole transaction with a fresh snapshot.

**SERIALIZABLE** makes an even stronger promise, so it reaches the same answer.

This is also why the first updater wins. The first writer's transaction ID is already in the row's `xmax`, so the second writer is the one who runs into it.

### Write meets an earlier read

Here T1 read F12, and afterwards T2 changed it, so T1 is now working from stale information. Two questions decide what happens: is that a problem for the level's promise, and can Postgres even notice? The second question comes down to whether the operation leaves a footprint:

![When T1 writes F12, its transaction ID is set in the tuple's xmax, so any later writer finds it and every level notices. When T1 reads F12, the tuple is unchanged, so later writers cannot know; only SERIALIZABLE tracks reads separately, with SIRead (predicate) locks.](/images/postgres/03-isolation-fundamentals/03-footprints.webp)

A write leaves a footprint in the row: it sets the row's `xmax` to its own transaction ID. That's why write-write conflicts are caught at every level: the second writer finds the first writer's transaction ID in `xmax`, in the row itself. A read leaves no footprint ([Fact 2](#fact-2)), so a stale read can't be detected unless the engine keeps extra records.

Now hold each level up against its promise:

- **READ COMMITTED and REPEATABLE READ** don't need to notice. T1 read from a valid committed snapshot, which is all they promised. A stale read is still a read of a consistent committed past.
- **SERIALIZABLE** promised "as if one at a time." Write skew breaks that promise: each transaction's decision rests on something the other changed, so no serial order produces the result. To keep the promise, SERIALIZABLE has to create the footprints MVCC doesn't, which is what SIRead locks (PostgreSQL's predicate locks) are: a record of who read what. Readers must never wait under MVCC, so SERIALIZABLE can only act after the fact. When the recorded reads and writes could form a cycle, it aborts one transaction with `ERROR: could not serialize access due to read/write dependencies among transactions` (`40001`). The check is conservative, so it sometimes aborts a transaction that would have been fine.

**If T1 then writes the row it read,** the lower levels split again. REPEATABLE READ runs into the write-write case above and fails with `40001`. READ COMMITTED doesn't: the new statement gets a new snapshot, so its write lands on top of T2's version. A value T1 computed in the application from the stale read then overwrites T2's change, which is a lost update. Compute it in the statement instead (`SET amount = amount + 100`, as in the earlier post's [lost-update example](/Postgres-Isolation-Model/#scenario-2-lost-update-prevention)).

**To make a read count below SERIALIZABLE, give it a footprint.** `SELECT ... FOR UPDATE` (or `FOR SHARE`) marks the row as locked in its `xmax`, the way a write does, so a later writer has to wait for it. That only works for rows that already exist. A check-then-insert worries about a row nobody has written yet, so it needs a lock on a parent row or a constraint, as in [Making Double Bookings Impossible](/Postgres-No-Double-Booking/#when-the-exclusion-constraint-is-the-wrong-tool).

## A Git analogy

Picture each row as its own Git branch that only accepts fast-forward pushes.

- **[Fact 1](#fact-1):** Commits are never rewritten, and old commits stay in history.
- **[Fact 2](#fact-2):** Reading is checking out a commit. Others can push while you read, and your checkout doesn't move.
- **[Fact 3](#fact-3):** A push must sit directly on the latest commit. There are no merges.

**Write-write.** You push, but someone else pushed after your checkout, so your push is rejected.

- READ COMMITTED automatically pulls the latest version of that one file, re-checks your condition, and pushes again. That's allowed because it only promised a new snapshot per statement.
- REPEATABLE READ and SERIALIZABLE based the whole task on one checkout. They throw the task away and start over from a fresh checkout.

**Read-write.** Someone pushed a change to a file you only read and based a decision on. Git keeps no record of which files you read, so it can't warn you. SERIALIZABLE is like adding a tracker that records every file you open. If a file your decision depended on changes underneath you, the tracker cancels your task.

## The whole derivation in one table

| Situation | Storage fact involved | READ COMMITTED | REPEATABLE READ | SERIALIZABLE |
|---|---|---|---|---|
| Read meets read | Reads change no data | Nothing to do | Nothing to do | Nothing to do |
| Read meets uncommitted write | Old version still exists, and the snapshot hides uncommitted work | Read the old version, no waiting | Same | Same |
| Write meets write, other transaction still running | Each row has one latest version | Wait | Wait | Wait |
| Write meets write, other transaction committed | The latest version is outside my snapshot | Using the newer version is allowed, so re-check and continue | Using the newer version would break the promise, so `40001` | Using the newer version would break the promise, so `40001` |
| A write makes an earlier read stale | Reads leave no footprint | Promise intact, ignore | Promise intact, ignore | Promise at risk, so track reads and abort when a cycle could form |

## In short

Because MVCC lets reads use older versions, readers never wait. Because each row has a single latest version, writers take turns. When a writer finds that the latest version is newer than its snapshot, the isolation promise decides the outcome: READ COMMITTED may use the newer version and carry on, while REPEATABLE READ and SERIALIZABLE must give up. Only SERIALIZABLE promises anything once a read goes stale, so only SERIALIZABLE pays the cost of tracking reads.

## References

1. [PostgreSQL documentation: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
2. [PostgreSQL documentation: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
3. [Dan R. K. Ports and Kevin Grittner, Serializable Snapshot Isolation in PostgreSQL (VLDB 2012)](https://arxiv.org/abs/1208.4179)
