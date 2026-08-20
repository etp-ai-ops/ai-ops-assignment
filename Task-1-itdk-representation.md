[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | Task 1 ⮕ | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 1 Guidance: Understanding the ITDK Representation

Use this guide with the Task 1 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). The notebook supplies fixture identifiers chosen to expose multiplicity, provenance, and missingness. Your job is to interpret the returned records, not replace those seeds with generic examples.

> **Note:** Study the schema and make predictions now. Some Task 1 notebook cells use the tools implemented in Tasks 2–4, so execute those evidence cells after the corresponding TODOs and tests are complete.

---

## Read Rows at Their Actual Grain

Before counting, state what one row represents:

- in link endpoints, one endpoint position of one inferred link;
- in node-to-AS, one `(node_id, asn)` assignment;
- in node geolocation, one supplied location row for a node; and
- in router hostnames, one `(ip, hostname)` PTR association.

The same node can therefore appear in many link endpoint rows and more than one AS row. Joining two one-to-many relations can multiply records. Use `nunique()` or explicit deduplication only after naming the entity you intend to count, and preserve the original evidence so the reason for deduplication remains visible.

---

## Distinguish Endpoint Fields

For the supplied link, make a compact table of all four endpoint columns. Annotate the role of each:

```text
link_id -> groups endpoint rows into one inferred adjacency/hyperlink
endpoint_ordinal -> distinguishes positions inside that link
endpoint_token -> preserves source endpoint encoding
node_id -> normalized router identifier used across router-level relations
```

Do not infer that the ordinal means direction or path order. Do not split every token at punctuation and assume the remainder is a valid interface: some encodings do not contain one. When connecting endpoint evidence to AS or geolocation evidence, start with `node_id`.

---

## Demonstrate Multiplicity Without Flattening It Away

Use separate MCP calls for each approved family rather than constructing a direct database join. For each supplied fixture node, compare counts at several grains, such as distinct node IDs, distinct ASNs, distinct link IDs, and endpoint rows.

A useful diagnostic is:

```python
summary = {
    "rows": len(df),
    "nodes": df["node_id"].nunique(),
    "links": df["link_id"].nunique(),
}
```

Adapt the columns to the actual result. This pattern is a counting aid, not an answer. Explain why multiple rows are plausible before deciding whether any should be deduplicated.

---

## Preserve Method and Missingness

The `method` columns expose how an AS or location assignment was made. Keep them in evidence tables and group summaries. A result produced by an inference method should be phrased as "assigned" or "inferred," not "proved."

For missing data, distinguish three states:

1. a successful tool call returning no matching rows;
2. a returned row with a null field; and
3. a failed call.

Only the third is an execution problem. The first two represent absence or incompleteness in the available snapshot. Neither proves that no real hostname, interface, location, or AS relationship exists.

---

## What Your Write-Up Should Address

Answer Q1–Q5 with concrete fixture rows and captured MCP metadata. State the grain of every count, explain why `node_id` is the relational key, retain method labels, and give a careful interpretation of missing evidence. Avoid claims about the current Internet: fixture rows are synthetic teaching records, and graded snapshot records remain measurement- and method-dependent.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | Task 1 ⮕ | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
