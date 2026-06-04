# SECTION C — SCALABILITY & PROBLEM SOLVING

**Scenario:** 1000 internships published. Within 1 hour, 50,000 students apply (~14 applications/second).

### 1. How will your system handle this traffic?

- **Connection pooling** — Use PgBouncer to reuse database connections and avoid connection overhead.
- **Gunicorn with multiple workers** — Run Django with `gunicorn -w 4` to handle concurrent requests.
- **Horizontal scaling** — Deploy multiple Django instances behind the load balancer.

### 2. How will you prevent duplicate applications?

- **Database-level constraint** — Already implemented via `unique_together = ('student', 'internship')` in the Application model. This guarantees no duplicates even under race conditions.
- **Application-level check** — The `ApplyInternshipView` checks `Application.objects.filter(student=request.user, internship=...).exists()` before creating.
- **Optimistic locking / `get_or_create`** — Use `Application.objects.get_or_create(student=request.user, internship=internship)` with IntegrityError handling as a safety net.
- The DB constraint is the single source of truth — it prevents duplicates regardless of race conditions between concurrent requests.

### 3. How will you keep response time below 500ms?

- **Indexes** — All foreign keys and filtered fields indexed (already done: `student`, `internship`, `status`, `company`, `created_at`).
- **`select_related`** — Already used in queries (`select_related('internship', 'student')`) to avoid N+1 queries.
- **Pagination** — Add `PageNumberPagination` or `CursorPagination` to list endpoints to avoid returning thousands of records at once.
- **Caching** — Cache the internships list endpoint with a short TTL since it's read-heavy and public.
- **Read replicas** — Route read queries to replicas to distribute load.

### 4. What indexes will you create?

- `email`, `role` (users table)
- `company`, `created_at` (internships table)
- `student`, `internship`, `status` (applications table)
- Composite: `(internship_id, created_at DESC)`, `(student_id, internship_id)`

### 5. Will you use Redis?

**Yes.** for:

- **Caching** — Cache the internships list endpoint (`GET /api/internships/`) which is public and read-heavy. Invalidate on create/update/delete.
- **Rate limiting** — Use `django-ratelimit` with Redis backend to throttle API requests per IP/user.
- **Task queuing** — Offload non-critical tasks like sending emails or generating reports via Redis + Celery.

### 6. Will you use Queue Systems (RabbitMQ/Kafka)?

**Yes, for specific use cases:**

- **Celery + RabbitMQ** — Offload asynchronous tasks:
  - Sending confirmation emails to students after applying.
  - Notifying companies when a new application arrives.
  - Generating analytics/reports without blocking API responses.
  - Batch processing (e.g., CSV exports).
- **Kafka** — Not needed at this scale.

### 7. How will you scale the system?

**Vertical scaling (first):**
- Increase server RAM/CPU.
- Tune PostgreSQL (shared_buffers, work_mem, effective_cache_size).

**Horizontal scaling (next):**
- **App layer** — Deploy multiple Django instances behind Nginx load balancer.
- **Database** — Set up PostgreSQL primary-replica: write to primary, read from replicas.
- **Separate read/write in code** — Use Django's database router to route `GET` requests to replicas.
- **Caching layer** — Add Redis cluster for cached responses and rate limiting.
- **CDN** — Serve static/media files via CDN (CloudFront, Cloudflare).
- **Auto-scaling** — Use Kubernetes or AWS ECS to auto-scale app instances based on CPU/memory/request rate.

---

# SECTION D — QUERY OPTIMIZATION

**Given query:**
```sql
SELECT * FROM applications WHERE internships_id = 100 ORDER BY created_at DESC;
```

The applications table contains **more than 10 million records**.

### 1. Why is the query slow?

- **Full table scan** 
- **Sort on disk** —filtered list when sorted is slow
- **`SELECT *`** — Retrieves all columns including large fields (e.g., `resume` file path), increasing I/O and network transfer.

### 2. How will you optimize it?

- **Add a composite index** on `(internships_id, created_at DESC)` — This lets PostgreSQL find matching rows by `internships_id` and return them already sorted by `created_at`, eliminating both the full scan and the explicit sort.
- **Use `SELECT` with only needed columns** — Instead of `SELECT *`, specify only the columns required (e.g., `SELECT id, student_id, status, applied_at`).
- **Partitioning** — Partition the table by `internships_id` (list partitioning) or by `created_at` (range partitioning, e.g., monthly). This limits the amount of data scanned per query.
- **Covering index** — If queries consistently need specific columns, create an index that includes them (e.g., `INCLUDE (status, student_id)`).
- **Vacuum and analyze** — Run `ANALYZE` to update table statistics so the query planner chooses the index correctly.

### 3. What indexes will you create?

- Composite index on `(internships_id, created_at DESC)` 
- Covering index on `(internships_id, created_at DESC) INCLUDE (student_id, status)`

### 4. How will you measure performance improvement?

- **Before optimization:** Run `EXPLAIN ANALYZE SELECT * FROM applications WHERE internships_id = 100 ORDER BY created_at DESC;` and record:
  - Execution time
  - Rows scanned
  - Whether a sequential scan or index scan is used
- **After optimization:** Run the same `EXPLAIN ANALYZE` query and compare:
  - **Execution time** — Target: <5ms vs potentially seconds before.
  - **Rows examined** — Should drop from 10M+ to only matching rows.
  - **Scan type** — Should show "Index Scan" instead of "Seq Scan".
  - **Sort method** — Should show "Index Only Scan" or no explicit sort step.
- **pg_stat_user_tables** — Monitor `seq_tup_read` vs `idx_tup_fetch` ratios.
- **pg_stat_statements** — Track `mean_exec_time` and `rows` for this query pattern over time.
- **Load testing** — Use `pgbench` or `locust` to simulate concurrent traffic and measure p95/p99 latency.
