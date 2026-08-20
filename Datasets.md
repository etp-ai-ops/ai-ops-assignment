[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Datasets

## The ITDK Teaching Snapshot

The graded analysis uses a frozen, instructor-prepared ITDK snapshot or approved representative teaching subset. The exact release identifier, source manifest, subset procedure, checksums, and seed identifiers are deployment decisions and are not known in this repository draft. Your instructor must provide them before you start Task 4. Record the supplied snapshot identifier in the notebook so another reader can tell which data your answers describe.

For fast local tests, the repository provisions the deterministic synthetic fixture `nids-itdk-mcp-synthetic-v1`, documented in [data/README.md](data/README.md) and `data/fixture-manifest.json`. It contains six invented nodes, six links (including multi-endpoint examples), eight AS-assignment rows, six geolocation rows, and eleven hostname rows. Its documented seeds use private-use teaching ASNs, reserved documentation IP ranges, and `.test` hostnames. Fixture values teach behavior and edge cases; they are not measurements of the public Internet and must not be used as evidence about real topology.

The starter notebook currently uses this synthetic fixture for its reproducible exercises. Before an instructor treats Task 4 as analysis of real ITDK topology, they must replace or supplement those seeds with a legally approved frozen teaching snapshot, publish its manifest, and preflight every required query. Until that happens, Task 4 answers describe only the synthetic fixture and must say so explicitly.

ITDK data may be access-controlled. Do not copy database contents into Git, publish generated CSVs, or redistribute snapshot rows unless your course's data terms explicitly allow it.

## Access Through the MCP Server

The database role is read-only and has `SELECT` access only to the four relations below. Students investigate the graded snapshot through the MCP server, not by opening a direct SQL connection. The one exception is Task 1, which deliberately opens a direct connection to the local synthetic fixture — see [Direct SQL Access for Exploration (Task 1 Only)](#direct-sql-access-for-exploration-task-1-only) below. The server returns metadata with this shape:

```json
{
  "file_path": "/app/outputs/tool_name_unique-id.csv",
  "row_count": 12,
  "columns": [
    {"name": "example", "type": "string"}
  ]
}
```

`file_path` is a path inside the server/consumer environment, not a public download URL. Your course deployment must mount or map the output directory so the notebook can read the returned path. The exact host path, retention period, quota, and cleanup procedure are instructor-supplied deployment settings.

## Direct SQL Access for Exploration (Task 1 Only)

Docker Compose also publishes the fixture PostgreSQL service directly to the host, on `127.0.0.1:${ITDK_DB_PORT:-5433}` by default, reusing the same read-only `itdk_reader` role already created for the MCP server's own connection (`SELECT`-only on all four relations, see `data/initdb/001_schema_fixture.sql`). A new `db_credentials.env.example` at the repository root documents its DSN.

This path exists for exactly one purpose: letting [Task 1](Task-1-sql-exploration.md) explore the local synthetic fixture with hand-written SQL, the way the prerequisite ITDK assignment teaches direct querying. Two rules keep this from undermining the rest of the assignment:

- **This path reaches only the local synthetic fixture used for practice.** It is never wired to the frozen graded teaching snapshot, and no course deployment should make it reach that snapshot.
- **Task 4's graded investigation must still go entirely through MCP tools, not direct SQL.** The whole point of Tasks 2 through 4 is investigating through the tool boundary you connect to and extend; querying the graded snapshot directly would bypass the exact interface this assignment teaches you to build and use.

If your course deployment changes this default port or DSN shape, the instructor handout takes precedence over the values shown here.

## Relation: `caida_itdk.itdk_link_endpoints`

This relation maps an inferred link to its endpoint records.

| Column | PostgreSQL type | Meaning |
| --- | --- | --- |
| `link_id` | `text` | Identifier shared by all endpoints of one inferred link. |
| `endpoint_ordinal` | `integer` | Position that distinguishes endpoint rows within a link. |
| `endpoint_token` | `text` | Source endpoint encoding retained for provenance; it may encode a node and observed interface. |
| `node_id` | `text` | Normalized router-node identifier used for joins and node filtering. |

The primary key is `(link_id, endpoint_ordinal)`, and `node_id` is indexed. The worked `get_link_endpoints` tool filters on `link_id` and orders by `endpoint_ordinal`. The student-built `find_links_for_node` (Task 3) filters on `node_id` and orders by `(link_id, endpoint_ordinal)`.

Most familiar links have two endpoints, but the model permits more. A bare or unusual `endpoint_token` must not be parsed as though every row contains an IP address. Use `node_id` to relate this table to node annotations.

## Relation: `caida_itdk.itdk_node_as`

This relation records router-node to ASN assignments.

| Column | PostgreSQL type | Meaning |
| --- | --- | --- |
| `node_id` | `text` | Router-node identifier. |
| `asn` | `bigint` | Assigned Autonomous System Number. |
| `method` | `text` | Method or provenance label for the assignment. |

The primary key is `(node_id, asn)`, and `asn` is indexed. A node can therefore have more than one assignment row. Do not silently choose one ASN or discard the `method` field. The required ASN tool filters on the indexed ASN and returns `(node_id, asn, method)` ordered by `node_id`.

## Relation: `caida_itdk.itdk_node_geolocation`

This relation records one supplied geolocation annotation per node in the classroom schema.

| Column | PostgreSQL type | Meaning |
| --- | --- | --- |
| `node_id` | `text` | Router-node identifier. |
| `continent` | `text` | Continent label. |
| `country` | `text` | Two-letter uppercase country code. |
| `region` | `text` | Region, state, or province when available. |
| `city` | `text` | City label when available. |
| `latitude` | `double precision` | Latitude in decimal degrees. |
| `longitude` | `double precision` | Longitude in decimal degrees. |
| `method` | `text` | Method or provenance label for the location. |

`node_id` is the primary key. The search index begins with `country` and then `longitude`, so every supported geolocation search requires a country and may narrow it with longitude and latitude bounds. Results order by `(country, longitude NULLS FIRST, latitude NULLS FIRST, node_id)`.

Coordinates are inferred annotations, not proof that hardware was physically present at a precise point. Interpret `method`, missing fields, measurement date, and agreement with other evidence before making a geographic claim.

## Relation: `caida_itdk.itdk_router_hostnames`

This relation records DNS PTR hostnames for router interface addresses when records were available.

| Column | PostgreSQL type | Meaning |
| --- | --- | --- |
| `ip` | `inet` | IPv4 or IPv6 interface address. |
| `hostname` | `text` | PTR hostname associated with the address. |

The primary key is `(ip, hostname)`, and hostname lookup is indexed. The assignment supports lookup by one IP, one exact hostname, or one literal hostname prefix. An absent result is not proof that the interface does not exist: the address may lack a PTR record, the record may have changed, or the snapshot may not contain it. Hostnames can be stale and location-like substrings are operator conventions rather than authoritative geography.

## Fixed Tool Projections

| Tool | Provided | Returned columns | Stable order |
| --- | --- | --- | --- |
| `get_link_endpoints` | complete | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `endpoint_ordinal` |
| `find_nodes_by_asn` | complete | `node_id`, `asn`, `method` | `node_id` |
| `search_nodes_by_geolocation` | complete | `node_id`, `continent`, `country`, `region`, `city`, `latitude`, `longitude`, `method` | `country`, longitude/latitude with nulls first, `node_id` |
| `lookup_router_hostnames` by IP | complete | `ip`, `hostname` | `ip`, hostname with nulls first |
| `lookup_router_hostnames` by exact name or prefix | complete | `ip`, `hostname` | `hostname`, `ip` |
| `find_links_for_node` | Task 3 (student-built) | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `link_id`, `endpoint_ordinal` |
| `find_peer_asns_for_node` | Task 3 (student-built) | `peer_node_id`, `peer_asn`, `peer_method` (distinct) | `peer_node_id`, `peer_asn` |
| `find_hostnames_for_asn` | Task 3 (student-built) | `node_id`, `ip`, `hostname` (distinct) | `node_id`, `ip` with nulls first, `hostname` |

The first four tools ship fully working so that Task 0's worked example and Task 2's agent investigation have a real, complete server to call. The final three are the tools you design and implement across all layers in Task 3, following the exact contracts in [Task 3 Guidance](Task-3-new-mcp-tools.md); Task 4's investigation then uses all seven together.

These projections and orderings are part of the public contract. A student tool must not accept caller-chosen tables, columns, joins, ordering, SQL fragments, limits, or cursors.

## Limitations to Carry Into Every Answer

- Topology reflects paths visible from a particular measurement campaign, not all possible Internet paths.
- Alias resolution can group interfaces incorrectly or fail to group interfaces that belong together.
- An inferred link does not reveal traffic direction, capacity, utilization, ownership, contractual relationship, or whether it still exists now.
- AS and geolocation assignments are method-dependent inferences with provenance.
- Missing rows and null fields mean unavailable evidence, not a confirmed negative fact.
- A hostname is a PTR observation that may be missing, stale, or operationally encoded.
- Counts describe the frozen teaching snapshot and selected filters; they should not be generalized to the whole Internet without justification.

[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
