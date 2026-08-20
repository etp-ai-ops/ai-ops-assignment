[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | Task 4 ⮕ | [Notebook](nids-itdk-mcp.ipynb)

# Task 4 Guidance: Evidence-Based Topology Investigation With the Full MCP Server

Use this guide with the Task 4 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). This task uses the instructor-provided, frozen teaching snapshot and vetted seeds, and your now-complete seven-tool MCP server: the four tools that shipped complete (`get_link_endpoints`, `find_nodes_by_asn`, `search_nodes_by_geolocation`, `lookup_router_hostnames`) plus the three you built in Task 3 (`find_links_for_node`, `find_peer_asns_for_node`, `find_hostnames_for_asn`). Access the snapshot only through these MCP tools. Direct SQL would bypass the interface whose design this assignment assesses — that path was only ever open for Task 1's local fixture practice, and only there.

---

## Keep an Evidence Ledger

For every tool call, append one record containing:

| Field | What to record |
| --- | --- |
| snapshot | instructor-provided snapshot or subset identifier |
| step | a stable label used in your narrative |
| tool | exact MCP tool name |
| arguments | complete JSON argument object |
| artifact | returned filename or notebook-captured stable artifact ID |
| rows | returned `row_count` |
| columns | ordered returned column metadata |
| transformation | filtering, grouping, deduplication, or merge applied afterward |

Keep intermediate DataFrames in named variables and show small relevant previews. Generated filenames may differ between runs, so reproducibility comes from the recorded call and snapshot plus a clear transformation, not from assuming a UUID-like filename will recur.

---

## Count Nodes Assigned to the Seed ASN (Q13)

Call `find_nodes_by_asn` with the supplied ASN. Report both returned rows and distinct `node_id` values if they differ, then tabulate `method`. Choose two nodes by a rule another reader can repeat, such as the first two distinct node IDs in the tool's stable order that meet a stated evidence condition.

Do not describe the result as every router currently operated by the organization. It is the set of assignments present in one teaching snapshot under the supplied methods and measurement coverage.

- **Q13** For the instructor-provided ASN, how many distinct router nodes are returned and which assignment methods occur? Explain why the result is a snapshot-specific assignment count rather than a complete current inventory of the AS.

---

## Follow Two Nodes' Immediate Neighbors With `find_peer_asns_for_node` (Q14)

For each chosen node, call `find_peer_asns_for_node` directly — this is the tool you built in Task 3 specifically to answer "who is this node's immediate router-level neighbor, and what AS runs it?" in one step, rather than manually walking `find_links_for_node` and `get_link_endpoints` and then cross-referencing `find_nodes_by_asn` yourself.

1. call `find_peer_asns_for_node` for each chosen node;
2. note that a node absent from the result may simply have no peer with an AS assignment — recall the INNER-join limitation from [Task 3](Task-3-new-mcp-tools.md#tool-2-find_peer_asns_for_node); and
3. where you want the full endpoint detail behind a peer relationship (multi-endpoint links, bare tokens), still call `find_links_for_node` and `get_link_endpoints` as in the previous version of this task — `find_peer_asns_for_node` summarizes; it does not replace the endpoint-level view when you need it.

A neighbor table can include seed node, peer node, peer ASN, peer method, and (when you drop to the endpoint-level tools) link ID, endpoint ordinal, endpoint token, and endpoint count for the link. Use "neighbor relationship observed in this inferred link" rather than claiming a current physical or business relationship.

- **Q14** Choose two returned nodes using a reproducible rule. For each, what does `find_peer_asns_for_node` return, and which records require special care because a link has other than two endpoint rows, an endpoint lacks an interface encoding, or a peer is excluded by the tool's INNER join?

---

## Compare Two Geographic Result Sets (Q15)

Use the two instructor-specified countries or bounds. Keep the arguments visible and apply the same summary to both result sets. Reasonable summaries include distinct-node count, method distribution, missing-field rate, or counts by region/city when the fields and cardinality support them.

Choose a visualization that matches the question and does not imply more precision than the data supplies. A bar chart of categorical counts is usually clearer than plotting exact inferred coordinates. Label the snapshot, filter, grain, and units.

Compare what is visible, then name what is not established: population-normalized router density, traffic volume, complete infrastructure footprint, causal investment, current deployment, or method-independent ground truth.

- **Q15** Compare the instructor-provided two countries or bounded regions with a clearly defined summary and visualization. What differences are visible, and which broader geographic conclusions would be unjustified from these results alone?

---

## Assemble and Audit an Evidence Table (Q16)

Start from the supplied IP or hostname selector and call `lookup_router_hostnames`. Connecting an IP back to a node is only possible where the available endpoint encoding and tool results expose a defensible match. Preserve unmatched rows instead of manufacturing a link.

Work outward with approved calls, using `find_hostnames_for_asn` where it is the more direct path — for example, once you have identified a seed node's ASN, `find_hostnames_for_asn` can recover every hostname the server is confident belongs to a node in that AS in one call, rather than chaining `find_links_for_node` and per-link hostname lookups yourself:

```text
IP/name seed -> hostname rows (lookup_router_hostnames)
defensible interface evidence -> node evidence
node -> ASN (find_nodes_by_asn / recorded assignment)
ASN -> every confidently-matched hostname in the AS (find_hostnames_for_asn)
node -> links and peers (find_links_for_node, find_peer_asns_for_node)
link -> complete endpoint rows (get_link_endpoints)
node -> geolocation evidence when available (search_nodes_by_geolocation)
```

Document each match key and whether it is direct, parsed from an eligible endpoint encoding, or unavailable. Remember that `find_hostnames_for_asn`'s INNER joins exclude interfaces with no PTR record and bare endpoint tokens — an incomplete evidence table here is often the honest result, not a bug in your query.

Give the approved MCP-capable agent a narrow question based on your evidence table and ask it for a short answer with claim-to-artifact citations. Save the prompt, relevant tool trace, and response. If no agent is uniformly available, use the instructor-provided deterministic fallback output; do not select a different public model that other students cannot access.

Break the response into factual claims. For each claim, mark it:

- **supported** — the cited artifact and your transformation establish it;
- **underspecified** — plausible, but missing the snapshot, grain, method, or filter;
- **overstated** — stronger than the evidence, such as turning an inference into certainty; or
- **unsupported** — no captured artifact establishes it.

Correct at least one weakness. If every factual claim is supported, identify the most important omitted limitation instead of inventing an error.

- **Q16** Starting from the supplied IP or hostname seed, build a reproducible evidence table connecting names, interfaces, nodes, links, AS assignments, and locations wherever the available tools permit it. Then ask the approved MCP-capable agent to propose a short interpretation, verify every factual claim against your captured CSVs, and identify at least one claim that is overstated, unsupported, or missing an essential limitation.

---

## What Your Write-Up Should Address

Answer Q13–Q16 in your own words. Each answer must cite exact tool arguments, artifact and row-count metadata, transformations, and relevant rows or aggregates. Include at least one limitation per analytical answer. Distinguish observed snapshot records from topology, ownership, location, and business inferences. The agent critique must verify claims individually; grading is based on your reproducible evidence and judgment, not the agent's wording.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | Task 4 ⮕ | [Notebook](nids-itdk-mcp.ipynb)
