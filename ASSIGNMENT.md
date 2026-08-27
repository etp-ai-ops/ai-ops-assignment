[README](README.md) | Assignment | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)

# Building an MCP Interface for Internet Topology Data

Everything you need to know to complete [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb) is in this
one document: the data model, the MCP tool contract, the safe-query rules, the exact contracts
for the three tools you build, how testing works, and the graded questions.

**Learning objectives.** Explore real CAIDA ITDK relations with direct SQL to answer questions
about how major networks interconnect and geolocate; use a working MCP server through an agent;
encode new analytical intents as restrictive JSON Schemas plus fixed, parameterized, read-only
SQL; test those contracts; and separate observed evidence from inference when you report
findings.

**Shape of the work.** Three parts:

| Part | What you do | Access path | Questions |
| --- | --- | --- | --- |
| 1 | Investigate real ASes' interconnection and geolocation with hand-written SQL | direct read-only SQL against the real teaching snapshot | Q1–Q3 |
| 2 | Use the 4 provided tools through an agent, in the notebook | a client-side tool-calling loop against an OpenAI-compatible endpoint + MCP | Q4–Q5 |
| 3 | Build 3 new general-purpose tools, then investigate with all 7 | your code + the same agent cells | Q6–Q9 |

Part 1 works with real, full-scale data and asks harder, open-ended analytical questions --
you have the full flexibility of hand-written SQL there. Parts 2 and 3 restrict you to the small,
fixed MCP tool vocabulary described below, so their questions are deliberately narrower in scope;
the payoff is that the same three general-purpose tools you build in Part 3 can be recombined to
answer many different questions, not just one each.

---

## 1. The data

### Real teaching snapshot vs. synthetic fixture

Graded analysis runs against a real, instructor-provided **ITDK teaching snapshot**: a read-only
Postgres role on the shared CAIDA ITDK database, restricted to `midar-iff-snmp`-derived
router-to-router topology (see the "Dataset scope" note your instructor distributes with the
connection details). This is real measurement data covering millions of router-level links and
AS assignments -- not an invented example. `db_credentials.env` holds the DSN for Part 1's direct
connection; the MCP server's own `DATABASE_URL` (set by whoever runs `docker compose`, not by
you) points the same read-only role at Parts 2 and 3. Record the snapshot's release identifier in
the notebook so a reader knows which data your answers describe.

This repository also ships a small deterministic synthetic **fixture**
`nids-itdk-mcp-synthetic-v1` (see [data/README.md](data/README.md)): six invented nodes, six links
(including multi-endpoint ones), eight AS-assignment rows, six geolocation rows, eleven hostname
rows, private-use ASNs, reserved documentation IP ranges, and `.test` hostnames. **The fixture
exists only so `uv run pytest` has something deterministic to run against** -- it is not the
target of any graded question, and it is not a measurement of the public Internet. Do not answer
Q1–Q9 from the fixture; use it only while iterating on `student_tools.py` before you point your
tests or notebook at the real snapshot.

ITDK data is access-controlled real measurement data about real networks. Do not commit database
contents, generated CSVs, snapshot rows, or the real read-only credentials themselves -- they stay
in the git-ignored `db_credentials.env` / `itdk_mcp_credentials.env` files only, and are handed
out by your instructor the same way a prior CAIDA assignment's `db_credentials.env` was.

### From measurements to router-level topology

Traceroute records responsive interfaces along a path. ITDK alias resolution groups interface
addresses that appear to belong to one physical router; that inferred router is a **node**, and
adjacent observations become **links** between nodes. This graph depends on vantage points,
destinations, responses, collection time, and processing choices. A node is an inference about a
device; a link is an observed or inferred adjacency. Neither proves ownership, physical location,
traffic, capacity, or a business relationship. Some links have more than two endpoints — treat a
hyperlink as a multi-endpoint observation, not a broken pair.

### The four relations

`caida_itdk.itdk_link_endpoints` — one row per endpoint position of one inferred link.

| Column | Type | Meaning |
| --- | --- | --- |
| `link_id` | `text` | Identifier shared by all endpoints of one inferred link. |
| `endpoint_ordinal` | `integer` | Position distinguishing endpoint rows within a link. Not direction. |
| `endpoint_token` | `text` | Source endpoint encoding kept for provenance; *may* encode `node:interface`. |
| `node_id` | `text` | Normalized router-node identifier used for joins and node filtering. |

Primary key `(link_id, endpoint_ordinal)`; `node_id` indexed. A bare or unusual `endpoint_token`
must not be parsed as though every row contains an IP address.

