"""Construction point for the complete approved repository surface."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from .hostnames import HostnameRepository
from .links import LinkRepository
from .nodes import NodeRepository
from .pool import DatabasePool
from .query import FixedQueryExecutor
from .result_writer import CsvResultWriter
from .topology import TopologyRepository


@dataclass(frozen=True, slots=True)
class Repositories:
    nodes: NodeRepository
    links: LinkRepository
    hostnames: HostnameRepository
    topology: TopologyRepository

    @classmethod
    def from_settings(cls, settings: Settings, pool: DatabasePool) -> Repositories:
        executor = FixedQueryExecutor(pool, CsvResultWriter(settings.output_dir))
        return cls(
            nodes=NodeRepository(executor),
            links=LinkRepository(executor),
            hostnames=HostnameRepository(executor),
            topology=TopologyRepository(executor),
        )
