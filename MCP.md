[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | MCP ⮕ | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# MCP Guide

This guide covers the part of the Model Context Protocol used in this assignment: discovering tools, validating arguments, dispatching calls, and reading structured CSV metadata. Transport, session framing, authentication middleware, connection pooling, and CSV publication are supplied infrastructure rather than student TODOs.

## 1. Client, Server, and Tool

An MCP client opens a session with a server, asks what tools are available, and calls a chosen tool with a JSON object. The server owns the mapping from that analytical intent to data access.

```text
client -> tools/list -> tool definitions
client -> tools/call(name, arguments) -> validation -> repository -> CSV
client <- structured result metadata <- server
```

The protocol can be used by a deterministic Python client or by an MCP-capable agent. The server contract is the same either way. Using an agent does not bypass schemas, grant database access, or make returned claims trustworthy without verification.

## 2. Discovering Tools

`tools/list` returns definitions that include a machine-oriented `name`, a human-readable `description`, an `inputSchema`, and an `outputSchema`. This server also labels its tools read-only, non-destructive, idempotent, and closed-world through annotations. Annotations help clients, but security still comes from validation, fixed implementation, and database permissions.

In Task 0, inspect rather than memorize the discovered definition of `get_link_endpoints` — one of four tools that ship complete. In Task 3 you will read this same discovery response for the three tools you design and build yourself, so get comfortable with what it exposes now. Identify:

- what the description promises;
- which argument is required and what strings are valid;
- whether extra properties are allowed; and
- which fields and types a successful result promises.

Descriptions matter because an agent uses them to select among tools. Schemas matter because a plausible-sounding but malformed call should fail before reaching a repository.

## 3. Restrictive Input Schemas

Every assignment input is a JSON Schema Draft 2020-12 object with `additionalProperties: false`. For example, this simplified, unrelated tool accepts one positive integer and rejects extra keys:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "sample_id": {"type": "integer", "minimum": 1}
  },
  "required": ["sample_id"]
}
```

JSON types are exact. `64500` is an integer; `"64500"` is a string. A schema can enforce independent bounds, patterns, required properties, and combinations such as exactly one selector. Application-level validation is still needed for rules such as finite coordinate values, minimum not exceeding maximum, and parsing an IPv4 or IPv6 address.

> **Gotcha:** `oneOf` means exactly one listed branch must validate. It does not mean "one or more." Design the branches and `additionalProperties` rule together, then test zero, one, and multiple selectors.

## 4. Dispatch and Repository Boundaries

After validation, dispatch maps a known tool name to one repository method and passes only validated values. The repository chooses the SQL statement, projection, parameter order, CSV column metadata, filename prefix, and stable ordering.

A useful separation of responsibility is:

| Layer | Owns | Does not own |
| --- | --- | --- |
| Tool definition | name, description, JSON schemas, annotations | SQL text |
| Validation | input shape and cross-field rules | database access |
| Dispatch | known tool-to-method mapping | caller-selected code paths |
| Repository | fixed query, bound parameters, columns, ordering | arbitrary client query structure |
| Executor/writer | connection use, streaming, atomic CSV output | analytical meaning |

For each of the three new tools you design in Task 3, all five pieces must agree. Advertising a tool without dispatch, or implementing a repository method without discovery, leaves an incomplete capability.

## 5. Structured CSV Results

A successful tool call returns a JSON object with exactly three required fields:

```json
{
  "file_path": "/app/outputs/example_unique-id.csv",
  "row_count": 3,
  "columns": [
    {"name": "node_id", "type": "string"},
    {"name": "asn", "type": "int64"},
    {"name": "method", "type": "string"}
  ]
}
```

`columns` is ordered metadata, not the data rows. Load `file_path` with the supplied notebook helper or pandas only after the call succeeds. Verify that the CSV header matches the metadata and record the exact arguments and `row_count` with every analytical artifact.

The allowed column type labels in this assignment are `string`, `inet`, `int32`, `int64`, and `float64`. Empty results are successful results with `row_count: 0`; they are different from tool errors.

## 6. Safe Failures

Invalid tool names or arguments produce the stable tool error code `INVALID_ARGUMENT`. Unexpected execution failures produce `INTERNAL_ERROR`. These errors should let a client change course without exposing SQL text, stack traces, database connection details, credentials, or sensitive configuration.

Test both the positive and negative paths. A tool that works for one valid example but accepts ambiguous selectors or arbitrary extra input does not satisfy its contract.

## 7. Calling a Tool

Use the supplied client helper rather than recreating protocol framing in the notebook. The exact import path may be scaffold-specific, but the call has this conceptual form:

```python
async with open_session() as session:
    listed = await session.list_tools()
    result = await session.call_tool(
        "get_link_endpoints",
        {"link_id": instructor_link_id},
    )
```

Keep the instructor-provided seed in a variable; do not replace it with a value copied from an old assignment or production example. Capture the returned structured object before loading its file so the notebook preserves the tool trace.

## 8. Contract Checklist

Before considering a tool complete, confirm that:

- discovery shows the intended name, precise description, input schema, output schema, and annotations;
- valid calls reach exactly one expected repository method;
- invalid types, ranges, selector combinations, and extra properties are rejected;
- the repository contains only package-owned read-only SQL and bound data values;
- result columns and types match the discovered output contract;
- rows have an explicit stable order; and
- direct dispatch and an actual MCP session produce consistent results.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | MCP ⮕ | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
