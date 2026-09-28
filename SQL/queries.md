### 2nd Max budget

```sql
select MAX(budget) from projects
where budget < (select MAX(budget) from projects);

select budget as '2ndmax'
from (select * from projects order by budget desc limit 2)
order by budget asc limit 1;

select budget as '2ndmax' from (
    select p.*, DENSE_RANK() over (
        order by budget desc
    ) as rank from projects p
)
where rank = 2;
```

### DENSE_RANK()

DENSE_RANK is used to rank rows based on the OVER clause

```sql
select t.* from (
    select 
        DENSE_RANK() OVER (
            partition by owning_department_id
            order by budget asc
        ) as rank, p.*
    from projects p
) as t
where rank = 2;
```

### Duplicate Entries Check

```sql
select owning_department_id, count(*) as 'cnt'
from projects
group by owning_department_id
having cnt > 1;
```

### Delete Duplicate Entries keeping 1 row

```sql
with ranked as (
    select p.*, ROW_NUMBER() OVER (
        partition by owning_department_id
        order by budget
    ) as row_rank
    from projects p
)
delete from projects
where project_id in (
    select project_id from ranked where row_rank > 1;
)
```

### Running Total

```sql
select owning_department_id, start_date, 
    SUM(budget) over (
        order by start_date
    ) as running_total
from projects;
```

### Longest Consecutive Streak

```sql
WITH GroupedLogins AS (
    SELECT 
        user_id,
        date,
        -- Subtracting the dense rank from the date creates a unique grouping identifier
        date(date, '-' || DENSE_RANK() OVER (PARTITION BY user_id ORDER BY date) || ' day') AS streak_group
    FROM projects
),
StreakCounts AS (
    SELECT 
        user_id,
        COUNT(*) AS streak_length
    FROM GroupedLogins
    GROUP BY user_id, streak_group
)
SELECT 
    user_id, 
    MAX(streak_length) AS longest_streak
FROM StreakCounts
GROUP BY user_id;
```

### Overlapping Meeting Rooms

```sql
select a.*, b.*
from reservations a
join reservations b
where a.id != b.id and
    a.room_id = b.room_id and
    a.start_time < b.end_time and
    b.start_time < a.end_time
```

### Find Users Who Performed A -> B -> C

```sql
SELECT DISTINCT e1.user
FROM Events e1
JOIN Events e2 
    ON e1.user = e2.user 
   AND e2.timestamp > e1.timestamp
JOIN Events e3 
    ON e2.user = e3.user 
   AND e3.timestamp > e2.timestamp
WHERE e1.event = 'login'
  AND e2.event = 'view'
  AND e3.event = 'buy';

```

```sql
WITH RankedEvents AS (
    SELECT 
        user,
        event,
        timestamp,
        LAG(event, 1) OVER (PARTITION BY user ORDER BY timestamp) AS prev_event,
        LAG(event, 2) OVER (PARTITION BY user ORDER BY timestamp) AS second_prev_event
    FROM Events
)
SELECT DISTINCT user
FROM RankedEvents
WHERE event = 'buy'
  AND prev_event = 'view'
  AND second_prev_event = 'login';
```

```sql
-- % revenue growth over months
WITH x AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (
            ORDER BY month
        ) AS previous_revenue
    FROM Sales
)
SELECT
    month,
    revenue,
    (revenue - previous_revenue) * 100.0
        / previous_revenue AS growth_pct
FROM x;
```


| Value | ROW_NUMBER | RANK | DENSE_RANK |
|---:|---:|---:|---:|
| 100 | 1 | 1 | 1 |
| 90 | 2 | 2 | 2 |
| 90 | 3 | 2 | 2 |
| 80 | 4 | 4 | 3 |
| 70 | 5 | 5 | 4 |

### Composite Index

The leftmost-prefix principle states that a composite index (an index on multiple columns, like (A, B, C)) can only be used by the SQL query optimizer if the query filters include the columns starting from the leftmost side of the index definition, without skipping any gaps.

composite index on (country, state, city)

| Query WHERE Clause | Uses Index? | Why? |
|---|---|---|
| WHERE country = 'US' AND state = 'NY' AND city = 'NYC' | Yes (Fully) | Follows the exact leftmost order without gaps. |
| WHERE country = 'US' AND state = 'NY' | Yes (Partially) | Uses the leftmost prefix (country, state). |
| WHERE country = 'US' | Yes (Partially) | Uses the leftmost prefix (country). |
| WHERE state = 'NY' AND city = 'NYC' | No | Missed country. The leftmost column is absent. |
| WHERE city = 'NYC' | No | Missed both country and state. |
| WHERE country = 'US' AND city = 'NYC' | Only country | Uses country to narrow down data, but skips state, so it cannot use the index for city. |

### Database Deadlock Prevention

* The Problem: Cyclic dependencies occur when Transaction A locks Row 1 and waits for Row 2, while Transaction B locks Row 2 and waits for Row 1.
* The Solutions:
* Enforcing a consistent locking order (sorting primary key updates application-side).
   * Using upserts/batch queries (WHERE id IN (1, 2)) to let the optimizer sort the locks.
   * Leveraging Optimistic Concurrency Control (OCC) using version numbers instead of row locks.
   * Adding application-level retry logic with exponential backoffs to capture and repeat deadlocked requests.

### Index Creation Space & Performance

* Storage Footprint: Creating a B-Tree index copies and sorts data out-of-line. It temporarily requires 2x to 3x the final index size in free disk space to handle sorting overhead, writing to disk if allocated RAM memory settings (like Postgres's maintenance_work_mem) are insufficient.
* Concurrence & Availability: Standard index creation locks tables against writes. Production environments require non-blocking syntax commands like CREATE INDEX CONCURRENTLY (PostgreSQL) or ALGORITHM=INPLACE LOCK=NONE (MySQL) to maintain uptime.

### Transaction Isolation

- READ UNCOMMITTED — Almost never.  Analytics/reporting where slight inconsistency is acceptable and you need max throughput.
- READ COMMITTED — Best general-purpose default.  Prevents dirty reads with minimal locking. Good for most OLTP apps.
- REPEATABLE READ — When you need a consistent snapshot within a transaction (e.g., financial calculations, multi-step business logic). 
- SERIALIZABLE — When absolute correctness is critical and you can afford the concurrency hit (e.g., bank transfers, seat reservations).  Expect serialization failures that your app must retry.

#### Anomaly

- Dirty Read — You read data that another transaction has written but not yet committed (it could be rolled back). 
- Non-Repeatable Read — You read a row, another transaction updates/deletes it and commits, you read the same row again and get a different value. 
- Phantom Read — You run a range query, another transaction inserts new rows matching your criteria and commits, you re-run the query and see new rows appear.



