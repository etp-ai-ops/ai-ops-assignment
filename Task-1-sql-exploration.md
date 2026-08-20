[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | Task 1 ⮕ | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 1 Guidance: Exploring the ITDK Representation With Direct SQL

Use this guide with the Task 1 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). Unlike every later task, Task 1 does **not** go through MCP. You connect directly to the local synthetic fixture with a read-only role and write the `SELECT` statements yourself, in the same style taught by the prerequisite ITDK assignment's `SQL.md`. This is deliberate: understanding what a fixed MCP tool is allowed to promise is much easier once you have felt the underlying relations firsthand.

---

## Why Direct SQL, Only Here

[Datasets](Datasets.md#direct-sql-access-for-exploration-task-1-only) describes the connection path in full. In short: this path reaches only the small invented fixture used for local practice, never the frozen graded teaching snapshot. Task 4's graded investigation must still go entirely through your MCP tools — direct SQL there would bypass the exact interface this assignment teaches you to build. Keep that boundary straight in your own head as you work: Task 1 is a hands-on SQL warm-up against practice data, not a rehearsal for how you will access the graded snapshot later.

---

## Connect With `pd.read_sql`

Open one SQLAlchemy engine using the read-only DSN from `db_credentials.env` (see [Datasets](Datasets.md#direct-sql-access-for-exploration-task-1-only)), then run each query with `pandas.read_sql` so the result comes back as a DataFrame:

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(READ_DSN)   # READ_DSN loaded from db_credentials.env

df = pd.read_sql("""
    SELECT link_id, endpoint_ordinal, endpoint_token, node_id
    FROM caida_itdk.itdk_link_endpoints
    WHERE link_id = %(link_id)s
    ORDER BY endpoint_ordinal
""", engine, params={"link_id": "L1"})
```

Use a bound parameter (`%(name)s` with a `params=` dict, or `%s` with a tuple) rather than an f-string whenever the value is something you might later change or a caller might supply — the habit matters even though you are the only "caller" here, because it is the same habit Task 3 will require of your MCP tools.

---

## Distinguish Endpoint Fields (Q1–Q2)

Run this against the fixture:

```sql
SELECT link_id, endpoint_ordinal, endpoint_token, node_id
FROM caida_itdk.itdk_link_endpoints
WHERE link_id = 'L1'
ORDER BY endpoint_ordinal;
```

For `L1` you get two rows: `N1` at ordinal 0 with token `N1:192.0.2.1`, and `N2` at ordinal 1 with token `N2:192.0.2.2`. Make a compact table of all four columns and annotate each role:

```text
link_id           -> groups endpoint rows into one inferred adjacency/hyperlink
endpoint_ordinal  -> distinguishes positions inside that link, not direction or path order
endpoint_token    -> preserves source endpoint encoding; sometimes carries an IP, sometimes not
node_id           -> normalized router identifier used across every router-level relation
```

Now look at `L2`:

```sql
SELECT link_id, endpoint_ordinal, endpoint_token, node_id
FROM caida_itdk.itdk_link_endpoints
WHERE link_id = 'L2'
ORDER BY endpoint_ordinal;
```

Row 0 has `endpoint_token = 'N2'` — a bare token with no embedded IP at all — while row 1 has `endpoint_token = 'N3:198.51.100.3'`. This is the concrete case for **Q2**: if you tried to use `endpoint_token` as though it were the router-level join key (say, splitting on `:` and joining the fragment before the colon into `itdk_node_as.node_id`), the bare `N2` token would still work by coincidence here, but any token carrying a different prefix, punctuation, or no colon at all would either fail to join or join to the wrong thing. `node_id` is the column every relation actually agrees on; `endpoint_token` is evidence about the interface, not a join key.

- **Q1** For the supplied fixture link, explain the different roles of `link_id`, `endpoint_ordinal`, `endpoint_token`, and `node_id`, citing concrete returned rows.
- **Q2** Which field is the normal key for relating an endpoint to AS or geolocation rows, and what goes wrong if `endpoint_token` is used as though it were that key?

---

## Multiplicity Without Flattening (Q3)

Before counting, name the grain of the row you are looking at:

- one row of `itdk_link_endpoints` is one endpoint position of one inferred link;
- one row of `itdk_node_as` is one `(node_id, asn)` assignment;
- one row of `itdk_node_geolocation` is one supplied location per node.

Two different one-to-many patterns are visible in the fixture:

```sql
-- (1) one node, many link-endpoint rows
SELECT link_id, endpoint_ordinal, endpoint_token
FROM caida_itdk.itdk_link_endpoints
WHERE node_id = 'N2'
ORDER BY link_id, endpoint_ordinal;

-- (2) one node, many AS-assignment rows
SELECT asn, method
FROM caida_itdk.itdk_node_as
WHERE node_id = 'N2'
ORDER BY asn;
```

`N2` participates in three separate link-endpoint rows (`L1`, `L2`, `L6`) and carries two AS-assignment rows (`64500` via `bdrmapit` and `64501` via `alias-overlap`). These are two *different* one-to-many relationships — a node can sit at many link endpoints, and independently can carry more than one AS assignment. If you joined `itdk_link_endpoints` directly to `itdk_node_as` for `N2` without deduplicating, you would get `3 × 2 = 6` rows, none of which is "the" AS for `N2` — flattening this into one assumed row per router would either drop a real assignment or silently prefer one link membership over another.

- **Q3** Use the supplied fixture nodes to show two different one-to-many patterns in the four-relation model. Why would flattening all annotations into one assumed row per router lose information or multiply rows?

---

## Method Fields and Missing Evidence (Q4–Q5)

`method` on `itdk_node_as` and `itdk_node_geolocation` records how the assignment was made — `bdrmapit`, `alias-overlap`, `maxmind`, `hostname-hint`, `country-only`, and so on. Keep it in every evidence table you build; a value produced by an inference method should be phrased as "assigned" or "inferred," not "proved."

```sql
SELECT node_id, continent, country, region, city, latitude, longitude, method
FROM caida_itdk.itdk_node_geolocation
WHERE node_id = 'N6';
```

`N6` returns `country = 'AU'`, `method = 'country-only'`, and `region`, `city`, `latitude`, and `longitude` all `NULL`. This is a defensible **Q5** example: the fixture asserts a country for `N6` but nothing more precise, and the `method` label tells you why — the geolocation process only had country-level evidence to work with. The tempting-but-unjustified conclusion would be to treat the missing city/coordinates as proof that `N6` has no more precise real-world location, or to guess a plausible city from the country alone; the correct conclusion is only that this snapshot's geolocation process did not produce anything more precise for this node.

A second good missing-value case is `L2`'s bare `N2` endpoint token (no embedded IP) or an IP in `itdk_router_hostnames` with no PTR row at all (query a fixture IP such as `198.51.100.4` against the hostnames table and compare it with one that does resolve). In every case, distinguish three states: a query with no matching rows, a returned row with a null field, and a failed query. Only the third is an execution problem.

- **Q4** What do the returned AS-assignment and geolocation `method` fields communicate? Explain why those values should remain in an evidence table.
- **Q5** Identify one missing PTR, location, interface encoding, or annotation in the fixture. What can you conclude from the missing value, and what tempting conclusion is not justified?

---

## What Your Write-Up Should Address

Answer Q1–Q5 with concrete fixture rows and your own `pd.read_sql` output — not with generic networking knowledge. State the grain of every count, explain why `node_id` is the relational key, retain `method` labels, and give a careful interpretation of missing evidence. Everything in Task 1 describes the invented `nids-itdk-mcp-synthetic-v1` fixture, not the public Internet or the graded snapshot; say so explicitly in your answers.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | Task 1 ⮕ | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
