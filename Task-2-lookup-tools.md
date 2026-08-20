[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | Task 2 ⮕ | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 2 Guidance: Constrained ASN and Geolocation Lookups

Use this guide with the Task 2 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). Complete only the marked student regions for `find_nodes_by_asn` and `search_nodes_by_geolocation`; the server transport, authentication, connection pool, executor, writer, result serialization, and error mapping are supplied.

---

## Work From the Public Contract

For each tool, trace the same sequence before editing:

1. locate its schema and description;
2. locate its validation and dispatch path;
3. locate the repository query and column metadata;
4. read the visible tests; and
5. compare all four with [Datasets](Datasets.md#fixed-tool-projections).

Write down the required inputs, optional inputs, projection, ordering, and invalid cases. This prevents a local fix in one layer from silently disagreeing with discovery or CSV metadata.

---

## Implement `find_nodes_by_asn`

The input is a JSON integer from 1 through PostgreSQL's signed `bigint` maximum, `9,223,372,036,854,775,807`. Boolean and string values are not integer-form ASNs for this contract. Extra properties are forbidden.

The repository operation must:

- select exactly `node_id`, `asn`, and `method` from the approved relation;
- filter by the indexed ASN using a bound parameter;
- return the documented column metadata; and
- order rows by `node_id`.

Do not add a caller-controlled limit or accept an ASN list. Those would define different tools with different scale and contract decisions.

A useful fake-repository test records the received Python value. It should show that a valid JSON integer becomes the same integer at the repository boundary, while a numeric string and an extra property produce `INVALID_ARGUMENT` without a repository call.

---

## Implement `search_nodes_by_geolocation`

The required `country` is exactly two uppercase ASCII letters. Each coordinate is optional but must be finite and within its physical range:

| Input | Inclusive range |
| --- | ---: |
| `longitude_min`, `longitude_max` | -180 to 180 |
| `latitude_min`, `latitude_max` | -90 to 90 |

If both ends of an axis are present, minimum must not exceed maximum. A minimum or maximum may be supplied alone. Keep `country` as the leading equality predicate so the query follows the intended country-first index path; optional coordinate predicates narrow that seed set.

When an optional predicate needs the same value more than once in fixed SQL, its parameter can occur more than once in the parameter tuple. Build that tuple explicitly and test its order. Never interpolate absent values or change the SQL structure based on caller input.

The fixed result contains node/location fields and orders by country, longitude with nulls first, latitude with nulls first, then node ID. Check the exact column order in [Datasets](Datasets.md#fixed-tool-projections) rather than relying on a `SELECT *` expansion.

---

## Distinguish Invalid, Empty, and Successful Results

Use three separate demonstrations:

- a valid fixture query with one or more rows;
- a valid, well-formed query with no fixture matches; and
- a malformed or cross-field-invalid query.

The first two are successful structured results with different `row_count` values. The third is a tool error. Do not treat zero rows as an exception or rewrite an invalid call into a different search on behalf of the caller.

---

## Add Tests That Protect the Intent

Beyond the visible happy paths, useful cases include:

- string-form ASN and ASN boundary values;
- lowercase, too-short, or too-long country codes;
- unexpected input properties;
- coordinate values on and just outside each range;
- minimum equal to maximum and minimum greater than maximum;
- non-finite Python numeric values at the application validation boundary;
- repository parameter order; and
- stable ordering with nullable coordinates in the fixture.

Choose at least one meaningful test per tool. It should catch a plausible broken implementation rather than simply repeat an existing assertion.

---

## What Your Write-Up Should Address

Answer Q6–Q8 with captured calls and test evidence. Explain why the ASN remains an integer, why country is required for geolocation access, where cross-field validation lives, how bound parameters keep caller values out of SQL structure, and how you distinguish a valid empty result from invalid input. Do not paste your complete implementation into the notebook response.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | Task 2 ⮕ | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
