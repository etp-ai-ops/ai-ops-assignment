"""The three student-owned MCP tools: schemas, descriptions, queries, dispatch.

Everything you need to write for Part 3 of the assignment lives in this one
file. ``mcp_tools.py`` merges ``STUDENT_TOOL_SCHEMAS`` and
``STUDENT_TOOL_DESCRIPTIONS`` into its own registries and routes any of the
three tool names here through :func:`dispatch`, so you never have to touch
the completed server code to make a new tool discoverable.

Search for ``TODO(student)`` below. For each of ``get_node_geolocation``,
``find_router_links_between_asns``, and ``count_nodes_by_asn_and_country`` you
must:

1. add its restrictive JSON Schema to ``STUDENT_TOOL_SCHEMAS``;
2. add its description to ``STUDENT_TOOL_DESCRIPTIONS``;
3. define a module-level :class:`~itdk_mcp.data_access.query.Query` with fixed
   SQL text, ordered column metadata, and a filename prefix; and
4. execute it from the matching function below with the caller's value(s)
   bound as parameters -- never interpolated into the SQL text.

These three tools are deliberately general-purpose: each takes only ASN(s) or
a node_id and returns raw rows, so an agent (or your own notebook code) can
combine them to answer many different questions -- border routers between any
two ASes, a node's location, or an AS's country footprint -- rather than one
narrow, single-purpose query apiece. The contracts (columns, ordering, SQL
shape) are fixed by ASSIGNMENT.md. Do not invent different column names or
orderings: the tests and the answer key assume exactly these.
"""

from __future__ import annotations

from typing import Any, Final, cast

from psycopg import sql  # noqa: F401  (needed once you define your Query objects)

from .data_access.nodes import GEOLOCATION_COLUMNS  # noqa: F401  (get_node_geolocation reuses these)
from .data_access.query import FixedQueryExecutor, Query  # noqa: F401
from .data_access.result_writer import Column, CsvResult  # noqa: F401

# The same restrictive shapes the four completed tools use. ``node_id`` is a
# 1-255 character string with at least one non-whitespace character and no C0
# or DEL control characters; ``asn`` is the same tightened integer schema as
# ``find_nodes_by_asn``.
MAX_IDENTIFIER_LENGTH: Final = 255
MAX_ASN: Final = 9_223_372_036_854_775_807

IDENTIFIER_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "minLength": 1,
    "maxLength": MAX_IDENTIFIER_LENGTH,
    "pattern": r"^(?=.*\S)[^\x00-\x1f\x7f]+$",
}
ASN_SCHEMA: Final[dict[str, Any]] = {
    "type": "integer",
    "exclusiveMinimum": 0,
    "maximum": MAX_ASN,
}


