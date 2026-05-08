from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

from atlas_memory.config import Config
from atlas_memory.models.entities import Entity, Relation, Observation


CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    signature TEXT,
    docstring TEXT,
    created_at INTEGER,
    updated_at INTEGER,
    access_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    type TEXT NOT NULL,
    FOREIGN KEY (from_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at INTEGER,
    access_count INTEGER DEFAULT 0,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_path ON entities(path);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_id);
CREATE INDEX IF NOT EXISTS idx_relations_to ON relations(to_id);
CREATE INDEX IF NOT EXISTS idx_observations_entity ON observations(entity_id);
"""


class Database:
    def __init__(self, config: Config):
        self._config = config
        db_file = Path(config.memory_db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_file))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()

    def _init_tables(self):
        self._conn.executescript(CREATE_TABLES)

    def close(self):
        self._conn.close()

    # ---- Entity CRUD ----

    def upsert_entity(self, entity: Entity) -> Entity:
        now = int(time.time())
        entity.updated_at = now
        if entity.created_at == 0:
            entity.created_at = now
        row = {
            "id": entity.id,
            "type": entity.type.value,
            "name": entity.name,
            "path": entity.path,
            "line_start": entity.line_start,
            "line_end": entity.line_end,
            "signature": entity.signature,
            "docstring": entity.docstring,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "access_count": entity.access_count,
        }
        self._conn.execute(
            """INSERT INTO entities (id, type, name, path, line_start, line_end,
               signature, docstring, created_at, updated_at, access_count)
               VALUES (:id, :type, :name, :path, :line_start, :line_end,
               :signature, :docstring, :created_at, :updated_at, :access_count)
               ON CONFLICT(id) DO UPDATE SET
               type=excluded.type, name=excluded.name, path=excluded.path,
               line_start=excluded.line_start, line_end=excluded.line_end,
               signature=excluded.signature, docstring=excluded.docstring,
               updated_at=excluded.updated_at, access_count=excluded.access_count""",
            row,
        )
        self._conn.commit()
        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        row = self._conn.execute(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        if row is None:
            return None
        self._bump_access("entities", entity_id)
        return Entity.from_row(dict(row))

    def query_entities(
        self,
        keyword: Optional[str] = None,
        entity_type: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Entity]:
        clauses = []
        params: list = []
        if keyword:
            clauses.append("(name LIKE ? OR path LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if entity_type:
            clauses.append("type = ?")
            params.append(entity_type)
        if path:
            clauses.append("path LIKE ?")
            params.append(f"%{path}%")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM entities{where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self._conn.execute(sql, params).fetchall()
        return [Entity.from_row(dict(r)) for r in rows]

    def delete_entity(self, entity_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # ---- Relation CRUD ----

    def add_relation(self, relation: Relation) -> Relation:
        cur = self._conn.execute(
            "INSERT INTO relations (from_id, to_id, type) VALUES (?, ?, ?)",
            (relation.from_id, relation.to_id, relation.type.value),
        )
        self._conn.commit()
        relation.id = cur.lastrowid
        return relation

    def get_relations(
        self,
        entity_id: str,
        direction: str = "both",
        relation_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[Relation]:
        if direction == "out":
            where = "r.from_id = ?"
        elif direction == "in":
            where = "r.to_id = ?"
        else:
            where = "(r.from_id = ? OR r.to_id = ?)"

        params: list = [entity_id]
        if direction == "both":
            params.append(entity_id)

        if relation_type:
            where += " AND r.type = ?"
            params.append(relation_type)

        sql = f"SELECT r.* FROM relations r WHERE {where} LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [Relation.from_row(dict(r)) for r in rows]

    # ---- Observation CRUD ----

    def add_observation(self, observation: Observation) -> Observation:
        now = int(time.time())
        if observation.created_at == 0:
            observation.created_at = now
        cur = self._conn.execute(
            "INSERT INTO observations (entity_id, content, source, created_at, access_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                observation.entity_id,
                observation.content,
                observation.source,
                observation.created_at,
                observation.access_count,
            ),
        )
        self._conn.commit()
        observation.id = cur.lastrowid
        return observation

    def get_observations(
        self,
        entity_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Observation]:
        rows = self._conn.execute(
            "SELECT * FROM observations WHERE entity_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (entity_id, limit, offset),
        ).fetchall()
        return [Observation.from_row(dict(r)) for r in rows]

    # ---- Helpers ----

    def _bump_access(self, table: str, entity_id: str):
        if table == "entities":
            self._conn.execute(
                "UPDATE entities SET access_count = access_count + 1, updated_at = ? WHERE id = ?",
                (int(time.time()), entity_id),
            )
            self._conn.commit()

    def count_entities(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

    def execute(self, sql: str, params: tuple = ()):
        return self._conn.execute(sql, params)

    def commit(self):
        self._conn.commit()
