[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Datasets

## The ITDK Teaching Snapshot

The graded analysis uses a frozen, instructor-prepared ITDK snapshot or approved representative teaching subset. The exact release identifier, source manifest, subset procedure, checksums, and seed identifiers are deployment decisions and are not known in this repository draft. Your instructor must provide them before you start Task 5. Record the supplied snapshot identifier in the notebook so another reader can tell which data your answers describe.

For fast local tests, the repository provisions the deterministic synthetic fixture `nids-itdk-mcp-synthetic-v1`, documented in [data/README.md](data/README.md) and `data/fixture-manifest.json`. It contains six invented nodes, six links (including multi-endpoint examples), eight AS-assignment rows, six geolocation rows, and eleven hostname rows. Its documented seeds use private-use teaching ASNs, reserved documentation IP ranges, and `.test` hostnames. Fixture values teach behavior and edge cases; they are not measurements of the public Internet and must not be used as evidence about real topology.

The starter notebook currently uses this synthetic fixture for its reproducible exercises. Before an instructor treats Task 5 as analysis of real ITDK topology, they must replace or supplement those seeds with a legally approved frozen teaching snapshot, publish its manifest, and preflight every required query. Until that happens, Task 5 answers describe only the synthetic fixture and must say so explicitly.

ITDK data may be access-controlled. Do not copy database contents into Git, publish generated CSVs, or redistribute snapshot rows unless your course's data terms explicitly allow it.

## Access Through the MCP Server

The database role is read-only and has `SELECT` access only to the four relations below. Students investigate the graded snapshot through the MCP server, not by opening a direct SQL connection. The server returns metadata with this shape:

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

## Relation: `caida_itdk.itdk_link_endpoints`

This relation maps an inferred link to its endpoint records.

| Column | PostgreSQL type | Meaning |
| --- | --- | --- |
| `link_id` | `text` | Identifier shared by all endpoints of one inferred link. |
| `endpoint_ordinal` | `integer` | Position that distinguishes endpoint rows within a link. |
| `endpoint_token` | `text` | Source endpoint encoding retained for provenance; it may encode a node and observed interface. |
| `node_id` | `text` | Normalized router-node identifier used for joins and node filtering. |

The primary key is `(link_id, endpoint_ordinal)`, and `node_id` is indexed. The worked `get_link_endpoints` tool filters on `link_id` and orders by `endpoint_ordinal`. The extension `find_links_for_node` filters on `node_id` and orders by `(link_id, endpoint_ordinal)`.

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

| Tool | Returned columns | Stable order |
| --- | --- | --- |
| `get_link_endpoints` | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `endpoint_ordinal` |
| `find_links_for_node` | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` | `link_id`, `endpoint_ordinal` |
| `find_nodes_by_asn` | `node_id`, `asn`, `method` | `node_id` |
| `search_nodes_by_geolocation` | `node_id`, `continent`, `country`, `region`, `city`, `latitude`, `longitude`, `method` | `country`, longitude/latitude with nulls first, `node_id` |
| `lookup_router_hostnames` by IP | `ip`, `hostname` | `ip`, hostname with nulls first |
| `lookup_router_hostnames` by exact name or prefix | `ip`, `hostname` | `hostname`, `ip` |

These projections and orderings are part of the public contract. A student tool must not accept caller-chosen tables, columns, joins, ordering, SQL fragments, limits, or cursors.

## Limitations to Carry Into Every Answer

- Topology reflects paths visible from a particular measurement campaign, not all possible Internet paths.
- Alias resolution can group interfaces incorrectly or fail to group interfaces that belong together.
- An inferred link does not reveal traffic direction, capacity, utilization, ownership, contractual relationship, or whether it still exists now.
- AS and geolocation assignments are method-dependent inferences with provenance.
- Missing rows and null fields mean unavailable evidence, not a confirmed negative fact.
- A hostname is a PTR observation that may be missing, stale, or operationally encoded.
- Counts describe the frozen teaching snapshot and selected filters; they should not be generalized to the whole Internet without justification.

[README](README.md) | [Introduction](Introduction.md) | Datasets ⮕ | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
