"""The three student-owned MCP tools: schemas, descriptions, queries, dispatch.

Everything you need to write for Part 3 of the assignment lives in this one
file. ``mcp_tools.py`` merges ``STUDENT_TOOL_SCHEMAS`` and
``STUDENT_TOOL_DESCRIPTIONS`` into its own registries and routes any of the
three tool names here through :func:`dispatch`, so you never have to touch
the completed server code to make a new tool discoverable.

Search for ``TODO(student)`` below. For each of ``find_links_for_node``,
``find_peer_asns_for_node``, and ``find_hostnames_for_asn`` you must:

1. add its restrictive JSON Schema to ``STUDENT_TOOL_SCHEMAS``;
2. add its description to ``STUDENT_TOOL_DESCRIPTIONS``;
3. define a module-level :class:`~itdk_mcp.data_access.query.Query` with fixed
   SQL text, ordered column metadata, and a filename prefix; and
4. execute it from the matching function below with the caller's value bound
   as a parameter -- never interpolated into the SQL text.

The contracts (columns, ordering, SQL shape) are fixed by ASSIGNMENT.md. Do
not invent different column names or orderings: the tests and the answer key
assume exactly these.
"""

from __future__ import annotations

from typing import Any, Final, cast

from psycopg import sql  # noqa: F401  (needed once you define your Query objects)

from .data_access.links import LINK_COLUMNS  # noqa: F401  (find_links_for_node reuses these)
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
    "find_links_for_node": _object_schema({"node_id": IDENTIFIER_SCHEMA}, required=["node_id"]),
    "find_peer_asns_for_node": _object_schema(
        {"node_id": IDENTIFIER_SCHEMA}, required=["node_id"]
    ),
    "find_hostnames_for_asn": _object_schema({"asn": ASN_SCHEMA}, required=["asn"]),
}

STUDENT_TOOL_DESCRIPTIONS: Final[dict[str, str]] = {
    "find_links_for_node": (
        "Write every link-endpoint record whose node_id is this node to CSV. Returns only "
        "that node's own endpoint rows (link_id, endpoint_ordinal, endpoint_token, node_id), "
        "not the other endpoints of those links; pass each returned link_id to "
        "get_link_endpoints to see a link's full endpoint set."
    ),
    "find_peer_asns_for_node": (
        "Write the distinct ASNs adjacent to this node across its links to CSV, as "
        "(peer_node_id, peer_asn, peer_method). A peer node with no AS-assignment row is "
        "excluded entirely rather than reported with a null ASN; this answers 'which known "
        "ASNs neighbor this node', not 'who are all of this node's neighbors'."
    ),
    "find_hostnames_for_asn": (
        "Write the distinct (node_id, ip, hostname) triples observed for nodes assigned to "
        "this ASN to CSV. An interface with no PTR record, or an endpoint whose token carries "
        "no embedded address, is excluded rather than returned with a null hostname; this "
        "answers 'which hostnames are we confident belong to a node in this ASN', not 'does "
        "every node in this ASN have an interface'."
    ),
}


# ---------------------------------------------------------------------------
# find_links_for_node(node_id)
#   -> link_id, endpoint_ordinal, endpoint_token, node_id
#      ordered by (link_id, endpoint_ordinal)
# ---------------------------------------------------------------------------

_FIND_LINKS_FOR_NODE = Query(
    sql.SQL("""
        SELECT link_id, endpoint_ordinal, endpoint_token, node_id
        FROM caida_itdk.itdk_link_endpoints
        WHERE node_id = %s
        ORDER BY link_id, endpoint_ordinal
    """),
    LINK_COLUMNS,
    "find_links_for_node",
)


def find_links_for_node(executor: FixedQueryExecutor, node_id: str) -> CsvResult:
    """Write all link-endpoint records that contain ``node_id``."""
    # Filtering endpoint rows by one node answers "which endpoint records
    # contain this node?" -- it does not return every endpoint on those links.
    return executor.execute(_FIND_LINKS_FOR_NODE, (node_id,))


