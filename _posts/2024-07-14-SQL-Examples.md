---
layout: post
title: SQL Examples
published: true
---


#### 

```sql
SELECT 
    LOWER(customer_name) AS lower_case_name,
    DATE_FORMAT(order_date, '%Y-%m-%d') AS formatted_date,
    TIMESTAMPDIFF(DAY, order_date, NOW()) AS days_since_order
FROM 
    orders
JOIN 
    customers ON orders.customer_id = customers.customer_id;
```



```sql
-- Create a test table
CREATE TABLE test_table (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP(3)
);

-- Begin a transaction
BEGIN;

-- Insert a record with the current timestamp with millisecond precision
INSERT INTO test_table (created_at) VALUES (NOW(3));

-- Insert another record with a timestamp 1 day in the future
INSERT INTO test_table (created_at) VALUES (NOW(3) + INTERVAL '1 day');

-- Commit the transaction
COMMIT;

-- Begin another transaction
BEGIN;

-- Insert a record with a timestamp 1 hour in the past
INSERT INTO test_table (created_at) VALUES (NOW(3) - INTERVAL '1 hour');

-- Simulate an error (e.g., duplicate key) to trigger a rollback
-- This line will cause an error because the primary key 'id' will conflict
INSERT INTO test_table (id, created_at) VALUES (1, NOW(3));

-- Rollback the transaction due to the error
ROLLBACK;

-- Select all records to see the state of the table
SELECT * FROM test_table;
```




```sql
SELECT 
    id,
    IFNULL(name, 'Unknown') AS name,
    IFNULL(age, 0) AS age
FROM 
    sample_table;
```