`caida_itdk.itdk_node_as` — router-node to ASN assignments.

| Column | Type | Meaning |
| --- | --- | --- |
| `node_id` | `text` | Router-node identifier. |
| `asn` | `bigint` | Assigned Autonomous System Number. |
| `method` | `text` | Method/provenance label for the assignment. |

Primary key `(node_id, asn)`; `asn` indexed. **A node can have more than one assignment row.**
Do not silently pick one ASN or drop `method`.

`caida_itdk.itdk_node_geolocation` — one supplied geolocation annotation per node.

| Column | Type | Meaning |
| --- | --- | --- |
| `node_id` | `text` | Primary key. |
| `continent`, `country`, `region`, `city` | `text` | Place labels; `country` is two uppercase letters. |
| `latitude`, `longitude` | `double precision` | Decimal degrees; may be null. |
| `method` | `text` | Method/provenance label for the location. |

The search index begins with `country`, then `longitude`, so every supported geolocation search
requires a country and may narrow it with longitude/latitude bounds. Coordinates are inferred
annotations, not proof that hardware sat at a precise point.

`caida_itdk.itdk_router_hostnames` — DNS PTR names for interface addresses, where records existed.

| Column | Type | Meaning |
| --- | --- | --- |
| `ip` | `inet` | IPv4 or IPv6 interface address. |
| `hostname` | `text` | PTR hostname for that address. |

Primary key `(ip, hostname)`; hostname lookup indexed. An absent result is not proof the interface
does not exist. Hostnames can be stale, and location-like substrings are operator conventions.

These four are different views of measured or inferred evidence, not a one-row-per-router record.
**`node_id` is the router-level join key.** `endpoint_token` is evidence about an interface, not a
substitute for the normalized key.

### Limitations to carry into every answer

- Topology reflects one measurement campaign's visible paths, not all Internet paths.
- Alias resolution can group interfaces incorrectly, or fail to group ones that belong together.
- An inferred link reveals no direction, capacity, utilization, ownership, contract, or currency.
- AS and geolocation assignments are method-dependent inferences with provenance.
- Missing rows and null fields mean unavailable evidence, not a confirmed negative fact.
- Counts describe the snapshot and your filters; do not generalize them to the whole Internet.

---

## 2. MCP: the tool contract

An MCP client opens a session with a server, asks what tools exist, and calls one with a JSON
object. The server owns the mapping from analytical intent to data access:

```text
client -> tools/list -> tool definitions
client -> tools/call(name, arguments) -> validation -> repository -> CSV
client <- structured result metadata <- server
```

