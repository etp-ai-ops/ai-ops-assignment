[README](README.md) | Assignment | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)

# Building an MCP Interface for Internet Topology Data

Everything you need to know to complete [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb) is in this
one document: the data model, the MCP tool contract, the safe-query rules, the exact contracts
for the three tools you build, how testing works, and the nine graded questions.

**Learning objectives.** Explore CAIDA ITDK relations with direct SQL; use a working MCP server
through an agent; encode new analytical intents as restrictive JSON Schemas plus fixed,
parameterized, read-only SQL; test those contracts; and separate observed evidence from
inference when you report findings.

**Shape of the work.** Three parts, nine questions:

| Part | What you do | Access path | Questions |
| --- | --- | --- | --- |
| 1 | Explore the four relations with hand-written SQL | direct read-only SQL, local fixture only | Q1–Q3 |
| 2 | Use the 4 provided tools through an agent, in the notebook | OpenAI-compatible client-side tool loop + MCP | Q4–Q5 |
| 3 | Build 3 new tools, then investigate with all 7 | your code + the same agent cells | Q6–Q9 |

---

## 1. The data

### Teaching snapshot vs. synthetic fixture

Graded analysis is meant to run against a frozen, instructor-prepared **ITDK teaching snapshot**.
Its release identifier, manifest, checksums, and seeds are deployment decisions your instructor
supplies; record the snapshot ID in the notebook so a reader knows which data your answers describe.

Until an instructor publishes one, this repository ships the deterministic synthetic **fixture**
`nids-itdk-mcp-synthetic-v1` (see [data/README.md](data/README.md)): six invented nodes, six links
(including multi-endpoint ones), eight AS-assignment rows, six geolocation rows, eleven hostname
rows, private-use ASNs, reserved documentation IP ranges, and `.test` hostnames. Fixture values
teach behaviour and edge cases. **They are not measurements of the public Internet** — say so
explicitly in every answer that cites them.

ITDK data may be access-controlled. Do not commit database contents, generated CSVs, or snapshot
rows unless your course's data terms allow it.

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
| `find_links_for_node` | **you build** | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `link_id`, `endpoint_ordinal` |
| `find_peer_asns_for_node` | **you build** | `peer_node_id`, `peer_asn`, `peer_method` (DISTINCT) | `peer_node_id`, `peer_asn` |
| `find_hostnames_for_asn` | **you build** | `node_id`, `ip`, `hostname` (DISTINCT) | `node_id`, `ip` nulls first, `hostname` |

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
4. **Start from an indexed predicate.** `asn` for AS lookups and `find_hostnames_for_asn`;
   `country` (first in the composite index) for geolocation; `link_id` for endpoints; `node_id`
   for `find_links_for_node` and the `find_peer_asns_for_node` self-join.
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
- the three `Query` objects plus `find_links_for_node(executor, node_id)`,
  `find_peer_asns_for_node(executor, node_id)`, `find_hostnames_for_asn(executor, asn)`; and
- a complete `dispatch(executor, name, arguments)` you do not need to edit.

`mcp_tools.py` merges your schemas and descriptions into `TOOL_SCHEMAS`/`TOOL_DESCRIPTIONS` and
routes any call naming one of the three through `dispatch`, so a tool becomes discoverable and
callable as soon as you fill in the file. You do not edit the completed server code.

### Contract 1 — `find_links_for_node`

Args `node_id`; returns `link_id, endpoint_ordinal, endpoint_token, node_id`; order
`link_id, endpoint_ordinal`; seed `node_id` (indexed).

```sql
SELECT link_id, endpoint_ordinal, endpoint_token, node_id
FROM caida_itdk.itdk_link_endpoints
WHERE node_id = %s
ORDER BY link_id, endpoint_ordinal
```

Filtering endpoint rows by one node answers "which endpoint records contain this node?" — it does
*not* return every endpoint on those links. To see a node's neighbours at endpoint level, feed the
returned `link_id`s to `get_link_endpoints`. That two-step design keeps each tool's meaning precise.

