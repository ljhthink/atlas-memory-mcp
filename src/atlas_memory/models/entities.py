from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class EntityType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    FILE = "file"
    MODULE = "module"
    VARIABLE = "variable"


class RelationType(str, Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"


def _now() -> int:
    return int(time.time())


@dataclass
class Entity:
    id: str
    type: EntityType
    name: str
    path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    created_at: int = field(default_factory=_now)
    updated_at: int = field(default_factory=_now)
    access_count: int = 0

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "docstring": self.docstring,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row: dict) -> Entity:
        return cls(
            id=row["id"],
            type=EntityType(row["type"]),
            name=row["name"],
            path=row["path"],
            line_start=row.get("line_start"),
            line_end=row.get("line_end"),
            signature=row.get("signature"),
            docstring=row.get("docstring"),
            created_at=row.get("created_at", 0),
            updated_at=row.get("updated_at", 0),
            access_count=row.get("access_count", 0),
        )


@dataclass
class Relation:
    from_id: str
    to_id: str
    type: RelationType
    id: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "type": self.type.value,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row: dict) -> Relation:
        return cls(
            id=row.get("id"),
            from_id=row["from_id"],
            to_id=row["to_id"],
            type=RelationType(row["type"]),
        )


@dataclass
class Observation:
    entity_id: str
    content: str
    source: str = "agent"
    created_at: int = field(default_factory=_now)
    access_count: int = 0
    id: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "entity_id": self.entity_id,
            "content": self.content,
            "source": self.source,
            "created_at": self.created_at,
            "access_count": self.access_count,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row: dict) -> Observation:
        return cls(
            id=row.get("id"),
            entity_id=row["entity_id"],
            content=row["content"],
            source=row.get("source", "agent"),
            created_at=row.get("created_at", 0),
            access_count=row.get("access_count", 0),
        )
