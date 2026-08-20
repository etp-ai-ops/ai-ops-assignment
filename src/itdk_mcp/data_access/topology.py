"""Student-owned cross-relation topology queries.

Neither method here is wired up yet: there is no ``TOOL_SCHEMAS`` entry, no
``TOOL_DESCRIPTIONS`` entry, and no dispatch branch in ``mcp_tools.py`` for
either tool -- mirroring exactly how ``LinkRepository.find_links_for_node``
is stubbed. Design a restrictive schema, application validation, and a
fixed, parameterized query for each, following the conventions worked out in
``get_link_endpoints`` and the three completed lookup tools.
"""

from __future__ import annotations

from .query import FixedQueryExecutor
from .result_writer import CsvResult


class TopologyRepository:
    def __init__(self, executor: FixedQueryExecutor) -> None:
        self._executor = executor

    def find_peer_asns_for_node(self, node_id: str) -> CsvResult:
        """Write the distinct ASNs adjacent to ``node_id`` across its links."""
        # TODO(student): Define a fixed Query self-joining
        # caida_itdk.itdk_link_endpoints on link_id (excluding the seed
        # node_id's own row) and joining caida_itdk.itdk_node_as on the peer
        # node_id. Bind node_id as the sole %s parameter. Project
        # peer_node_id, peer_asn, peer_method as DISTINCT rows ordered by
        # (peer_node_id, peer_asn). An intended reference query:
        #
        #     SELECT DISTINCT e2.node_id AS peer_node_id,
        #            a2.asn AS peer_asn, a2.method AS peer_method
        #     FROM caida_itdk.itdk_link_endpoints e1
        #     JOIN caida_itdk.itdk_link_endpoints e2
        #       ON e2.link_id = e1.link_id AND e2.node_id <> e1.node_id
        #     JOIN caida_itdk.itdk_node_as a2 ON a2.node_id = e2.node_id
        #     WHERE e1.node_id = %s
        #     ORDER BY peer_node_id, peer_asn
        #
        # Note the INNER join on itdk_node_as excludes peers with no AS
        # assignment row -- document that tradeoff.
        raise NotImplementedError("TODO(student): implement find_peer_asns_for_node")

    def find_hostnames_for_asn(self, asn: int) -> CsvResult:
        """Write the distinct (node_id, ip, hostname) triples observed for one ASN."""
        # TODO(student): Define a fixed Query starting from the indexed asn
        # predicate on caida_itdk.itdk_node_as, joining
        # caida_itdk.itdk_link_endpoints on node_id, then parsing the
        # embedded interface address out of endpoint_token to join
        # caida_itdk.itdk_router_hostnames on ip. Bind asn as the sole %s
        # parameter. Project DISTINCT node_id, ip, hostname ordered by
        # (node_id, ip NULLS FIRST, hostname). An intended reference query:
        #
        #     SELECT DISTINCT le.node_id, h.ip, h.hostname
        #     FROM caida_itdk.itdk_node_as a
        #     JOIN caida_itdk.itdk_link_endpoints le ON le.node_id = a.node_id
        #     JOIN caida_itdk.itdk_router_hostnames h
        #       ON h.ip = CASE WHEN strpos(le.endpoint_token, ':') > 0
        #                      THEN substring(le.endpoint_token FROM strpos(le.endpoint_token, ':') + 1)::inet
        #                 END
        #     WHERE a.asn = %s
        #     ORDER BY le.node_id, h.ip NULLS FIRST, h.hostname
        #
        # Do NOT use split_part(endpoint_token, ':', 2)/NULLIF/::inet here:
        # split_part only returns the text between the FIRST and SECOND
        # colon, which truncates an IPv6 token like "N1:2001:db8:1::1" down
        # to just "2001" and fails the ::inet cast. strpos/substring finds
        # the first colon and takes everything after it, which works for
        # both IPv4 and IPv6 tokens. Note the INNER joins exclude interfaces
        # with no PTR row and bare endpoint_token values with no embedded IP
        # (e.g. fixture L2's bare "N2" token) -- document that tradeoff.
        raise NotImplementedError("TODO(student): implement find_hostnames_for_asn")