# ---------------------------------------------------------------------------
# find_peer_asns_for_node(node_id)
#   -> DISTINCT peer_node_id, peer_asn, peer_method
#      ordered by (peer_node_id, peer_asn)
# ---------------------------------------------------------------------------

_FIND_PEER_ASNS_FOR_NODE = Query(
    sql.SQL("""
        SELECT DISTINCT e2.node_id AS peer_node_id,
               a2.asn AS peer_asn, a2.method AS peer_method
        FROM caida_itdk.itdk_link_endpoints e1
        JOIN caida_itdk.itdk_link_endpoints e2
          ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
        JOIN caida_itdk.itdk_node_as a2 ON a2.node_id = e2.node_id
        WHERE e1.node_id = %s
        ORDER BY peer_node_id, peer_asn
    """),
    (
        Column("peer_node_id", "string"),
        Column("peer_asn", "int64"),
        Column("peer_method", "string"),
    ),
    "find_peer_asns_for_node",
)


def find_peer_asns_for_node(executor: FixedQueryExecutor, node_id: str) -> CsvResult:
    """Write the distinct ASNs adjacent to ``node_id`` across its links."""
    # DISTINCT collapses the fan-out from a node sitting on more than one
    # link to the same peer. The INNER join on itdk_node_as excludes peers
    # with no AS assignment row rather than reporting a null ASN.
    return executor.execute(_FIND_PEER_ASNS_FOR_NODE, (node_id,))


# ---------------------------------------------------------------------------
# find_hostnames_for_asn(asn)
#   -> DISTINCT node_id, ip, hostname
#      ordered by (node_id, ip NULLS FIRST, hostname)
# ---------------------------------------------------------------------------

_FIND_HOSTNAMES_FOR_ASN = Query(
    sql.SQL("""
        SELECT DISTINCT le.node_id, h.ip, h.hostname
        FROM caida_itdk.itdk_node_as a
        JOIN caida_itdk.itdk_link_endpoints le ON le.node_id = a.node_id
        JOIN caida_itdk.itdk_router_hostnames h
          ON h.ip = CASE WHEN strpos(le.endpoint_token, ':') > 0
                         THEN substring(le.endpoint_token FROM strpos(le.endpoint_token, ':') + 1)::inet
                    END
        WHERE a.asn = %s
        ORDER BY le.node_id, h.ip NULLS FIRST, h.hostname
    """),
    (
        Column("node_id", "string"),
        Column("ip", "inet"),
        Column("hostname", "string"),
    ),
    "find_hostnames_for_asn",
)


def find_hostnames_for_asn(executor: FixedQueryExecutor, asn: int) -> CsvResult:
    """Write the distinct (node_id, ip, hostname) triples observed for one ASN."""
    # Do NOT use split_part(endpoint_token, ':', 2)/NULLIF/::inet here:
    # split_part only returns the text between the FIRST and SECOND
    # colon, which truncates an IPv6 token like "N1:2001:db8:1::1" down
    # to just "2001" and fails the ::inet cast. strpos/substring finds
    # the first colon and takes everything after it, which works for
    # both IPv4 and IPv6 tokens. The INNER joins exclude interfaces with
    # no PTR row and bare endpoint_token values with no embedded IP (e.g.
    # fixture L2's bare "N2" token).
    return executor.execute(_FIND_HOSTNAMES_FOR_ASN, (asn,))


# ---------------------------------------------------------------------------
# Dispatch (complete -- you do not need to edit this)
# ---------------------------------------------------------------------------


def dispatch(
    executor: FixedQueryExecutor, name: str, arguments: dict[str, Any]
) -> CsvResult | None:
    """Route one validated student tool call, or return ``None`` if unknown."""
    if name == "find_links_for_node":
        return find_links_for_node(executor, cast(str, arguments["node_id"]))
    if name == "find_peer_asns_for_node":
        return find_peer_asns_for_node(executor, cast(str, arguments["node_id"]))
    if name == "find_hostnames_for_asn":
        return find_hostnames_for_asn(executor, cast(int, arguments["asn"]))
    return None
