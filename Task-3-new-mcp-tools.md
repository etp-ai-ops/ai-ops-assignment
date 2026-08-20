[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | Task 3 ⮕ | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 3 Guidance: Designing and Building Three New MCP Tools

Use this guide with the Task 3 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). This is the assignment's core vertical-slice work. The four tools from Task 0/2 ship complete; here you add three tools that do not exist yet, each one a full path from schema through repository through test. Re-read [MCP](MCP.md) and [Safe-Queries](Safe-Queries.md) before starting — the same discovery/validation/dispatch/repository/executor boundary and the same fixed-SQL discipline apply to every tool you design, not only the ones already in the codebase.

The three contracts below are fixed. Do not invent different column names, ordering, or SQL shapes — your notebook, your tests, and the private answer key all assume exactly this contract.

---

## Tool 1: `find_links_for_node`

This is the same tool the previous version of this assignment called its one guided extension; it is now the first of three.

| Part | Decision |
| --- | --- |
| args | `node_id` (identifier string) |
| returns | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` |
| order | `link_id`, then `endpoint_ordinal` |
| repository | `LinkRepository.find_links_for_node` |
| seed/access path | `node_id` (indexed) |

Filtering endpoint rows by one node answers "which endpoint records contain this node?" — it does not return every endpoint on those link IDs. To inspect a node's immediate neighbors, use the returned `link_id`s to call `get_link_endpoints` for each link of interest; that two-step design keeps each tool's meaning precise.

- **Q9** Trace one `find_links_for_node` call from discovery through CSV publication, and demonstrate one valid and one invalid call. Which contract rule handles the invalid case, and how did you verify all layers agree?

---

## Tool 2: `find_peer_asns_for_node`

| Part | Decision |
| --- | --- |
| args | `node_id` (identifier string) |
| returns | `peer_node_id`, `peer_asn`, `peer_method`, **distinct** |
| order | `peer_node_id`, then `peer_asn` |
| repository | new `TopologyRepository.find_peer_asns_for_node` |
| seed/access path | `node_id`, via a self-join on `link_id` |

The fixed shape self-joins `itdk_link_endpoints` to itself on `link_id`, excluding the seed node's own row, then inner-joins the peer's `node_id` to `itdk_node_as`:

```sql
SELECT DISTINCT e2.node_id AS peer_node_id, a2.asn AS peer_asn, a2.method AS peer_method
FROM caida_itdk.itdk_link_endpoints e1
JOIN caida_itdk.itdk_link_endpoints e2
  ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
