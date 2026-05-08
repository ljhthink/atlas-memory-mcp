from __future__ import annotations

import json
from typing import Optional

from atlas_memory.storage.database import Database


def get_relations(
    db: Database,
    entity_id: str,
    direction: str = "both",
    relation_type: Optional[str] = None,
    limit: int = 20,
) -> str:
    results = db.get_relations(
        entity_id=entity_id,
        direction=direction,
        relation_type=relation_type,
        limit=limit,
    )
    return json.dumps([r.to_dict() for r in results], ensure_ascii=False)