A general SQL interface would let a caller choose tables, projections, joins, and expensive or
unsafe operations. This server instead exposes a small vocabulary of intents ("find nodes assigned
to this ASN"). That boundary is both an analytical design choice and a security control.

**Discovery.** `tools/list` returns `name`, `description`, `inputSchema`, `outputSchema`, and
annotations (read-only, non-destructive, idempotent, closed-world). An agent picks a tool from the
name and description, so those must distinguish similar operations — and must state what a tool
*excludes*.

**Restrictive input schemas.** Every input is a JSON Schema Draft 2020-12 object with
`additionalProperties: false`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "properties": {"sample_id": {"type": "integer", "minimum": 1}},
  "required": ["sample_id"]
}
```

JSON types are exact: `64500` is an integer, `"64500"` is a string. Application-level validation
still handles rules a schema cannot express (finite coordinates, min ≤ max, parsing an IP).

> **Gotcha:** `oneOf` means *exactly one* branch validates — not "one or more". Design the branches
> and the `additionalProperties` rule together, then test zero, one, and multiple selectors.

**Layer responsibilities.** All five must agree for a tool to be complete:

| Layer | Owns | Does not own |
| --- | --- | --- |
| Tool definition | name, description, JSON schemas, annotations | SQL text |
| Validation | input shape and cross-field rules | database access |
| Dispatch | known tool-to-implementation mapping | caller-selected code paths |
| Query | fixed SQL, bound parameters, columns, ordering | arbitrary client query structure |
| Executor/writer | connection use, streaming, atomic CSV output | analytical meaning |

**Structured CSV results.** A successful call returns exactly three fields:

```json
{
  "file_path": "/app/outputs/example_unique-id.csv",
  "row_count": 3,
  "columns": [{"name": "node_id", "type": "string"}, {"name": "asn", "type": "int64"}]
}
```

`columns` is ordered metadata, not data. `file_path` is a path inside the server container; your
deployment maps it into the notebook. Allowed column types: `string`, `inet`, `int32`, `int64`,
`float64`. An empty result is a *success* with `row_count: 0` — different from an error.

**Safe failures.** Invalid names or arguments produce `INVALID_ARGUMENT`; unexpected execution
failures produce `INTERNAL_ERROR`. Neither exposes SQL, stack traces, or credentials.

### The seven tools

| Tool | Provided | Returned columns | Stable order |
| --- | --- | --- | --- |
| `get_link_endpoints` | complete | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `endpoint_ordinal` |
| `find_nodes_by_asn` | complete | `node_id`, `asn`, `method` | `node_id` |
| `search_nodes_by_geolocation` | complete | `node_id`, `continent`, `country`, `region`, `city`, `latitude`, `longitude`, `method` | `country`, longitude/latitude nulls first, `node_id` |
| `lookup_router_hostnames` | complete | `ip`, `hostname` | by IP: `ip`, hostname nulls first; by name/prefix: `hostname`, `ip` |
| `get_node_geolocation` | **you build** | `node_id`, `continent`, `country`, `region`, `city`, `latitude`, `longitude`, `method` | `node_id` |
| `find_router_links_between_asns` | **you build** | `link_id`, `node_a`, `node_b` | `link_id`, `node_a`, `node_b` |
| `count_nodes_by_asn_and_country` | **you build** | `country`, `node_count` (DISTINCT node_id per country) | `node_count` DESC, `country` |

These projections and orderings are part of the public contract. A tool must not accept
caller-chosen tables, columns, joins, ordering, SQL fragments, limits, or cursors.

---

## 3. Safe query rules

1. **Fix the query shape in source code**: schema and relation, projected columns, joins,
   predicates, sort keys and null ordering, output column names/types, filename prefix. Inputs
   choose only documented *values* — one ASN, country, bound, node ID, link ID, IP, or selector.
2. **Bind values separately.** In psycopg, placeholders are `%s` regardless of Python type:

   ```python
   statement = sql.SQL("SELECT sample_id, label FROM teaching.example WHERE sample_id = %s ORDER BY sample_id")
   parameters = (sample_id,)
   ```

   Never use concatenation, f-strings, `.format()`, or your own quoting.
   > **Gotcha:** a placeholder binds a *value*, not an identifier. This assignment never needs
   > caller-chosen tables or columns.
3. **Project and order explicitly.** No `SELECT *`. Relational results have no order without
   `ORDER BY`; when nullable columns participate, state `NULLS FIRST`/`NULLS LAST`.
4. **Start from an indexed predicate.** `asn` for AS lookups, `find_router_links_between_asns`,
   and `count_nodes_by_asn_and_country`; `country` (first in the composite index) for geolocation;
   `link_id` for endpoints; `node_id` (primary key) for `get_node_geolocation`.
5. **Validate numeric bounds twice.** Schema expresses ranges (longitude `[-180,180]`, latitude
   `[-90,90]`); the application must also reject non-finite values and inverted min/max pairs.
6. **Make selectors mutually exclusive.** Hostname lookup takes exactly one of `ip`,
   `hostname_exact`, or `hostname_prefix`. Reject zero, two, three, and extra properties.
7. **Escape literal prefixes.** In `LIKE`, `%`, `_`, and `\` are special. Escape backslash, then
   `%`, then `_`; append the server-owned `%`; use an explicit `ESCAPE` clause. A caller asking for
   `lab_5%\edge` wants literal text, not a wider search.
8. **Keep every layer narrow**: a small tool allowlist, restrictive schemas plus application
   validation, fixed parameterized `SELECT`s, narrow method signatures, a `SELECT`-only database
   role, statement timeouts and conservative pools, and generic public errors with sanitized logs.

**Review checklist for each query you write:** Is every keyword, relation, column, predicate,
join, and ordering choice package-owned? Are all caller values bound? Does it start from the
intended indexable filter? Do the selected columns and column metadata match exactly, in order? Is
the order deterministic including nulls? Can an invalid selector reach the executor? Does a prefix
containing `%`, `_`, or `\` stay literal? Can the operation write, or leak internal errors?

---

## 4. Where your code goes

All three new tools live in **one file**: `src/itdk_mcp/student_tools.py`. It holds

- `STUDENT_TOOL_SCHEMAS` — the three restrictive JSON Schemas (reuse the `IDENTIFIER_SCHEMA` and
  `ASN_SCHEMA` shapes already defined at the top of that file);
- `STUDENT_TOOL_DESCRIPTIONS` — one precise description per tool;
- the three `Query` objects plus `get_node_geolocation(executor, node_id)`,
  `find_router_links_between_asns(executor, asn_a, asn_b)`,
  `count_nodes_by_asn_and_country(executor, asn)`; and
- a complete `dispatch(executor, name, arguments)` you do not need to edit.

`mcp_tools.py` merges your schemas and descriptions into `TOOL_SCHEMAS`/`TOOL_DESCRIPTIONS` and
routes any call naming one of the three through `dispatch`, so a tool becomes discoverable and
callable as soon as you fill in the file. You do not edit the completed server code.

These three tools are deliberately **general-purpose**, not single-question probes: each takes
only a `node_id` or one/two `asn` values and returns raw rows, so an agent (or your own notebook
code) combines them to answer many different questions -- which node sits where, which two ASes
share a router-level link, how one AS's routers are spread across countries -- rather than each
tool answering exactly one fixed question. Part 3's Q8/Q9 ask you to use that generality directly.

### Contract 1 — `get_node_geolocation`

Args `node_id`; returns zero or one row of `node_id, continent, country, region, city, latitude,
longitude, method`; order `node_id`; seed `node_id` (primary key of
`itdk_node_geolocation`).

```sql
SELECT node_id, continent, country, region, city, latitude, longitude, method
FROM caida_itdk.itdk_node_geolocation
WHERE node_id = %s
ORDER BY node_id
```

None of the four provided tools can answer "where is this specific node located" --
`search_nodes_by_geolocation` only takes a `country` (plus optional coordinate bounds), never a
`node_id`. This tool fills exactly that gap: given a `node_id` returned by `find_nodes_by_asn`,
`get_link_endpoints`, or `find_router_links_between_asns`, look up its one geolocation annotation.
Zero rows means "this snapshot has no geolocation annotation for this node" -- not an error, and
not proof the router doesn't exist.

### Contract 2 — `find_router_links_between_asns`

Args `asn_a`, `asn_b`; returns `link_id, node_a, node_b`; order `link_id, node_a, node_b`; seed
`asn` (indexed) via two CTEs, then a self-join on `link_id`.

```sql
WITH a_nodes AS (
    SELECT node_id FROM caida_itdk.itdk_node_as WHERE asn = %s
),
b_nodes AS (
    SELECT node_id FROM caida_itdk.itdk_node_as WHERE asn = %s
)
SELECT e1.link_id, e1.node_id AS node_a, e2.node_id AS node_b
FROM caida_itdk.itdk_link_endpoints e1
JOIN a_nodes ON a_nodes.node_id = e1.node_id
JOIN caida_itdk.itdk_link_endpoints e2
  ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
