from __future__ import annotations

import json

from atlas_memory.models.entities import Observation
from atlas_memory.storage.database import Database


def list_observations(
    db: Database,
    entity_id: str,
    limit: int = 10,
    offset: int = 0,
) -> str:
    results = db.get_observations(
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return json.dumps([o.to_dict() for o in results], ensure_ascii=False)


def add_observation(
    db: Database,
    entity_id: str,
    content: str,
    source: str = "agent",
) -> str:
    obs = Observation(
        entity_id=entity_id,
        content=content,
        source=source,
    )
    result = db.add_observation(obs)
    return json.dumps(result.to_dict(), ensure_ascii=False)
