"""
Database Schemas for Mindmap App

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class MindmapNode(BaseModel):
    id: str = Field(..., description="Client-generated node id")
    label: str = Field(..., description="Text inside the node")
    x: float = Field(0, description="X position on canvas")
    y: float = Field(0, description="Y position on canvas")
    parentId: Optional[str] = Field(None, description="Optional parent node id")

class Mindmap(BaseModel):
    """
    Mindmaps collection schema
    Collection name: "mindmap"
    """
    title: str = Field(..., description="Mindmap title")
    nodes: List[MindmapNode] = Field(default_factory=list, description="All nodes in the map")