JOIN b_nodes ON b_nodes.node_id = e2.node_id
ORDER BY e1.link_id, node_a, node_b
```

This is the general form of "find border routers between AS *X* and AS *Y*": pass any two ASNs
and get back every router-level link with one endpoint's node assigned to `asn_a` and the other's
to `asn_b`. Part 1's Q1 asks the identical question by hand for Level3/Netflix; here it becomes a
reusable tool an agent can call for any AS pair -- including the 18-AS sweep in Part 1's Q3, or a
smaller version of it in Part 3.

> **Design choice, not a bug: passing `asn_a == asn_b` is allowed.** It returns links where *both*
> endpoints belong to the same AS -- that AS's own intra-network router-level mesh, a legitimate
> and distinct question, not an error. Say so in the tool description so a caller isn't surprised.

> **What this tool does not dedupe.** A link with more than two endpoints (a "hyperlink", see
> §1) can contribute more than one `(node_a, node_b)` row if several of its endpoints belong to
> the two ASes in question -- each such pair is a real, distinct adjacency recorded on that link,
> not a duplicate. Do not silently drop rows from a link with unusual endpoint counts; flag them.

### Contract 3 — `count_nodes_by_asn_and_country`

Args `asn` (same tightened integer schema as `find_nodes_by_asn`); returns `country, node_count`;
order `node_count DESC, country`; seed `asn` (indexed).

```sql
SELECT g.country, COUNT(DISTINCT a.node_id) AS node_count
FROM caida_itdk.itdk_node_as a
JOIN caida_itdk.itdk_node_geolocation g ON g.node_id = a.node_id
WHERE a.asn = %s
GROUP BY g.country
ORDER BY node_count DESC, country
```

This is the general form of Part 1's Q2 country-concentration table for one AS: how many of its
geolocated routers sit in each country, busiest first. Calling it once per AS and comparing the
two result tables in pandas (as Part 1's `_by_country` helper does directly in SQL) reproduces
the China-Unicom-vs-Level3 comparison through the MCP tool layer instead.

> **INNER-join tradeoff.** The join to `itdk_node_geolocation` is an INNER join, so a node with an
> AS assignment but no geolocation row is excluded from every country's count -- it does not
> silently attribute to some fallback country. This tool answers "how is this AS's *geolocated*
> footprint distributed", not "how many routers does this AS have in total"; compare the sum of
> `node_count` here against `find_nodes_by_asn`'s `row_count` to see how much coverage that INNER
> join drops for a given AS.

---

## 5. Testing

Use the narrowest layer that can prove each requirement:

| Layer | What it proves | Dependencies |
| --- | --- | --- |
| Schema | discovery advertises exact names, required inputs, types, bounds, no extra properties | none |
| Validation/dispatch | valid calls reach the right implementation; invalid calls return a stable error and never dispatch | fake repositories |
| Query | SQL shape, parameter tuple, projection metadata, filename prefix, ordering | recording executor |
| Database integration | the fixed statement runs against the fixture with real types and order | fixture PostgreSQL |
| MCP end to end | discovery and a call work through transport/auth/session and produce readable CSV metadata | running scaffold |

Name the behaviour, not the implementation (`test_hostname_prefix_treats_percent_literally`, not
`test_replace_called_three_times`). Cover equivalence classes, not one happy path: minimum/
ordinary/maximum values, just-below and just-above bounds, wrong JSON types including numeric
strings, missing required and unexpected extra properties, zero/one/multiple selectors, IPv4 and
IPv6 and a string that only resembles an IP. When validation fails, assert both the error code and
that no query ran. A recording executor lets you check that caller data appears only in the
parameter tuple, that the projection matches the documented columns, and that `ORDER BY` is explicit.

Run:

```bash
uv run pytest                                  # everything
uv run pytest tests/test_student_tools.py -q   # just your three tools
```

`tests/test_completed_infrastructure.py` covers the four provided tools and should already pass.
`tests/test_student_tools.py` is the executable specification for your three; it carries a
module-level `xfail` marker that you remove once you implement them. **You must add at least one
meaningful test of your own per tool** to that file (see Q6).

---

## 6. Calling the tools from an agent, in the notebook

Parts 2 and 3 drive a real agent from this notebook using an **OpenAI-compatible endpoint** (NRP
Nautilus by default), so you are not limited by needing your own Claude subscription or API key.
That endpoint has no equivalent of a server-side remote-MCP connector, so the notebook's third
"Complete setup" cell implements the loop itself: it sends the model a standard OpenAI-style
`tools` list built from `list_itdk_tools()`, executes any `tool_calls` the model requests against
this MCP server directly (via `call_itdk_raw`), feeds the results back as `role: "tool"` messages,
and repeats until the model stops asking for tools. There is no separate agent process and no
desktop app -- and, unlike a server-side connector, the model itself never needs network access to
the MCP server, only this notebook process does.

`await call_agent_with_mcp_tools(prompt)` returns `(trace, answer)`: `trace` is one record per
tool call / tool result pair -- built from the same `mcp_tool_use`-shaped call and
`mcp_tool_result`-shaped outcome you would audit from a server-side connector -- and `answer` is
the model's final text. Two things this needs, both set in `itdk_mcp_credentials.env`:
`OPENAI_API_KEY` (your NRP Nautilus key or another OpenAI-compatible provider's) and
`OPENAI_BASE_URL` (for NRP Nautilus, `https://ellm.nrp-nautilus.io/v1`). Never paste either into
the notebook or commit them.