### Contract 2 — `find_peer_asns_for_node`

Args `node_id`; returns DISTINCT `peer_node_id, peer_asn, peer_method`; order
`peer_node_id, peer_asn`; seed `node_id` via a self-join on `link_id`.

```sql
SELECT DISTINCT e2.node_id AS peer_node_id, a2.asn AS peer_asn, a2.method AS peer_method
FROM caida_itdk.itdk_link_endpoints e1
JOIN caida_itdk.itdk_link_endpoints e2
  ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
JOIN caida_itdk.itdk_node_as a2 ON a2.node_id = e2.node_id
WHERE e1.node_id = %s
ORDER BY peer_node_id, peer_asn
```

`DISTINCT` collapses the fan-out created when the seed node shares more than one link with the
same peer.

> **INNER-join tradeoff.** The join to `itdk_node_as` is an **INNER** join, so a peer node with no
> AS-assignment row is excluded entirely — it does not appear as `peer_asn = NULL`. Document that
> limitation in your tool *description*, not only in your notebook answer.

### Contract 3 — `find_hostnames_for_asn`

Args `asn` (same tightened integer schema as `find_nodes_by_asn`); returns DISTINCT
`node_id, ip, hostname`; order `node_id, ip NULLS FIRST, hostname`; seed `asn` (indexed).

```sql
SELECT DISTINCT le.node_id, h.ip, h.hostname
FROM caida_itdk.itdk_node_as a
JOIN caida_itdk.itdk_link_endpoints le ON le.node_id = a.node_id
JOIN caida_itdk.itdk_router_hostnames h
  ON h.ip = CASE WHEN strpos(le.endpoint_token, ':') > 0
                 THEN substring(le.endpoint_token FROM strpos(le.endpoint_token, ':') + 1)::inet
            END
WHERE a.asn = %s
ORDER BY le.node_id, h.ip NULLS FIRST, h.hostname
```

- `strpos(endpoint_token, ':')` finds the *first* colon; `substring(... FROM strpos(...) + 1)`
  takes everything after it, so the extracted text is the whole remainder of the token.
- The `CASE` yields `NULL` (not an error) for a bare token with no colon, like `L2`'s `N2`, so
  `::inet` never runs on an empty string.
- `::inet` casts the extracted text to Postgres's IP type for comparison with `h.ip`.

> **Gotcha — do not use `split_part` here.** `NULLIF(split_part(endpoint_token, ':', 2), '')::inet`
> is right when a token has *at most one* colon (`N1:192.0.2.1`) but silently breaks on IPv6:
> `split_part('N1:2001:db8:1::1', ':', 2)` returns `'2001'` — the text between the first and second
> colon — which then fails the `::inet` cast. `strpos`/`substring` split on the *position* of the
> first colon, so they handle any number of embedded colons. The lesson generalizes: don't assume a
> delimiter appears exactly once because your first examples only had one.

> **INNER-join tradeoff.** Both joins reaching `itdk_router_hostnames` are INNER joins, so an
> interface with no PTR record *and* a bare endpoint token with no embedded IP are excluded rather
> than returned with a null `hostname`. This tool answers "which hostnames are we confident belong
> to a node in this ASN?", not "does every node in this ASN have an interface?".

For ASN `64500` (nodes `N1`, `N2`) the fixture returns four rows: `N1`/`192.0.2.1`/
`edge-la.example.test`, `N1`/`2001:db8:1::1`/`v6-edge-la.example.test`, `N2`/`192.0.2.2`/
`edge-sea.example.test`, and `N2`/`2001:db8:2::2`/`v6-edge-sea.example.test` (from `N2`'s `L6`
endpoint). `L2`'s bare `N2` token is correctly absent, dropped by the INNER join.

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

