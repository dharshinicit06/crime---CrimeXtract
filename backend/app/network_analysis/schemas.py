"""Graph JSON schemas for criminal network visualization."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """A single node in the criminal network graph."""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Entity type: accused, victim, fir, location, crime_type, phone, vehicle, bank_account")
    group: Optional[str] = Field(None, description="Group/category for color-coding")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional node attributes")


class GraphEdge(BaseModel):
    """A directed/undirected edge connecting two nodes."""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(..., description="Relationship type label")
    weight: float = Field(1.0, description="Edge weight / connection strength")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional edge attributes")


class NetworkStatistics(BaseModel):
    """Summary statistics for the criminal network."""
    total_criminals: int = Field(0, description="Unique accused persons")
    total_connections: int = Field(0, description="Total edges/relationships")
    total_nodes: int = Field(0, description="Total graph nodes")
    total_edges: int = Field(0, description="Total graph edges")
    largest_network: int = Field(0, description="Nodes in the largest connected component")
    active_networks: int = Field(0, description="Number of distinct connected components")
    top_association: str = Field("", description="Most common relationship type")
    repeat_offenders: int = Field(0, description="Accused linked to 2+ FIRs")


class GraphResponse(BaseModel):
    """Complete graph payload for network visualization libraries."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    total_nodes: int = Field(0)
    total_edges: int = Field(0)
    statistics: Optional[NetworkStatistics] = Field(None, description="Network statistics")
    metadata: Optional[dict[str, Any]] = Field(None, description="Graph-level metadata")


class CriminalNetworkDetail(BaseModel):
    """Subgraph focused on a single criminal and their connections."""
    accused: dict[str, Any] = Field(..., description="Accused person details")
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    total_nodes: int = Field(0)
    total_edges: int = Field(0)
    co_accused_count: int = Field(0, description="Number of co-accused")
    fir_count: int = Field(0, description="Number of linked FIRs")
    total_crime_count: int = Field(0, description="Total crimes linked")
