from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class Node(SQLModel, table=True):
    id: str = Field(primary_key=True)
    hostname: str
    os: str
    capabilities: str  # JSON string

class Agent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    node_id: str = Field(foreign_key="node.id")
    role: str
    operator: Optional[str] = None
    version: Optional[str] = None
    status: str
    last_seen: datetime
    parent_id: Optional[str] = None

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender: str  # from
    target: str  # to
    topic: str
    payload: str  # JSON string
    state: str  # delivered, pending, error

