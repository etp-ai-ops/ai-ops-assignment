[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | Task 3 ⮕ | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 3 Guidance: Mutually Exclusive Hostname Selectors

Use this guide with the Task 3 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). This task combines JSON Schema composition, application-level IP validation, defensive repository invariants, and safe SQL pattern matching. Implement the marked regions without replacing the three precise operations with one vague string search.

---

## Model Exactly One Intent

The tool supports three distinct intentions:

| Selector | Meaning | Important validation |
| --- | --- | --- |
| `ip` | records for one interface address | parses as IPv4 or IPv6 |
| `hostname_exact` | records equal to one complete visible-ASCII hostname | 1–253 characters |
| `hostname_prefix` | records beginning with literal visible-ASCII text | 3–253 characters |

Use schema composition so exactly one required-selector branch matches, and keep `additionalProperties: false` at the object boundary. Then preserve the exactly-one invariant in the repository method. This second check protects direct Python callers and documents what the repository expects; it is not permission to weaken schema validation.

Test `{}`, each valid one-selector object, every pair, all three together, and an allowed selector plus an unknown property.

---

## Parse Addresses Instead of Recognizing Their Shape

JSON Schema format validation and Python's IP-address parser work together. Include ordinary and compressed IPv6, ordinary IPv4, out-of-range octets, malformed separators, and strings with leading/trailing decoration in tests.

Do not normalize an arbitrary invalid string into something accepted, and do not silently reinterpret a malformed IP as a hostname. The caller selected the IP intent, so failure should remain `INVALID_ARGUMENT`.

---

## Use Separate Fixed Queries

IP, exact-name, and prefix lookup have different predicates and ordering contracts. Select one fixed query after confirming the invariant; never choose a relation, column, operator, or ordering string supplied by the caller.

The projection is always `ip, hostname`. IP results order by IP and then hostname with nulls first. Exact and prefix results order by hostname and then IP. The caller supplies one data value, and that value is passed separately as a bound parameter.

---

## Escape a Literal Prefix Correctly

SQL `LIKE` assigns special meaning to `%` and `_`; the chosen escape character also needs escaping. Transform caller text in this order:

```text
backslash -> escaped backslash
percent   -> escaped percent
underscore -> escaped underscore
then append one server-owned percent wildcard
```

The fixed SQL statement must name the escape character explicitly. Bind the resulting pattern rather than interpolating it. Ordering the replacements matters: escaping `%` first and then escaping every backslash can also alter the escape characters you just introduced.

Use fixture pairs designed so a wildcard bug is observable. For example, a literal-prefix row and a second row differing only where `_` would match any one character can reveal whether the implementation widened the search. The notebook owns the actual fixture values; do not replace them with this abstract example.

---

## Test at More Than One Boundary

Schema/dispatch tests prove selector combinations and invalid IP behavior. A recording-executor test proves the escaped bound parameter and chosen fixed query. A PostgreSQL fixture test proves the actual `LIKE ... ESCAPE` semantics and stable result ordering. No one of these tests proves all three.

Also test an ordinary prefix so over-escaping does not break normal behavior, plus a prefix at the minimum length and one just below it.

---

## What Your Write-Up Should Address

Answer Q9–Q10 with zero/one/multiple-selector evidence and literal-prefix fixture evidence. Explain the independent roles of schema, application validation, repository invariant, prefix escaping, parameter binding, and stable ordering. Report rows that an unsafe wildcard interpretation would have included, but do not expose the complete implementation as your answer.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | Task 3 ⮕ | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
