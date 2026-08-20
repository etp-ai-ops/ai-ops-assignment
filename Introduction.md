[README](README.md) | Introduction ⮕ | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Introduction

## Reading

- [CAIDA Internet Topology Data Kit](https://www.caida.org/catalog/datasets/internet-topology-data-kit/) (webpage) — the dataset's purpose, production context, and release information.
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) (specification) — tool discovery, tool calls, input schemas, and structured results.
- [Datasets](Datasets.md) — the exact classroom relations, fields, access path, and known limitations.
- [MCP](MCP.md) — the tool contract and supported client workflow for this assignment.

Your instructor must identify the release-specific ITDK page or approved teaching-subset manifest before the graded investigation begins. Do not assume that a year, seed, or snapshot used by another class applies to yours.

### Prerequisite NIDS Assignments

- [ITDK — ITDK](https://github.com/CAIDA/nids-itdk) — supplies router nodes, interfaces, inferred links, node-to-AS assignments, geolocation, hostnames, and limitations of traceroute-derived topology.
- [ASN — ASN Introduction](https://github.com/CAIDA/nids-asn) — supplies autonomous systems and ASN concepts. This may be inherited through the ITDK prerequisite when the course catalog treats dependencies as transitive.

You should also be able to write basic Python, read a small parameterized SQL `SELECT`, inspect CSV data with pandas, use a Jupyter notebook, and use Git. If one of these general skills is new to you, ask for the course primer before starting rather than guessing through the implementation.

## From Measurements to Router-Level Topology

Traceroute records a sequence of responsive interfaces along a measured path. ITDK processing uses alias-resolution techniques to group interface addresses that appear to belong to one physical router. That inferred router becomes a **node**. Adjacent observations are then represented as **links** between nodes.

This graph is useful, but it is not a complete or permanent map of the Internet. It depends on the measurement vantage points, destinations, responses, collection time, alias-resolution evidence, and processing choices. A node is an inference about a device; a link is an observed or inferred adjacency; neither proves ownership, physical location, traffic volume, direction, capacity, or a business relationship.

Some links contain more than two endpoints. Treat such a hyperlink as a multi-endpoint observation instead of forcing it into an assumed two-router model. Some hops do not answer traceroute. Missing annotations or an absent row also require care: they can mean that a measurement or inference was unavailable, not that the corresponding router, name, location, or relationship does not exist.

## Four Complementary Relations

The classroom database exposes four approved relations through narrow MCP tools:

- link endpoints connect `link_id` values to endpoint positions, endpoint tokens, and normalized `node_id` values;
- node-to-AS rows associate nodes with ASNs and retain the assignment method;
- node-geolocation rows associate nodes with coordinates and place names and retain the geolocation method; and
- router-hostname rows associate interface IP addresses with DNS PTR names.

These are different views of measured or inferred evidence. They do not form a perfect one-row-per-router record. A node can participate in many link rows and can have more than one AS-assignment row. An interface may have no PTR record. A geolocation result may be missing or uncertain. When relations can be connected, `node_id` is the normal router-level join key. `endpoint_token` preserves source encoding and may include interface information, but it is not a substitute for the normalized key.

## Why Put MCP in Front of the Data?

A general SQL interface would let a caller choose tables, projections, predicates, joins, and perhaps operations that are expensive or unsafe. This assignment instead exposes a small vocabulary of analytical intents such as "find nodes assigned to this ASN" or "find the endpoints for this link."

Each MCP tool advertises a name, description, restrictive input schema, and structured output schema. The server validates a call, dispatches it to one approved repository operation, executes package-owned SQL with separately bound data values, and writes a CSV. The client receives only stable metadata about that CSV. This boundary is both an analytical design choice and a security control.

Good tools help a client choose correctly. Their names and descriptions distinguish similar operations; their schemas reject ambiguous or irrelevant inputs; their results have fixed columns and stable ordering; and their failures reveal enough to correct a call without exposing credentials, SQL text, or internal exception details.

## Evidence, Inference, and Agents

An MCP-capable agent can discover tools, compose calls, and propose an explanation. It cannot make weak evidence stronger. Task 2 connects a real agent to your already-complete MCP server for the first time, and Task 4 asks you to audit an agent's full evidence-based interpretation; in both places, treat an agent's prose as a hypothesis to audit, not a result to trust. A defensible answer records:

1. the exact tool name and arguments;
2. the returned filename or stable artifact identifier and row count;
3. the transformation used to compute any summary;
4. the rows or aggregate that support each claim; and
5. at least one relevant limitation or alternative explanation.

The grade attaches to reproducible behavior, captured evidence, analysis, and your interpretation—not to whether an agent produced polished prose.

### Optional Reading

- [Hoiho: Internet Router Geolocation using Hostname Data](https://www.caida.org/catalog/papers/2021_hoiho/) (paper) — background on hostname-based router geolocation.
- [MCP Schema Reference](https://modelcontextprotocol.io/specification/2025-11-25/schema) (specification) — protocol message and schema details beyond what this assignment requires.

[README](README.md) | Introduction ⮕ | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
