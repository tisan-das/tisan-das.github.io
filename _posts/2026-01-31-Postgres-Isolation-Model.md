---
layout: post
title: PostgreSQL - Isolation Levels
published: true
---

The transaction isolation level is one of the vital aspects to understand how transactions influence each other when run concurrently. Isolation level establishes a balance between consistency and performance. Without knowledge of the transaction isolation level, the application might behave differently than expected.

It's to be noted that the discussions here are limited to postgres, however the same concept can be applied to all the relational databases, that rely on **Multi-Version Concurrency Control (MVCC)**. MVCC is a widely used approach that enables high concurrency, allowing transactions to read and write the same data with less blocking.

Instead of overwriting a record when it is updated, the database creates a new version of that record. This means:
- Readers can continue viewing the old version safely.
- Writers update a new version without stopping others.
- No read/write blocking happens.


### How MVCC Works

PostgreSQL implements MVCC using transaction IDs and hidden metadata columns on every row:

- **XID (Transaction ID)**: Every transaction gets a unique, incrementing transaction ID when it starts
- **xmin**: Stores the XID of the transaction that created/inserted this row version
​- **xmax**: Stores the XID of the transaction that deleted or updated this row (0 if still active)
​
When a transaction modifies a row, PostgreSQL doesn't overwrite the existing version. Instead, it creates a new version with a new xmin value. For deletes, the xmax of the existing row is set to the current transaction's ID. Other transactions can still see the old version until they're ready to see the new committed state, based on their isolation level and transaction start time.
​


### Detailed Example: Concurrent Updates

##### Scenario 1: Basic Concurrent Read and Write

Let's say you have an accounts table:

```sql
CREATE TABLE accounts (
    id INT PRIMARY KEY,
    client VARCHAR(50),
    amount DECIMAL(10,2)
);

INSERT INTO accounts VALUES (1, 'alice', 1000.00);
```

Transaction 1 (XID = 100):
```sql
BEGIN;
UPDATE accounts SET amount = amount - 200 WHERE id = 1;
-- Row version created: xmin=100, xmax=0, amount=800.00
-- Old version still exists: xmin=99, xmax=100, amount=1000.00
```

Transaction 2 (XID = 101) starts while Transaction 1 is still running:
```sql
BEGIN;
SELECT * FROM accounts WHERE id = 1;
-- Returns amount = 1000.00 (sees old version because xmax=100 is not committed)
```

Transaction 1 completes:
```sql
COMMIT;
-- Now the xmin=100 version becomes visible to new transactions
```

Transaction 2 (still running, at READ COMMITTED level):
```sql
SELECT * FROM accounts WHERE id = 1;
-- Returns amount = 800.00 (now sees committed changes)
COMMIT;
```


### Scenario 2: Lost Update Prevention

Two concurrent transactions are trying to update the same account:​
Initial state: Account has ₽1000

Transaction 1 (XID = 200):
```sql
BEGIN;
SELECT amount FROM accounts WHERE id = 1;  -- Reads ₽1000
```

Transaction 2 (XID = 201):
```sql
BEGIN;
SELECT amount FROM accounts WHERE id = 1;  -- Also reads ₽1000
```

Transaction 1 continues:
```sql
UPDATE accounts SET amount = amount + 100 WHERE id = 1;
COMMIT;  -- Successfully commits ₽1100
```

Transaction 2 attempts update:
```sql
UPDATE accounts SET amount = amount + 100 WHERE id = 1;
-- This statement WAITS because Transaction 1 modified this row
-- After Transaction 1 commits, Transaction 2 re-evaluates
-- It now sees amount = ₽1100 and adds 100
COMMIT;  -- Final amount is ₽1200 (correct!)
```
PostgreSQL prevents the lost update by making Transaction 2 wait and then re-evaluating the row after Transaction 1 commits.
​

### Scenario 3: Repeatable Read Isolation
Transaction 1 (REPEATABLE READ):
```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT sum(amount) FROM accounts WHERE client = 'bob';
-- Returns 1000.00 (accounts 2 and 3 each have 500.00)
```

Transaction 2 transfers money:
```sql
BEGIN;
UPDATE accounts SET amount = amount - 100 WHERE id = 2;
UPDATE accounts SET amount = amount + 100 WHERE id = 3;
COMMIT;
```


Transaction 1 reads again:
```sql
SELECT sum(amount) FROM accounts WHERE client = 'bob';
-- Still returns 1000.00 (sees snapshot from transaction start)
-- Does NOT see Transaction 2's committed changes
COMMIT;
```

At the REPEATABLE READ level, Transaction 1 sees a consistent snapshot of the database as it existed when the transaction began, even though other transactions have committed changes.



### Details on isolation levels

The SQL standard defines isolation levels based on which anomalies (problems) they prevent:
- **Dirty reads**: Reading uncommitted data from other transactions that might be rolled back
- **Non-repeatable reads**: Reading the same row twice in a transaction and getting different values
- **Phantom reads**: Running the same query twice and getting different sets of rows
- **Serialization anomalies**: Results inconsistent with any serial execution order
​