JOIN caida_itdk.itdk_node_as a2 ON a2.node_id = e2.node_id
WHERE e1.node_id = %s
ORDER BY peer_node_id, peer_asn
```

This is exactly the self-join pattern the prerequisite ITDK assignment's `SQL.md §3.3` and `Task-2.md` teach, and the same pattern your Task 1 direct-SQL work should already have made familiar. `DISTINCT` collapses the fan-out from a node sitting on more than one link to the same peer.

> **Note on join behavior**: the join to `itdk_node_as` is an **INNER** join, so a peer node without any AS-assignment row is excluded from the result entirely — it does not appear as a `peer_asn = NULL` row. This mirrors the same tradeoff the prerequisite assignment's Task 2 documents for its own peer-identification query. Document this limitation in your own tool description, not only in your notebook answer.

- **Q10** Explain the self-join, the role of `DISTINCT`, and the INNER-join tradeoff for `find_peer_asns_for_node`. Using the fixture, show a peer that the INNER join correctly excludes and explain why excluding it (rather than returning a null `peer_asn`) is the right contract for this tool.

---

## Tool 3: `find_hostnames_for_asn`

| Part | Decision |
| --- | --- |
| args | `asn` (integer, same tightened schema as `find_nodes_by_asn`) |
| returns | `node_id`, `ip`, `hostname`, **distinct** |
| order | `node_id`, then `ip` (nulls first), then `hostname` |
| repository | new `TopologyRepository.find_hostnames_for_asn` |
| seed/access path | `asn` (indexed) |

The fixed shape seeds from `itdk_node_as.asn`, joins outward to that node's `itdk_link_endpoints` rows, then parses each `endpoint_token` into an IP the way [Task 1](Task-1-sql-exploration.md) and the prerequisite assignment's `SQL.md §3.5` teach, and inner-joins that parsed IP to `itdk_router_hostnames`:

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

- `strpos(endpoint_token, ':')` locates the *first* colon; `substring(... FROM strpos(...) + 1)` takes everything after it, so the extracted text is the whole remainder of the token, not just the segment between the first two colons;
- the `CASE` yields `NULL` (not an error) for a bare token with no colon at all, like `L2`'s `N2`, so `::inet` never runs on an empty string; and
- `::inet` casts the extracted text to Postgres's IP type so it can compare against `h.ip`.

> **Gotcha — don't reach for `split_part` here.** An earlier draft of this tool used `NULLIF(split_part(endpoint_token, ':', 2), '')::inet`, which is exactly right when a token has *at most one* colon (a bare IPv4 suffix like `N1:192.0.2.1`), but silently breaks on this fixture's IPv6 tokens: `split_part('N1:2001:db8:1::1', ':', 2)` returns only `'2001'` — the text between the *first and second* colon — which then fails the `::inet` cast outright. `strpos`/`substring` split on the *position* of the first colon instead of a fixed field count, so they handle an endpoint token with any number of embedded colons. The lesson generalizes: don't assume a delimiter appears exactly once just because your first few examples only had one.

> **Note on join behavior**: both joins that reach `itdk_router_hostnames` are **INNER** joins here (unlike the `LEFT JOIN` the prerequisite assignment uses for the same parse when it wants to keep unmatched interfaces). That means an interface with no PTR record, and a bare endpoint token with no embedded IP at all — the fixture's `L2` row for `N2` is exactly this case — are both excluded from this tool's result rather than appearing as a row with a null `hostname`. Document this limitation explicitly: `find_hostnames_for_asn` answers "which hostnames are we confident belong to a node in this ASN?", not "does every node in this ASN have an interface, resolvable or not?"

For ASN `64500` (nodes `N1`, `N2`) the fixture produces four rows: `N1`/`192.0.2.1`/`edge-la.example.test`, `N1`/`2001:db8:1::1`/`v6-edge-la.example.test`, `N2`/`192.0.2.2`/`edge-sea.example.test`, and `N2`/`2001:db8:2::2`/`v6-edge-sea.example.test` (from `N2`'s `L6` endpoint) — `L2`'s bare `N2` token is the one endpoint correctly absent, dropped by the INNER join rather than appearing as a null-hostname row.

- **Q11** Explain the `endpoint_token` parsing and the INNER-join tradeoff for `find_hostnames_for_asn`. Using ASN `64500`, show the four returned rows and explain why `L2`'s bare `N2` endpoint does not appear among them.

---

## Build All Three the Same Way You'd Build Any Tool

For each of the three tools, follow the same sequence [MCP](MCP.md#4-dispatch-and-repository-boundaries) describes:

1. define the fixed query and column metadata;
2. add the narrow repository method (`find_links_for_node` on `LinkRepository`; the other two on a new `TopologyRepository` registered on `Repositories` alongside `nodes`, `links`, `hostnames`);
3. add validation/dispatch — `node_id` reuses the shared identifier rules (1–255 characters, at least one non-whitespace character, no C0/DEL control characters); `asn` reuses the same tightened integer schema as `find_nodes_by_asn`;
4. advertise the schema and description; and
5. add tests at the schema, dispatch, repository, and (where your environment supports it) MCP-session layers.

---

## Add Tests for Each Tool (Q12)

Add your tests to `tests/test_student_tools.py`, which now targets these three tools instead of the single guided extension from the previous version of this assignment. For each tool, aim for the same rigor as any required tool: valid/invalid schema cases, a recording-executor check that caller data appears only in bound parameters, and a fixture-backed check of projection, ordering, and the documented INNER-join exclusions above.

- **Q12** For your three new tools combined, describe the single most useful test you added, the concrete failure it would catch, and why a test at a different layer would not prove the same thing.

---

## What Your Write-Up Should Address

Answer Q9–Q12 by tracing each tool's contract and citing concrete fixture rows and captured MCP metadata, not by pasting your complete implementation. Explain every INNER-join limitation in your own words, and connect each SQL pattern back to what Task 1's direct-SQL exploration already showed you about the schema.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | Task 3 ⮕ | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
