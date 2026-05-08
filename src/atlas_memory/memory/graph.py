from __future__ import annotations

import logging
from pathlib import Path

from atlas_memory.config import Config
from atlas_memory.storage.database import Database
from atlas_memory.parser.code_parser import CodeParser
from atlas_memory.models.entities import Entity, Relation

logger = logging.getLogger(__name__)


class GraphEngine:
    def __init__(self, config: Config, db: Database, vector=None):
        self._config = config
        self._db = db
        self._vector = vector
        self._parser = CodeParser()

    def index_project(self, root_path: str | None = None):
        root = Path(root_path or self._config.project_root)
        if not root.exists():
            return 0

        count = 0
        max_size = self._config.max_index_file_size_kb * 1024
        for filepath in root.rglob("*.py"):
            if filepath.stat().st_size > max_size:
                continue
            try:
                entities, relations = self._parser.parse_file(filepath)
                for e in entities:
                    self._db.upsert_entity(e)
                    if self._vector is not None:
                        self._vector.index_entity(e)
                for r in relations:
                    self._db.add_relation(r)
                count += 1
            except Exception as e:
                logger.warning("Failed to index %s: %s", filepath, e)
        return count

    def index_file(self, filepath: str | Path):
        path = Path(filepath)
        entities, relations = self._parser.parse_file(path)
        for e in entities:
            self._db.upsert_entity(e)
            if self._vector is not None:
                self._vector.index_entity(e)
        for r in relations:
            self._db.add_relation(r)
        return len(entities)

    def get_callers(self, entity_id: str) -> list[Entity]:
        relations = self._db.get_relations(entity_id, direction="in", relation_type="calls")
        results = []
        for r in relations:
            caller = self._db.get_entity(r.from_id)
            if caller is not None:
                results.append(caller)
        return results

    def get_dependencies(self, entity_id: str) -> list[Entity]:
        relations = self._db.get_relations(entity_id, direction="out", relation_type="calls")
        results = []
        for r in relations:
            dep = self._db.get_entity(r.to_id)
            if dep is not None:
                results.append(dep)
        return results