##### The Four SQL Standard Isolation Levels
The SQL standard defines four isolation levels in increasing order of strictness:
​- READ UNCOMMITTED (weakest)
- READ COMMITTED
- REPEATABLE READ
- SERIALIZABLE (strongest)


PostgreSQL technically supports all four levels, but internally implements only three distinct isolation levels:

**READ UNCOMMITTED** behaves identically to READ COMMITTED (PostgreSQL never allows dirty reads)

READ COMMITTED, REPEATABLE READ, and SERIALIZABLE are distinct implementations. This is because PostgreSQL's MVCC architecture prevents dirty reads, so there's no way to implement a true READ UNCOMMITTED level.

Detailed Breakdown of Each Level
##### READ UNCOMMITTED
PostgreSQL behavior: Treated as READ COMMITTED
Prevents: Dirty reads (in PostgreSQL)
Allows: Non-repeatable reads, phantom reads, serialization anomalies
​
Since PostgreSQL doesn't actually implement this level separately, all the guarantees of READ COMMITTED apply.
​

##### READ COMMITTED (Default)
**Snapshot timing**: Each statement sees a fresh snapshot of committed data at the start of that statement
Prevents: Dirty reads
Allows: Non-repeatable reads, phantom reads, serialization anomalies
​

**Example of non-repeatable read at READ COMMITTED:**

```sql
-- Transaction 1
BEGIN;
SELECT balance FROM accounts WHERE id = 1;  -- Returns 1000

-- Transaction 2 (in parallel)
BEGIN;
UPDATE accounts SET balance = 500 WHERE id = 1;
COMMIT;

-- Transaction 1 continues
SELECT balance FROM accounts WHERE id = 1;  -- Now returns 500 (different!)
COMMIT;
```

The same SELECT query returned different values within a single transaction because READ COMMITTED creates a new snapshot for each statement. This is acceptable for many applications, but it can cause issues in complex business logic.

**When to use**: High-volume applications where slight inconsistencies are acceptable, or when you're only performing simple single-statement operations.

##### REPEATABLE READ
**Snapshot timing**: Transaction sees a consistent snapshot from the start of the first non-transaction-control statement
​

Prevents: Dirty reads, non-repeatable reads
​
Allows: Phantom reads (per SQL standard, but PostgreSQL prevents them too), serialization anomalies

**Example of consistent reads at REPEATABLE READ:**

```sql
-- Transaction 1
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id = 1;  -- Returns 1000

-- Transaction 2 (in parallel)
BEGIN;
UPDATE accounts SET balance = 500 WHERE id = 1;
COMMIT;

-- Transaction 1 continues
SELECT balance FROM accounts WHERE id = 1;  -- Still returns 1000 (consistent!)
COMMIT;
```

The second SELECT still sees the old value because REPEATABLE READ maintains a consistent snapshot throughout the entire transaction.

PostgreSQL bonus: PostgreSQL's REPEATABLE READ actually prevents phantom reads too, making it stronger than the SQL standard requires.

**When to use**: Most banking and financial operations that need consistent reads across multiple queries within a transaction.
​

##### SERIALIZABLE (Strictest)
**Snapshot timing**: Transaction sees a consistent snapshot, plus PostgreSQL monitors for read-write conflicts
​

Prevents: All anomalies—dirty reads, non-repeatable reads, phantom reads, and serialization anomalies

How it works: PostgreSQL uses Serializable Snapshot Isolation (SSI) to detect conflicts and will abort transactions that would cause anomalies.

**Example of serialization anomaly prevention:**

```sql
-- Account A: $1000, Account B: $1000

-- Transaction 1: Check if total > $1500, then withdraw from A
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT sum(balance) FROM accounts;  -- Sees $2000
-- Decides to proceed with withdrawal
UPDATE accounts SET balance = balance - 600 WHERE id = 'A';

-- Transaction 2 (concurrent): Withdraw from B
BEGIN ISOLATION LEVEL SERIALIZABLE;
UPDATE accounts SET balance = balance - 600 WHERE id = 'B';
COMMIT;  -- Succeeds

-- Transaction 1 tries to commit
COMMIT;  -- ERROR: could not serialize access due to read/write dependencies
```

One transaction is aborted to prevent an inconsistent state where both withdrawals succeed, even though the total balance check should have prevented it.

**When to use**: Critical financial operations, complex multi-row transactions, anywhere data integrity is paramount.


### References
1. [What is Multi-Version Concurrency Control (MVCC) in DBMS?](https://www.geeksforgeeks.org/dbms/what-is-multi-version-concurrency-control-mvcc-in-dbms/)
2. [What is MVCC? How does multiversion concurrency control work?](https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/What-is-MVCC-How-does-Multiversion-Concurrencty-Control-work)