Model choice matters here more than it would with a single frontier model: NRP Nautilus's catalog
(`GET {OPENAI_BASE_URL}/models`) includes several open-weight models of noticeably different
tool-calling reliability. In testing, `kimi` completed both fixed prompts cleanly in a couple of
tool calls each; a weaker model can go off track -- for example, guessing at countries one at a
time when a question requires a lookup no tool provides, or exhausting its token budget mid-answer
without ever emitting a final response. That is not a bug in your setup; it is exactly the kind of
agent behaviour Q5 asks you to audit. Set `ITDK_AGENT_MODEL` to whichever model you use, and note
which one you picked alongside your trace.

**An agent cannot make weak evidence stronger.** Treat its prose as a hypothesis to audit. A
defensible answer records: the exact tool name and arguments; the returned artifact and row count;
the transformation used for any summary; the rows or aggregate supporting each claim; and at least
one limitation or alternative explanation. The grade attaches to reproducible evidence and your
judgement, not to how convincing the agent's wording is.

---

## Part 1 — Investigate real ASes with direct SQL (Q1–Q3)

Part 1 is the **only** part that touches the database directly. It connects straight to the real
teaching snapshot with the read-only role your instructor hands out (`db_credentials.env` holds
the DSN) -- **this path is never a substitute for MCP access in Parts 2 and 3**, and its full
flexibility is precisely why it can ask harder questions than Parts 2/3 can.

