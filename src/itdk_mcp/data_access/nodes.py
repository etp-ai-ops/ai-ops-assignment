"""Student-owned fixed node ASN and geolocation queries."""

from __future__ import annotations

from .query import FixedQueryExecutor
from .result_writer import CsvResult


class NodeRepository:
    def __init__(self, executor: FixedQueryExecutor) -> None:
        self._executor = executor

    def find_nodes_by_asn(self, asn: int) -> CsvResult:
        """Write nodes assigned to one ASN in stable node order."""
        # TODO(student): Define a module-level Query selecting node_id, asn,
        # and method from caida_itdk.itdk_node_as. Bind asn as the sole %s
        # parameter and order by node_id.
        raise NotImplementedError("TODO(student): implement find_nodes_by_asn")

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
        # TODO(student): Define and execute a fixed Query over
        # caida_itdk.itdk_node_geolocation. Keep `country = %s` as the leading
        # predicate, bind every value, return the documented eight columns, and
        # use deterministic country/longitude/latitude/node ordering.
        raise NotImplementedError("TODO(student): implement search_nodes_by_geolocation")
