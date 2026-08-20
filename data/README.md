[README](../README.md) | [Assignment](../ASSIGNMENT.md) | Fixture Data | [Notebook](../nids-itdk-mcp.ipynb)

# Synthetic Fixture Data

The local environment provisions `nids-itdk-mcp-synthetic-v1`, a deterministic,
invented dataset for development and automated feedback. It has the same four-table
teaching schema described in [ASSIGNMENT.md](../ASSIGNMENT.md), but none of its records come
from a CAIDA ITDK release. Do not interpret fixture results as observations about the
public Internet.

## Files

- `fixture-manifest.json` records the fixture identifier, row counts, and stable seeds.
- `initdb/001_schema_fixture.sql` creates the schema, indexes, invented rows, and a
  database role with `SELECT` access only to the approved tables.

Docker Compose loads the SQL file only when it initializes a new database volume. If
an instructor changes the fixture, they must also change the fixture identifier and
manifest rather than silently reusing `nids-itdk-mcp-synthetic-v1`.

## Stable Local Seeds

The starter notebook uses ASN `64500`, countries `US` and `DE`, nodes `N1` and `N2`,
and link `L1`. The fixture also includes IPv4 and IPv6 endpoints, a multipoint link,
an endpoint without an interface encoding, missing geolocation fields, an IP without
a PTR row, and hostnames containing literal `%`, `_`, and backslash characters.

These values are safe for local development. For a graded ITDK snapshot, the
instructor must replace them with preflighted seeds and publish the snapshot ID,
source/access terms, subset procedure, schema version, checksums, expected runtime,
result-size limits, retention policy, and cleanup procedure.

## Resetting the Local Fixture

The database is persistent by design. To rebuild it, use the course-approved reset
procedure before deleting the Compose volume; resetting removes all local fixture
state. Generated CSVs live under `outputs/`, are git-ignored, and should be cleaned up
according to the course retention policy.

[README](../README.md) | [Assignment](../ASSIGNMENT.md) | Fixture Data | [Notebook](../nids-itdk-mcp.ipynb)