Use `pandas.read_sql` with bound parameters (`%(name)s` plus `params=`), not f-strings — the same
habit Part 3 requires of your tools.

### Q1 — Border routers between Level3 (AS3356) and Netflix (AS2906)

A router-level link with one endpoint's node assigned to AS3356 (Level3, a transit ISP) and the
other to AS2906 (Netflix, a content provider) is a **border router pair**: the physical point
where one AS hands traffic to the other. Build the set with a CTE per AS (each already enriched
with geolocation) joined on `link_id`:

```sql
WITH level3_nodes AS (
    SELECT le.link_id, le.node_id AS l3_node_id,
           g.latitude AS l3_lat, g.longitude AS l3_lon, g.city AS l3_city, g.country AS l3_country
    FROM caida_itdk.itdk_link_endpoints le
    JOIN caida_itdk.itdk_node_as na ON le.node_id = na.node_id
    JOIN caida_itdk.itdk_node_geolocation g ON le.node_id = g.node_id
    WHERE na.asn = 3356
),
netflix_nodes AS (
    -- student_code_start: identical shape, filtered to asn = 2906 and aliased nf_*
    -- student_code_end
)
SELECT l3.link_id, l3.l3_node_id, l3.l3_lat, l3.l3_lon, l3.l3_city, l3.l3_country,
       n.nf_node_id, n.nf_lat, n.nf_lon, n.nf_city, n.nf_country
FROM level3_nodes l3
JOIN netflix_nodes n ON l3.link_id = n.link_id;
```

This returns roughly 130 links with geolocation on both ends. Compute the great-circle distance
between each link's two endpoints with the haversine formula, and classify each link as
**geographically adjacent** (`<= 40 km`) or not. Because latency roughly tracks physical distance,
legitimate peering links cluster in the same metro area; an implausibly large distance is more
likely a geolocation error than a genuine transoceanic router adjacency (a Hoiho-geolocated
endpoint paired with a Maxmind-geolocated one is a common source of that error). Then, restricting
to the adjacent links only, group by city/country and count distinct links per location to find
the distinct peering locations.

> **Q1** (a) How many links are adjacent vs. non-adjacent? List the non-adjacent link IDs. (b) For
> adjacent links only, present the `city, country, link_count` peering-location table. (c) One
> paragraph: why would an ISP and a content provider prefer to peer in the same metro area, and are
> the non-adjacent outliers real long-haul links or likely geolocation artifacts?

### Q2 — Router concentration: China Unicom (AS4837) vs. Level3 (AS3356)

Count each AS's geolocated routers per country in one round trip:

```sql
SELECT na.asn, g.country, COUNT(DISTINCT na.node_id) AS node_count
FROM caida_itdk.itdk_node_as na
JOIN caida_itdk.itdk_node_geolocation g ON g.node_id = na.node_id
WHERE na.asn IN (4837, 3356)
GROUP BY na.asn, g.country
```

For each ASN, add a `rank` (0 = most routers, ties share a rank, the next rank skips the tied
count -- `RANK()`-style, not `DENSE_RANK()`) and a `pct` (that country's share of the AS's own
geolocated total). Build a `comparison` table with columns
`country_name, cu_num_router, cu_rank, cu_pct, l3_pct, l3_rank, l3_num_routers` for China Unicom's
top 10 countries, with Level3's figures for those same countries alongside (use `pycountry` to map
the two-letter code to a country name; a country with zero Level3 routers gets `l3_pct = 0` and a
rank below every ranked country). As of this writing, China Unicom has roughly 49.4k geolocated
routers across 21 countries (about 98% of them in `CN`); Level3 has roughly 29.6k across 53
countries (its largest single share, in `US`, is about 89%) -- expect numbers in that neighborhood,
not identical to the letter, since the snapshot may have moved since this was written.

Then, for China Unicom's **US West Coast** routers only (`asn = 4837`, `country = 'US'`,
`longitude < -115`), find every other AS that shares a router-level link with one of them, using a
self-join on `link_id` plus a `LEFT JOIN` to `itdk_router_hostnames` for the peer interface's
hostname where one exists. Build a `city, total, <peer ASN columns...>` table: `total` is the
count of *distinct* West Coast China Unicom routers with at least one peer in that city (not the
sum of the peer columns -- a router with several peers is one router, counted once), and each peer
column is the count of distinct routers connecting to that peer ASN in that city.

