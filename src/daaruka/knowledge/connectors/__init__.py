"""Connectors package exposing SoilGrids and GBIF thin clients."""

from daaruka.knowledge.connectors.base import BaseConnector
from daaruka.knowledge.connectors.soilgrids import SoilGridsClient
from daaruka.knowledge.connectors.gbif import GBIFClient

__all__ = ["BaseConnector", "SoilGridsClient", "GBIFClient"]
