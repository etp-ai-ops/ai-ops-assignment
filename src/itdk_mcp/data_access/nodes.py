"""Fixed node ASN and geolocation queries.

Both tools are complete, fully-worked examples of the fixed, parameterized
query pattern described in ASSIGNMENT.md section 3: the SQL text never changes
between calls, every caller value is bound as a separate parameter, and the
projected columns and ordering match ASSIGNMENT.md's "The seven tools"
table exactly.
"""

from __future__ import annotations

from psycopg import sql

from .query import FixedQueryExecutor, Query
from .result_writer import Column, CsvResult

NODE_AS_COLUMNS = (
    Column("node_id", "string"),
    Column("asn", "int64"),
    Column("method", "string"),
)

_FIND_NODES_BY_ASN = Query(
    sql.SQL("""
        SELECT node_id, asn, method
        FROM caida_itdk.itdk_node_as
        WHERE asn = %s
        ORDER BY node_id
    """),
    NODE_AS_COLUMNS,
    "find_nodes_by_asn",
)

GEOLOCATION_COLUMNS = (
    Column("node_id", "string"),
    Column("continent", "string"),
    Column("country", "string"),
    Column("region", "string"),
    Column("city", "string"),
    Column("latitude", "float64"),
    Column("longitude", "float64"),
    Column("method", "string"),
)

# The country predicate is always present (it leads the composite index), and
# every optional bound is expressed as `(%s IS NULL OR column op %s)` so the
# SQL text itself never changes shape based on which bounds a caller supplied
# -- only the bound parameter values do. Each optional bound is therefore
# bound twice: once for the NULL check, once for the comparison. Both
# occurrences are cast to `double precision` explicitly: a bare `%s IS NULL`
# gives Postgres no operator context to infer that parameter's type from, so
# a caller that omits every bound (e.g. `{"country": "US"}` alone, the
# common case) makes every bound parameter NULL with no inferable type at
# all, and the query fails with `IndeterminateDatatype` before any row is
# ever read.
_SEARCH_NODES_BY_GEOLOCATION = Query(
    sql.SQL("""
        SELECT node_id, continent, country, region, city, latitude, longitude, method
        FROM caida_itdk.itdk_node_geolocation
        WHERE country = %s
          AND (%s::double precision IS NULL OR longitude >= %s::double precision)
          AND (%s::double precision IS NULL OR longitude <= %s::double precision)
          AND (%s::double precision IS NULL OR latitude >= %s::double precision)
          AND (%s::double precision IS NULL OR latitude <= %s::double precision)
        ORDER BY country, longitude NULLS FIRST, latitude NULLS FIRST, node_id
    """),
    GEOLOCATION_COLUMNS,
    "search_nodes_by_geolocation",
)


class NodeRepository:
    def __init__(self, executor: FixedQueryExecutor) -> None:
        self._executor = executor

    def find_nodes_by_asn(self, asn: int) -> CsvResult:
        """Write nodes assigned to one ASN in stable node order."""
        return self._executor.execute(_FIND_NODES_BY_ASN, (asn,))

    def search_nodes_by_geolocation(
        self,
        country: str,
        *,
        longitude_min: float | None = None,
        longitude_max: float | None = None,
        latitude_min: float | None = None,
        latitude_max: float | None = None,
    ) -> CsvResult:
        """Write country-matching nodes within optional coordinate bounds."""
        parameters = (
            country,
            longitude_min,
            longitude_min,
            longitude_max,
            longitude_max,
            latitude_min,
            latitude_min,
            latitude_max,
            latitude_max,
        )
        return self._executor.execute(_SEARCH_NODES_BY_GEOLOCATION, parameters)