> **Q2** (a) Compare China Unicom's and Level3's country concentration; what business-model
> difference explains it? (b) Which AS has more total routers, and why? (c) Present the West Coast
> peering table. (d) One paragraph: why would China Unicom peer with the **same** AS more than once
> in one city, and why with the same AS across **different** cities?

### Q3 — Interconnection structure across 18 major ASes

Using the 18-AS list (11 transit ISPs, 2 CDNs, 5 content networks -- see the notebook for the
exact table with ASN, name, and category code), count router-level links between every pair:

```sql
WITH le_as AS (
    SELECT DISTINCT le.link_id, na.asn
    FROM caida_itdk.itdk_link_endpoints le
    JOIN caida_itdk.itdk_node_as na ON na.node_id = le.node_id
    WHERE na.asn IN (174, 701, 1299, 3257, 3491, 5511, 6453, 3320, 6461, 6762, 6830,
                      12956, 15133, 20940, 714, 2906, 13335, 15169)
)
SELECT a.asn AS asn1, b.asn AS asn2, COUNT(*) AS link_count
FROM le_as a
JOIN le_as b ON b.link_id = a.link_id AND a.asn < b.asn
GROUP BY a.asn, b.asn
ORDER BY link_count DESC
```

`DISTINCT` in the CTE collapses the grain to one row per `(link, AS)` before the self-join, so a
link with several endpoints in the same AS does not fan out; `a.asn < b.asn` keeps each unordered
pair counted once. Render the resulting matrix as a heatmap (`imshow` with a log color scale reads
better than a linear one, given the wide range of link counts). Reordering the 18 ASes so
heavily-interconnected ones sit next to each other -- a linear-arrangement/seriation problem -- 
makes the structure easier to read than the arbitrary category/ASN order; the notebook uses
`scipy.optimize.quadratic_assignment` with several randomized restarts for this (a single
default-start call can land in a mediocre local optimum).

> **Q3** In two paragraphs: which AS categories are most/least interconnected, which ASes (if any)
> don't match their category's typical behavior, and what does that say about how the Internet is
> structured economically?

---

## Part 2 — Use the four provided tools through an agent (Q4–Q5)

The four provided tools ship complete; nothing needs implementing before you can use them. The
notebook runs **two fixed prompts** verbatim through `call_agent_with_mcp_tools`, seeded on
**AS15133 (Edgecast)** -- a real AS with exactly two geolocated router nodes in this snapshot, small
enough that every claim in the trace is checkable by hand. Run the cells, then audit what came back.

- **Prompt A (ASN → geolocation):** "Which router nodes does this snapshot assign to ASN 15133,
  where is each of those nodes geolocated, and which inference method produced each AS assignment
  and each location? Use the ITDK MCP tools; report the exact tool calls, arguments, and row counts
  you used."
- **Prompt B (hostname ↔ geolocation provenance):** "For the router nodes assigned to ASN 15133,
  find the PTR hostname of each node's known interface and compare any location hint embedded in
  that hostname against the recorded geolocation for nodes in the US. State which method produced
  each location and whether the hostname is independent evidence."

