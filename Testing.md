[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | Testing ⮕ | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Testing Guide

Tests in this assignment protect a public behavior, not a particular spelling of the solution. Use the narrowest test layer that can prove each requirement, then keep a small number of integration and end-to-end checks for boundaries that unit tests cannot cover.

## 1. Test Layers

| Layer | What it proves | Typical dependencies |
| --- | --- | --- |
| Schema | discovery advertises exact names, required inputs, types, bounds, selector composition, and no extra properties | none |
| Validation/dispatch | valid calls reach the correct repository method; invalid calls return a stable error and do not dispatch | fake repository |
| Repository | SQL shape, parameter tuple, projection metadata, filename prefix, and ordering are correct | recording executor |
| Database integration | the fixed statement runs against the four-relation fixture and handles real PostgreSQL types/order | fixture PostgreSQL |
| MCP end to end | discovery and a call work through the supplied transport/auth/session and produce readable CSV metadata | running scaffold |

Do not make every test start containers. Fast schema, dispatch, and repository tests should explain most failures before an integration test runs.

## 2. Arrange, Act, Assert

Keep each test focused:

```python
def test_example_rejects_extra_property():
    # Arrange a fake dependency and invalid arguments.
    # Act through the public validation/dispatch boundary.
    # Assert INVALID_ARGUMENT and assert the fake was not called.
    ...
```

Name the behavior, not an implementation detail. Prefer `test_hostname_prefix_treats_percent_literally` to `test_replace_called_three_times`.

## 3. Schema and Validation Cases

For a constrained input, cover equivalence classes rather than only one happy path:

- minimum, ordinary, and maximum valid values;
- just-below and just-above bounds;
- wrong JSON types, including numeric strings;
- missing required properties and unexpected extra properties;
- zero, one, and multiple selectors;
- IPv4, IPv6, and a string that only resembles an IP;
- finite coordinate edges and inverted minimum/maximum pairs; and
- identifier whitespace, length, and control-character cases where relevant.

When validation fails, assert both the public error code and that the repository was not called.

## 4. Repository Tests

A recording executor can capture the query object and parameters without contacting PostgreSQL. Use it to check that:

- caller data appears in the parameters tuple rather than SQL text;
- parameters appear in the exact order required by repeated optional predicates;
- the projection metadata matches the documented columns and types;
- an explicit `ORDER BY` supplies the promised stable order; and
- the filename prefix identifies the operation.

Avoid assertions on incidental whitespace or the complete SQL string when a more focused assertion proves the behavior. Security-significant structure—such as the absence of interpolation and presence of a fixed predicate—does deserve an explicit check.

## 5. Prefix-Escaping Tests

Test an ordinary prefix and separate cases containing `%`, `_`, and backslash. The recorded bound parameter should preserve each character as literal SQL pattern content and add only the server-owned trailing wildcard. Also include a fixture row that would match if the caller's `%` or `_` were accidentally treated as wildcards but must not match the correct literal search.

## 6. Integration and End-to-End Checks

Integration tests should use the synthetic fixture, never production credentials or unstable live records. Confirm empty, single-row, multi-row, nullable, IPv4, IPv6, and hyperlink-like cases where the fixture supports them. Assert both row contents and stable order.

An end-to-end smoke test should:

1. establish an authenticated session using test-only settings;
2. list tools and locate the capability under test;
3. make one valid call;
4. validate the structured metadata;
5. load the CSV from the returned path; and
6. compare its header and row count with the result metadata.

Do not log or print bearer keys, database URLs, passwords, or raw internal exceptions.

## 7. Running Tests

Use the commands shipped with your scaffold. The expected Python workflow is:

```bash
uv run pytest
```

Run a focused file or test while iterating:

```bash
uv run pytest tests/test_student_tools.py -q
uv run pytest tests/test_student_tools.py -q -k hostname
```

Database integration tests may require the supported container runtime. If your course deployment uses a separate command or marker, follow the instructor handout. A clean final submission runs the published required suite without production secrets and executes the notebook from top to bottom without errors.

## 8. Hidden Tests and Fair Contracts

Hidden tests check announced observable behavior, including wrong types, unordered bounds, extra properties, SQL interpolation, missing ordering, wildcard escaping, and complete discovery/dispatch wiring. They should not depend on secret production rows or demand byte-for-byte agreement with a reference implementation.

Passing visible tests is evidence, not proof, that your tool is complete. Use the guides and public contract to add at least one meaningful student-authored test per required tool, including the Task 4 vertical slice.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | Testing ⮕ | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