def _object_schema(properties: dict[str, Any], *, required: list[str]) -> dict[str, Any]:
    """Build the same Draft 2020-12 object schema shape ``mcp_tools.py`` uses."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


# ---------------------------------------------------------------------------
# Discovery: schemas and descriptions
# ---------------------------------------------------------------------------

STUDENT_TOOL_SCHEMAS: Final[dict[str, dict[str, Any]]] = {
    # TODO(student): Add "get_node_geolocation" (one required node_id, using
    # IDENTIFIER_SCHEMA), "find_router_links_between_asns" (two required
    # properties asn_a and asn_b, both ASN_SCHEMA), and
    # "count_nodes_by_asn_and_country" (one required asn, ASN_SCHEMA). Use
    # _object_schema(...) so additionalProperties stays false on all three.
}

STUDENT_TOOL_DESCRIPTIONS: Final[dict[str, str]] = {
    # TODO(student): Add one precise description per tool. Say what the tool
    # returns AND what it excludes -- an agent picks a tool from this text.
    # find_router_links_between_asns in particular must document that passing
    # the same ASN for asn_a and asn_b returns that AS's own intra-network
    # router-level links, not an error -- a caller who does not expect that
    # needs to be told.
}


# ---------------------------------------------------------------------------
# get_node_geolocation(node_id)
#   -> node_id, continent, country, region, city, latitude, longitude, method
#      ordered by node_id (at most one row: node_id is that table's primary key)
# ---------------------------------------------------------------------------

# TODO(student): Define _GET_NODE_GEOLOCATION = Query(sql.SQL(...),
# GEOLOCATION_COLUMNS, "get_node_geolocation") here.


def get_node_geolocation(executor: FixedQueryExecutor, node_id: str) -> CsvResult:
    """Write the single geolocation row for ``node_id``, if one exists."""
    # TODO(student): Complete this vertical slice by defining a fixed Query
    # above and executing it here. Never interpolate node_id into SQL:
    #
    #     SELECT node_id, continent, country, region, city,
    #            latitude, longitude, method
    #     FROM caida_itdk.itdk_node_geolocation
    #     WHERE node_id = %s
    #     ORDER BY node_id
    #
    # node_id is that table's primary key, so this returns zero or one row --
    # zero rows means "no geolocation annotation for this node", not an error.
    raise NotImplementedError("TODO(student): implement get_node_geolocation")


# ---------------------------------------------------------------------------
# find_router_links_between_asns(asn_a, asn_b)
#   -> link_id, node_a, node_b
#      ordered by (link_id, node_a, node_b)
# ---------------------------------------------------------------------------

# TODO(student): Define _FIND_ROUTER_LINKS_BETWEEN_ASNS = Query(...) with
# columns (Column("link_id", "string"), Column("node_a", "string"),
# Column("node_b", "string")) and prefix "find_router_links_between_asns".


def find_router_links_between_asns(
    executor: FixedQueryExecutor, asn_a: int, asn_b: int
) -> CsvResult:
    """Write every router-level link with one endpoint in each ASN."""
    # TODO(student): Define a fixed Query with two CTEs selecting the node_ids
    # assigned to asn_a and asn_b, then self-joining itdk_link_endpoints on
    # link_id (excluding the same endpoint row) to keep only links where one
    # endpoint's node is in the asn_a set and the other endpoint's node is in
    # the asn_b set. Bind asn_a and asn_b as the two %s parameters, in that
    # order. An intended reference query:
    #
    #     WITH a_nodes AS (
    #         SELECT node_id FROM caida_itdk.itdk_node_as WHERE asn = %s
    #     ),
    #     b_nodes AS (
    #         SELECT node_id FROM caida_itdk.itdk_node_as WHERE asn = %s
    #     )
    #     SELECT e1.link_id, e1.node_id AS node_a, e2.node_id AS node_b
    #     FROM caida_itdk.itdk_link_endpoints e1
    #     JOIN a_nodes ON a_nodes.node_id = e1.node_id
    #     JOIN caida_itdk.itdk_link_endpoints e2
    #       ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
    #     JOIN b_nodes ON b_nodes.node_id = e2.node_id
    #     ORDER BY e1.link_id, node_a, node_b
    #
    # Passing the same ASN for both arguments is not rejected: it returns
    # that AS's own intra-network router-level links (both endpoints drawn
    # from the same node set), which is a legitimate, distinct question, not
    # an error condition. Document that in the tool description.
    raise NotImplementedError("TODO(student): implement find_router_links_between_asns")


# ---------------------------------------------------------------------------
# count_nodes_by_asn_and_country(asn)
#   -> country, node_count
#      ordered by (node_count DESC, country)
# ---------------------------------------------------------------------------

# TODO(student): Define _COUNT_NODES_BY_ASN_AND_COUNTRY = Query(...) with
# columns (Column("country", "string"), Column("node_count", "int64")) and
# prefix "count_nodes_by_asn_and_country".


def count_nodes_by_asn_and_country(executor: FixedQueryExecutor, asn: int) -> CsvResult:
    """Write one ASN's geolocated router count, grouped by country."""
    # TODO(student): Define a fixed Query starting from the indexed asn
    # predicate on caida_itdk.itdk_node_as, joining
    # caida_itdk.itdk_node_geolocation on node_id, grouping by country, and
    # counting DISTINCT node_id per group (a node could in principle appear
    # more than once per country if the join fanned out -- COUNT(DISTINCT)
    # keeps the count meaning "routers", not "join rows"). Bind asn as the
    # sole %s parameter. An intended reference query:
    #
    #     SELECT g.country, COUNT(DISTINCT a.node_id) AS node_count
    #     FROM caida_itdk.itdk_node_as a
    #     JOIN caida_itdk.itdk_node_geolocation g ON g.node_id = a.node_id
    #     WHERE a.asn = %s
    #     GROUP BY g.country
    #     ORDER BY node_count DESC, country
    #
    # A node with no geolocation row at all is excluded by this INNER join --
    # this tool answers "how is this AS's *geolocated* footprint
    # distributed", not "how many routers does this AS have in total". Look
    # up the total from find_nodes_by_asn's row_count and compare the two if
    # you need to know how much geolocation coverage is missing.
    raise NotImplementedError("TODO(student): implement count_nodes_by_asn_and_country")


# ---------------------------------------------------------------------------
# Dispatch (complete -- you do not need to edit this)
# ---------------------------------------------------------------------------


def dispatch(
    executor: FixedQueryExecutor, name: str, arguments: dict[str, Any]
) -> CsvResult | None:
    """Route one validated student tool call, or return ``None`` if unknown."""
    if name == "get_node_geolocation":
        return get_node_geolocation(executor, cast(str, arguments["node_id"]))
    if name == "find_router_links_between_asns":
        return find_router_links_between_asns(
            executor, cast(int, arguments["asn_a"]), cast(int, arguments["asn_b"])
        )
    if name == "count_nodes_by_asn_and_country":
        return count_nodes_by_asn_and_country(executor, cast(int, arguments["asn"]))
    return None