**Use `kimi` as `ITDK_AGENT_MODEL`** (the default in `itdk_mcp_credentials.env.example`, and set
`temperature=0` in `call_agent_with_mcp_tools`, already the cell's default) -- it was the most
reliable tool-caller of NRP Nautilus's catalog in testing; a weaker model is more likely to stall
or guess rather than answer cleanly, which makes Q4/Q5 harder to answer, not more interesting.

There is a fixed, guaranteed gap regardless of model: **none of the four provided tools can look up
a node's location directly by `node_id`** -- `search_nodes_by_geolocation` only takes a `country`.
Every run must confront this gap one way or another; that is Q5's anchor finding.

For each run, keep the trace (`mcp_tool_use`-shaped call + `mcp_tool_result`-shaped outcome) and
the final answer with your submission — they are the artifacts Q4 and Q5 grade.

> **Q4** Pick one fixed prompt. Re-run its tool calls yourself through `call_itdk_tool` /
> `load_tool_csv` and re-derive each number the agent reported. List which of its claims held, which
> didn't, and the evidence for each.

> **Q5** Explain how the agent handled the missing node-location lookup (guessed at countries,
> stated it couldn't determine location, or something else) -- quote the trace. Then name one more
> issue from either run: a redundant call, or a claim no tool result actually supports. What one
> change to the tool descriptions (or one new tool) would have prevented it?

---

## Part 3 — Build three new general-purpose tools, then investigate with all seven (Q6–Q9)

Implement the three contracts from §4 in `src/itdk_mcp/student_tools.py`, add tests, then re-run
the same in-notebook agent pattern against all seven tools. Every question below stays seeded on
small, real ASes so every returned row is small enough to check by hand.

### Q6 — Trace one new tool end to end

> **Q6** Show `get_node_geolocation`'s discovered contract (name, description, input/output schema),
> one valid call (a node from `find_nodes_by_asn(15133)`), and one invalid call. Which layer rejects
> the invalid call, and how do you know it never reached the query? Does the valid call's row match
> your Part 1 SQL for that node? Name your single most useful new test and the bug it would catch.

You must add at least one meaningful test per tool to `tests/test_student_tools.py` and remove the
module-level `xfail` marker once the tools are implemented.

### Q7 — The `find_router_links_between_asns` tradeoffs

> **Q7** Call `find_router_links_between_asns(15133, 1299)` and show the rows where one `link_id`
> appears more than once with a different `node_b` -- a multi-endpoint "hyperlink" contributing more
> than one row, not a duplicate. Then call it with `asn_a = asn_b = 15133` and explain in one or two
> sentences why that should return Edgecast's own intra-network links rather than an error.

### Q8 — From a seed ASN to its neighbors

The notebook sends two more fixed prompts, now with all seven tools attached, still seeded on
**AS15133 (Edgecast)**:

- **Prompt C:** "For ASN 15133, list every router node assigned to it, the assignment method for
  each, and each node's geolocation. Then, for AS15133 paired with AS174 (Cogent) and again with
  AS1299 (Arelion), report every router-level link between them. State the row count of every tool
  call you make."
- **Prompt D:** "Starting from ASN 15133, connect what you can: its router nodes, their
  geolocations, their PTR hostnames, and every router-level link they share with AS174 or AS1299.
  Then give a short interpretation of what this evidence does and does not establish."

> **Q8** How many router nodes does ASN 15133 return, and what assignment method(s)? Pick one other
> AS and compare its `count_nodes_by_asn_and_country` total against its `find_nodes_by_asn` row
> count -- do they match? If not, what does the gap mean? Name one record from this investigation
> that needs special care (a multi-endpoint link, a node missing geolocation, or a missing PTR).

### Q9 — Evidence table and audit

Build a reproducible evidence table starting from ASN 15133, using only MCP tools, and preserve
every call record (tool, arguments, artifact, row count, columns, transformation applied
afterwards). Merge only on documented keys (`node_id`, `asn`, `ip`); preserve unmatched rows rather
than manufacturing a link.

Then split Prompt D's answer into individual factual claims and mark each one:

- **supported** — the cited artifact and your transformation establish it;
- **underspecified** — plausible, but missing the snapshot, grain, method, or filter;
- **overstated** — stronger than the evidence, e.g. an inference stated as certainty, or a router
  adjacency described as a business relationship;
- **unsupported** — no captured artifact establishes it.

> **Q9** Present your evidence table and the claim audit. Identify at least one claim that is
> overstated, unsupported, or missing an essential limitation, and correct it. If every claim is
> supported, name the most important omitted limitation instead of inventing an error.

---

## Glossary

- **Node** — an ITDK router inferred by grouping interface addresses that likely belong to one
  device. An inference, not a confirmed device.
- **Link** — an inferred router-level adjacency. Some links have more than two endpoints
  ("hyperlinks") -- treat each as a genuine multi-endpoint observation, not a broken pair, and
  don't silently collapse the extra endpoints when counting.
- **ASN** — the numeric identifier of an Autonomous System (a network under one routing policy).
- **Border router** — one of the two (or more) routers on an inferred link whose endpoints belong
  to *different* ASes -- the physical point at which one AS hands traffic to another. An inferred
  adjacency, not proof of a business peering agreement, capacity, or traffic volume.
- **`endpoint_token` vs. `node_id`** — `endpoint_token` is the raw source encoding of one endpoint
  (sometimes `node:interface`, sometimes bare); `node_id` is the normalized router key every
  relation agrees on. Join on `node_id`; treat `endpoint_token` as evidence about an interface.
- **Teaching snapshot vs. fixture** — the *teaching snapshot* is the real, instructor-provisioned
  read-only role on the shared CAIDA ITDK database, and is the target of every graded question; the
  *fixture* (`nids-itdk-mcp-synthetic-v1`) is a small invented local dataset that exists only so
  `uv run pytest` has something deterministic to run against while you develop
  `student_tools.py`. Never answer a graded question from the fixture.

---

[README](README.md) | Assignment | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)
