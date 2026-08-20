[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | Task 5 ⮕ | [Notebook](nids-itdk-mcp.ipynb)

# Task 5 Guidance: Evidence-Based Topology Investigation

Use this guide with the Task 5 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). This task uses the instructor-provided, frozen teaching snapshot and vetted seeds. Access it only through your MCP tools; direct SQL would bypass the interface whose design this assignment assesses.

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

## Count Nodes Assigned to the Seed ASN

Call `find_nodes_by_asn` with the supplied ASN. Report both returned rows and distinct `node_id` values if they differ, then tabulate `method`. Choose two nodes by a rule another reader can repeat, such as the first two distinct node IDs in the tool's stable order that meet a stated evidence condition.

Do not describe the result as every router currently operated by the organization. It is the set of assignments present in one teaching snapshot under the supplied methods and measurement coverage.

---

## Walk From Nodes to Complete Links

For each chosen node:

1. call `find_links_for_node` to obtain its link memberships;
2. extract distinct link IDs in their returned stable order;
3. call `get_link_endpoints` for each link under analysis; and
4. label the seed node and other endpoint rows without assuming there is exactly one other endpoint.

If the vetted seed produces more link calls than the course budget allows, use the instructor-specified deterministic selection rule. Do not invent an arbitrary truncation after seeing which rows support a preferred story.

A neighbor table can include seed node, link ID, endpoint ordinal, endpoint token, endpoint node, and endpoint count for the link. Use "neighbor endpoint observed in this inferred link" rather than claiming a current physical or business relationship.

---

## Compare Two Geographic Result Sets

Use the two instructor-specified countries or bounds. Keep the arguments visible and apply the same summary to both result sets. Reasonable summaries include distinct-node count, method distribution, missing-field rate, or counts by region/city when the fields and cardinality support them.

Choose a visualization that matches the question and does not imply more precision than the data supplies. A bar chart of categorical counts is usually clearer than plotting exact inferred coordinates. Label the snapshot, filter, grain, and units.

Compare what is visible, then name what is not established: population-normalized router density, traffic volume, complete infrastructure footprint, causal investment, current deployment, or method-independent ground truth.

---

## Build a Cross-Tool Evidence Table

Start from the supplied IP or hostname selector and call `lookup_router_hostnames`. Connecting an IP back to a node is only possible where the available endpoint encoding and tool results expose a defensible match. Preserve unmatched rows instead of manufacturing a link.

Work outward with approved calls:

```text
IP/name seed -> hostname rows
defensible interface evidence -> node/link evidence
node -> links and approved node profile families
link -> complete endpoint rows
node -> AS and geolocation evidence when available
```

Document each match key and whether it is direct, parsed from an eligible endpoint encoding, or unavailable. The goal is an honest evidence table, not a fully populated table at any cost.

---

## Audit an Agent's Proposed Interpretation

Give the approved MCP-capable agent a narrow question based on your evidence table and ask it for a short answer with claim-to-artifact citations. Save the prompt, relevant tool trace, and response. If no agent is uniformly available, use the instructor-provided deterministic fallback output; do not select a different public model that other students cannot access.

Break the response into factual claims. For each claim, mark it:

- **supported** — the cited artifact and your transformation establish it;
- **underspecified** — plausible, but missing the snapshot, grain, method, or filter;
- **overstated** — stronger than the evidence, such as turning an inference into certainty; or
- **unsupported** — no captured artifact establishes it.

Correct at least one weakness. If every factual claim is supported, identify the most important omitted limitation instead of inventing an error.

---

## What Your Write-Up Should Address

Answer Q13–Q16 in your own words. Each answer must cite exact tool arguments, artifact and row-count metadata, transformations, and relevant rows or aggregates. Include at least one limitation per analytical answer. Distinguish observed snapshot records from topology, ownership, location, and business inferences. The agent critique must verify claims individually; grading is based on your reproducible evidence and judgment, not the agent's wording.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | Task 5 ⮕ | [Notebook](nids-itdk-mcp.ipynb)
