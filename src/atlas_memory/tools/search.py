from __future__ import annotations

import json
from typing import Optional

from atlas_memory.storage.database import Database


def search_entities(
    db: Database,
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> str:
    results = db.query_entities(
        keyword=query,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    return json.dumps([e.to_dict() for e in results], ensure_ascii=False)
