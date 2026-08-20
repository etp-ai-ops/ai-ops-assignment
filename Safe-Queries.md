[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | Safe Queries ⮕ | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Safe Query Guide

This assignment does not ask you to build a general SQL service. It asks you to encode a small number of approved analytical intents as deterministic, read-only operations. The difference is central: callers supply data values, while the package owns every piece of SQL structure.

## 1. Fix the Query Shape

A repository query fixes all of the following in source code:

- the schema and relation;
- projected columns;
- joins and predicates;
- sort keys and null ordering;
- output column names and types; and
- the filename prefix.

Inputs may choose only documented values such as one ASN, country, coordinate bound, node ID, link ID, IP, or hostname selector. Do not accept raw SQL, relation names, columns, operators, joins, `ORDER BY`, `LIMIT`, or cursor text from a caller.

## 2. Bind Values Separately

Pass data values separately from the SQL statement. In psycopg, placeholders are `%s` regardless of the Python value's type:

```python
statement = sql.SQL("""
    SELECT sample_id, label
    FROM teaching.example
    WHERE sample_id = %s
    ORDER BY sample_id
""")
parameters = (sample_id,)
```

This toy example demonstrates the pattern without implementing an assignment query. Do not use string concatenation, f-strings, `.format()`, or interpolation to place a caller's value into SQL text. Quoting a value yourself is not a substitute for binding it.

> **Gotcha:** SQL identifiers and SQL values are different. A parameter placeholder can bind a value, not safely grant the caller a choice of table or column. This assignment does not need caller-chosen identifiers at all.

## 3. Project and Order Explicitly

Use explicit columns instead of `SELECT *`. The projection is part of both the privacy boundary and the MCP output contract. Pair it with column metadata in the same order.

Relational results have no guaranteed order without `ORDER BY`. Stable ordering makes tests reproducible, helps a student compare runs, and prevents an agent from treating incidental database order as meaningful. When nullable values participate in ordering, state `NULLS FIRST` or `NULLS LAST` rather than relying on a default.

## 4. Start With an Indexed Predicate

The teaching relations are large enough that unconstrained scans can harm a shared classroom service. The supplied operations begin from approved indexed access paths:

| Intent | Required seed/access path |
| --- | --- |
| nodes assigned to an AS | `asn` |
| nodes in a geographic area | `country`, optionally narrowed by coordinate bounds |
| endpoints of one link | `link_id` |
| links containing one node | `node_id` |
| hostname lookup | one IP, exact hostname, or sufficiently long hostname prefix |

The composite geolocation index begins with `country`, so a longitude-only tool would not meet the intended access pattern. This is why `country` remains required even when bounds are supplied. Classroom scale is controlled with vetted seeds, a frozen subset, timeouts, quotas, and pooling—not caller-controlled query fragments or arbitrary row limits.

## 5. Validate Numeric Bounds Twice

JSON Schema expresses individual longitude and latitude ranges, but the application must also reject non-finite numeric values and cross-field inversions. For any optional pair:

```text
if both minimum and maximum are present:
    require minimum <= maximum
```

Longitude is restricted to `[-180, 180]`; latitude is restricted to `[-90, 90]`. A country is exactly two uppercase ASCII letters. Validation belongs before dispatch, while the fixed repository remains safe even if called directly in a unit test.

## 6. Make Selectors Mutually Exclusive

Hostname lookup accepts exactly one of:

- `ip` — a value that parses as IPv4 or IPv6;
- `hostname_exact` — one exact visible-ASCII hostname string; or
- `hostname_prefix` — a visible-ASCII prefix from 3 through 253 characters.

Reject calls with zero selectors and calls with two or three. Also reject extra properties. Enforce this in the advertised schema and preserve the invariant at the repository boundary so direct callers cannot accidentally trigger ambiguous behavior.

## 7. Escape Literal Prefixes

In SQL `LIKE`, `%` matches any sequence, `_` matches one character, and backslash is commonly used as the escape character. A client requesting a hostname prefix containing any of these characters is asking for literal text, not permission to widen the search.

Use this order:

1. escape backslash;
2. escape `%`;
3. escape `_`;
4. append the server-owned `%` wildcard; and
5. use an explicit SQL `ESCAPE` clause.

For illustration, an unrelated input `lab_5%\edge` should become a pattern whose `_`, `%`, and `\` are literals, followed only by the server's final prefix wildcard. Write tests that distinguish this behavior from wildcard expansion.

## 8. Preserve Read-Only Defense in Depth

Safety does not depend on one check. This assignment combines:

- a small allowlist of MCP tools;
- restrictive input schemas and application validation;
- fixed, parameterized `SELECT` statements;
- repository methods with narrow signatures;
- a database role with explicit `SELECT` access only to approved relations;
- statement timeouts and conservative connection pools; and
- generic public errors with sanitized logging.

A passing unit test cannot compensate for a writable database role, and a read-only role cannot make an unbounded, ill-designed query appropriate. Keep every layer narrow.

## 9. Review Checklist

For each student-owned query, ask:

- Is every SQL keyword, relation, column, predicate, join, and ordering choice package-owned?
- Are all caller values separately bound?
- Does the query start from the intended indexable filter?
- Are the selected columns and column metadata exact and ordered?
- Is the output order deterministic, including null handling?
- Can an invalid selector or range reach the executor?
- Does a prefix containing `%`, `_`, or backslash remain literal?
- Can the operation write to the database or reveal internal errors?

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | Safe Queries ⮕ | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
