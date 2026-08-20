[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | Task 4 ⮕ | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 4 Guidance: Adding a Complete MCP Capability

Use this guide with the Task 4 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). Unlike earlier tasks with marked pieces in an existing operation, this guided extension asks you to connect one narrow analytical intent across every layer: `find_links_for_node`.

---

## Start With the Contract

Write a small contract table before code:

| Part | Decision |
| --- | --- |
| intent | return link endpoint rows that contain one selected node |
| input | one validated `node_id`; no extra properties |
| projection | `link_id`, `endpoint_ordinal`, `endpoint_token`, `node_id` |
| filter | exact `node_id` bound separately from fixed SQL |
| ordering | `link_id`, then `endpoint_ordinal` |
| result | the common CSV metadata envelope |
| behavior | read-only, non-destructive, idempotent, closed-world |

This table tells you what must stay consistent without giving you an assembled implementation.

---

## Trace the Existing Example

Use `get_link_endpoints` as a structural example. Identify where it defines:

- its input schema and description;
- its dispatch branch;
- its fixed query and column tuple;
- its repository method and parameter tuple;
- its result filename prefix; and
- its tests at each layer.

Mirror the architecture, not the filtering behavior. The existing tool starts from one `link_id`; the new tool starts from one `node_id`, can return endpoints across multiple links, and therefore needs a different stable ordering.

---

## Implement From the Inside Out

A productive sequence is:

1. define the fixed query and metadata;
2. add the narrow repository method;
3. add validation/dispatch;
4. advertise the schema and description; and
5. add tests plus one MCP smoke call.

After each step, compare the name, argument key, projection, and ordering with the contract table. The final discovery response must describe behavior that direct dispatch and the database-backed result actually implement.

Use the shared identifier rules: 1–255 characters, at least one non-whitespace character, and no C0/DEL control characters. Do not create a second, subtly different node-ID schema.

---

## Interpret Returned Endpoint Rows Carefully

Filtering endpoint rows by one node answers "which endpoint records contain this node?" It does not automatically return every endpoint on those link IDs. To inspect immediate neighbors in Task 5, use the returned link IDs to call the completed `get_link_endpoints` tool for each selected link.

This two-step design keeps each tool's meaning precise:

```text
node -> find_links_for_node -> relevant link IDs
link ID -> get_link_endpoints -> all endpoint rows for that link
```

Do not assume every link has two rows, and do not call every other endpoint a bilateral business peer. The observation is router-level adjacency or multi-endpoint membership in the teaching snapshot.

---

## Prove the Vertical Slice

Add tests that separately prove:

- discovery exposes the schema, description, and common output contract;
- invalid identifiers and extra properties do not dispatch;
- valid dispatch sends exactly one node ID to the expected method;
- the query uses a bound parameter and the node indexable predicate;
- projection metadata and `(link_id, endpoint_ordinal)` ordering are exact;
- fixture results contain the expected selected-node rows in stable order; and
- one real MCP session produces readable CSV metadata.

Choose one student-authored test that adds coverage rather than copying a visible test. A hyperlink fixture, empty valid result, control-character identifier, or discovery/dispatch mismatch are useful candidates if not already covered.

---

## What Your Write-Up Should Address

Answer Q11–Q12 by tracing the capability and discussing your strongest added test. Explain each layer's responsibility, show consistent discovery/direct/MCP evidence, and state what the tool does not claim. Do not paste the complete vertical-slice implementation into the notebook response.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | Task 4 ⮕ | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