Parts 2 and 3 run a **client-side tool-calling loop** against an OpenAI-compatible chat completions
endpoint (NRP Nautilus by default, so you aren't limited by needing your own Claude subscription or
API key). Unlike a server-side remote-MCP connector, this notebook process is what actually calls
your MCP server: it lists your tools, sends the model a standard `tools=[...]` list built from that
discovery call, executes whatever `tool_calls` the model requests against the MCP server itself, and
feeds each result back as a `role: "tool"` message -- repeating until the model stops asking for
tools. There is no separate agent process, no desktop app, and -- because the model never talks to
your MCP server directly -- no public tunnel or hosted URL is required either; only this notebook
process needs to reach it.

The notebook's third "Complete setup" cell defines `call_agent_with_mcp_tools(prompt)` for you. Each
turn of its loop looks like:

```python
response = await agent_client.chat.completions.create(
    model="gemma",                          # or another model your endpoint serves
    max_tokens=16384,
    messages=messages,
    tools=tool_specs,                       # built from list_itdk_tools()
)
```

and every `tool_calls` entry the model returns is executed via `call_itdk_raw(name, arguments)` --
the same MCP call your own audit cells make. The `trace` list `call_agent_with_mcp_tools` returns
pairs one `{"kind": "call", ...}` record with one `{"kind": "result", ...}` record per tool call --
that pair is what you record and audit. Two things this needs, both set in
`itdk_mcp_credentials.env`: `OPENAI_API_KEY` (your endpoint's key -- never commit it) and
`OPENAI_BASE_URL` (the endpoint's base URL).

**An agent cannot make weak evidence stronger.** Treat its prose as a hypothesis to audit. A
defensible answer records: the exact tool name and arguments; the returned artifact and row count;
the transformation used for any summary; the rows or aggregate supporting each claim; and at least
one limitation or alternative explanation. The grade attaches to reproducible evidence and your
judgement, not to how convincing the agent's wording is.

---

## Part 1 — Explore the ITDK relations with direct SQL (Q1–Q3)

Part 1 is the **only** part that touches the database directly. Docker Compose publishes the
fixture PostgreSQL service on `127.0.0.1:${ITDK_DB_PORT:-5433}` using the read-only `itdk_reader`
role (`SELECT` on the four relations, `default_transaction_read_only = on`); `db_credentials.env`
holds the DSN. **This path reaches only the local synthetic fixture, never a graded snapshot**, and
it is never a substitute for MCP access in Parts 2 and 3.

Use `pandas.read_sql` with bound parameters (`%(name)s` plus `params=`), not f-strings — the same
habit Part 3 requires of your tools.

### Q1 — Identifier roles and the join key

Run the endpoint rows for `L1`: `N1` at ordinal 0 with token `N1:192.0.2.1`, `N2` at ordinal 1 with
token `N2:192.0.2.2`. Annotate all four columns:

```text
link_id           -> groups endpoint rows into one inferred adjacency/hyperlink
endpoint_ordinal  -> distinguishes positions inside that link, not direction or path order
endpoint_token    -> preserves source endpoint encoding; sometimes carries an IP, sometimes not
node_id           -> normalized router identifier used across every router-level relation
```

Then look at `L2`: ordinal 0 has the bare token `N2` with no embedded IP, ordinal 1 has
`N3:198.51.100.3`. If you joined `itdk_node_as` on `endpoint_token` instead of `node_id`, the bare
`N2` token would match *by coincidence*, while every token carrying a prefix, punctuation, or no
colon would fail to join or join to the wrong thing — a silently wrong answer, which is worse than
an error.

> **Q1** Using concrete rows you returned, explain the roles of `link_id`, `endpoint_ordinal`,
> `endpoint_token`, and `node_id`. Which is the normal key for relating an endpoint to AS or
> geolocation rows, and what goes wrong when `endpoint_token` is used as though it were that key?
> Cite the two row counts from the correct and incorrect joins.

### Q2 — Multiplicity across relations

Name the grain first: one `itdk_link_endpoints` row is one endpoint position of one link; one
`itdk_node_as` row is one `(node_id, asn)` assignment; one `itdk_node_geolocation` row is one
location per node.

Two different one-to-many patterns are visible in the fixture. `N2` participates in three
link-endpoint rows (`L1`, `L2`, `L6`) *and* carries two AS-assignment rows (`64500` via `bdrmapit`,
`64501` via `alias-overlap`). Joining the two for `N2` without deduplicating yields `3 × 2 = 6`
rows, none of which is "the" AS for `N2`.

> **Q2** Show two different one-to-many patterns using your own counts. Why would flattening all
> annotations into one assumed row per router either lose information or multiply rows? Name the
> specific fixture nodes and links that break the assumption.

### Q3 — Provenance and missing evidence

`method` on `itdk_node_as` and `itdk_node_geolocation` records *how* a row was produced —
`bdrmapit`, `alias-overlap`, `maxmind`, `hostname-hint`, `country-only`. Keep it in every evidence
table: a value produced by an inference method is "assigned" or "inferred", never "proved". Note
also that a hostname-derived location and a hostname that appears to confirm it are **not**
independent evidence.

`N6`'s geolocation row returns `country = 'AU'`, `method = 'country-only'`, and null `region`,
`city`, `latitude`, `longitude`. The justified conclusion is only that this snapshot's process
produced nothing more precise for `N6`; the unjustified one is that `N6` has no more precise
real-world location, or that you may guess a city from the country. Other good missing-value cases:
`L2`'s bare `N2` token, or an IP such as `198.51.100.4` with no PTR row. Distinguish three states —
a query with no matching rows, a returned row with a null field, and a failed query. Only the last
is an execution problem.

> **Q3** What do the AS-assignment and geolocation `method` values communicate about how each row
> was produced? Contrast one AS method with one geolocation method. Then identify one missing value
> in the fixture (PTR, location detail, or interface encoding), state exactly what you can conclude
> from it and what tempting conclusion is *not* justified, and say which of these disappear
> silently under an INNER JOIN.

---

## Part 2 — Use the four provided tools through an agent (Q4–Q5)

The four provided tools ship complete; nothing needs implementing before you can use them. The
notebook runs **two fixed prompts** verbatim through `call_agent_with_mcp_tools`, using the
documented fixture seeds (ASN `64500`, countries `US` and `DE`, node `N1`). Run the cells, then
audit what came back.

- **Prompt A (ASN → geolocation):** "Which router nodes does this snapshot assign to ASN 64500,
  where is each of those nodes geolocated, and which inference method produced each AS assignment
  and each location? Use the ITDK MCP tools; report the exact tool calls, arguments, and row counts
  you used."
- **Prompt B (hostname ↔ geolocation provenance):** "For node N1, find the PTR hostname of its
  known IPv4 interface 192.0.2.1 and compare any location hint embedded in that hostname against
  the recorded geolocation for nodes in the US and DE. State which method produced each location
  and whether the hostname is independent evidence."

For each run, keep the trace (`mcp_tool_use` name + arguments, `mcp_tool_result` outcome) and the
final answer with your submission — they are the artifacts Q4 and Q5 grade.

> **Q4** Pick one of the two fixed prompts. Verify the agent's tool-call trace and every factual
> claim it made against your own repeat calls: re-run the calls that matter through
> `call_itdk_tool`, load the CSVs with `load_tool_csv`, and re-derive each number yourself. Report
> which claims held, which did not, and the exact evidence.

> **Q5** Critique the agent's *process* across both runs, not just its answers. Identify at least
> one redundant call (same tool and arguments when the result was already available) or one
> unverified assumption (a location, relationship, or completeness claim no tool result
> established), and say what a more careful trace would have looked like. What would you change
> about the tool descriptions so a future agent makes fewer of those mistakes?

---

## Part 3 — Build three new tools, then investigate with all seven (Q6–Q9)

Implement the three contracts from §4 in `src/itdk_mcp/student_tools.py`, add tests, then re-run
the same in-notebook agent pattern against all seven tools.

### Q6 — Trace one new tool end to end

> **Q6** Give the advertised contract for `find_links_for_node` (discovered name, description,
> input schema, output schema) and show one valid call and one invalid call. Which layer rejects
> the invalid call, and how do you know the invalid arguments never reached the query? Do the
> returned rows match what you saw in SQL in Part 1? Finally, name in one line the most useful test
> you added for your three tools and the concrete failure it would catch.

You must add at least one meaningful test per tool to `tests/test_student_tools.py` and remove the
module-level `xfail` marker once the tools are implemented.

### Q7 — The `find_peer_asns_for_node` tradeoffs

> **Q7** Explain the three design choices in `find_peer_asns_for_node`: the self-join on `link_id`,
> the `DISTINCT`, and the INNER join to `itdk_node_as`. What does each buy and what does each cost?
> Name the concrete rows in your result that demonstrate the fan-out `DISTINCT` collapses (not
> every node shows this — you may need to try more than one seed). Then check whether the INNER
> join actually excludes any peer in this fixture, e.g. by comparing against a LEFT JOIN variant of
> the same query. If it excludes one, show it; if it does not, explain why the tradeoff still
> matters for this tool's general contract, and describe what an excluded row would look like if
> the fixture had one.

### Q8 — From the seed ASN to a node's peers

The notebook sends two more fixed prompts, now with all seven tools attached, using the same seeds
(ASN `64500`, the two nodes it returns, countries `US`/`DE`, IP seed `192.0.2.1`):

- **Prompt C:** "For ASN 64500, list every router node assigned to it and the assignment method for
  each. Then, for the first two node IDs in the tool's stable order, report the peer nodes and peer
  ASNs. State the row count of every tool call you make."
- **Prompt D:** "Starting from the interface 192.0.2.1, connect what you can: the hostname, the
  node, that node's links and peers, its AS assignments, and its geolocation. Then give a short
  interpretation of what this evidence does and does not establish."

> **Q8** For seed ASN `64500`: how many distinct router nodes are returned and which assignment
> methods occur? Explain why this is a snapshot-specific assignment count rather than a complete
> current inventory of the AS. Then choose one returned node by a reproducible rule, report what
> `find_peer_asns_for_node` returns for it, and identify which records need special care — a link
> with other than two endpoint rows, an endpoint with no interface encoding, or a peer dropped by
> the INNER join.

### Q9 — Evidence table and audit

Build a reproducible evidence table from the IP/hostname seed, using only MCP tools, and preserve
every call record (tool, arguments, artifact, row count, columns, transformation applied
afterwards). Merge only on documented keys; preserve unmatched rows rather than manufacturing a
link. `find_hostnames_for_asn` can supply the whole name side for one ASN in a single call — if you
use it, say which interfaces it excluded and why.

Then split Prompt D's answer into individual factual claims and mark each one:

- **supported** — the cited artifact and your transformation establish it;
- **underspecified** — plausible, but missing the snapshot, grain, method, or filter;
- **overstated** — stronger than the evidence, e.g. an inference stated as certainty;
- **unsupported** — no captured artifact establishes it.

> **Q9** Present your evidence table and the claim audit. Identify at least one claim that is
> overstated, unsupported, or missing an essential limitation, and correct it. If every claim is
> supported, name the most important omitted limitation instead of inventing an error.

---

## Glossary

- **Node** — an ITDK router inferred by grouping interface addresses that likely belong to one
  device. An inference, not a confirmed device.
- **Link** — an inferred router-level adjacency. Some links have more than two endpoints.
- **ASN** — the numeric identifier of an Autonomous System (a network under one routing policy).
- **`endpoint_token` vs. `node_id`** — `endpoint_token` is the raw source encoding of one endpoint
  (sometimes `node:interface`, sometimes bare); `node_id` is the normalized router key every
  relation agrees on. Join on `node_id`; treat `endpoint_token` as evidence about an interface.
- **Teaching snapshot vs. fixture** — the *teaching snapshot* is the frozen, instructor-published
  ITDK subset used for graded analysis; the *fixture* (`nids-itdk-mcp-synthetic-v1`) is the
  invented local dataset used for Part 1, tests, and development. Fixture rows are not
  measurements of the public Internet.

---

[README](README.md) | Assignment | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)
