from __future__ import annotations

import json

from atlas_memory.models.entities import Entity, EntityType, Relation, RelationType, Observation
from atlas_memory.tools.search import search_entities
from atlas_memory.tools.relations import get_relations
from atlas_memory.tools.observations import list_observations, add_observation


class TestSearchEntities:
    def test_search_by_name(self, db):
        db.upsert_entity(Entity(id="t1::login", type=EntityType.FUNCTION, name="login", path="auth.py"))
        db.upsert_entity(Entity(id="t1::logout", type=EntityType.FUNCTION, name="logout", path="auth.py"))
        db.upsert_entity(Entity(id="t1::render", type=EntityType.FUNCTION, name="render", path="ui.py"))

        result = json.loads(search_entities(db, "login"))
        assert len(result) == 1
        assert result[0]["name"] == "login"

    def test_search_by_type(self, db):
        db.upsert_entity(Entity(id="t2::App", type=EntityType.CLASS, name="App", path="app.py"))
        db.upsert_entity(Entity(id="t2::run", type=EntityType.FUNCTION, name="run", path="app.py"))

        result = json.loads(search_entities(db, "", entity_type="class"))
        assert len(result) == 1
        assert result[0]["type"] == "class"

    def test_search_empty(self, db):
        result = json.loads(search_entities(db, "nonexistent"))
        assert result == []

    def test_search_with_pagination(self, db):
        for i in range(5):
            db.upsert_entity(Entity(id=f"t3::f{i}", type=EntityType.FUNCTION, name=f"f{i}", path="t3.py"))

        page1 = json.loads(search_entities(db, "f", limit=3, offset=0))
        assert len(page1) == 3
        page2 = json.loads(search_entities(db, "f", limit=3, offset=3))
        assert len(page2) == 2


class TestGetRelations:
    def test_get_outgoing(self, db):
        db.upsert_entity(Entity(id="r1::a", type=EntityType.FUNCTION, name="a", path="r1.py"))
        db.upsert_entity(Entity(id="r1::b", type=EntityType.FUNCTION, name="b", path="r1.py"))
        db.add_relation(Relation(from_id="r1::a", to_id="r1::b", type=RelationType.CALLS))

        result = json.loads(get_relations(db, "r1::a", direction="out"))
        assert len(result) == 1
        assert result[0]["to_id"] == "r1::b"

    def test_get_empty(self, db):
        db.upsert_entity(Entity(id="r2::x", type=EntityType.FUNCTION, name="x", path="r2.py"))
        result = json.loads(get_relations(db, "r2::x"))
        assert result == []

    def test_filter_by_type(self, db):
        db.upsert_entity(Entity(id="r3::p", type=EntityType.CLASS, name="Parent", path="r3.py"))
        db.upsert_entity(Entity(id="r3::c", type=EntityType.CLASS, name="Child", path="r3.py"))
        db.add_relation(Relation(from_id="r3::c", to_id="r3::p", type=RelationType.EXTENDS))
        db.add_relation(Relation(from_id="r3::c", to_id="r3::p", type=RelationType.CALLS))

        result = json.loads(get_relations(db, "r3::c", direction="out", relation_type="extends"))
        assert len(result) == 1


class TestObservations:
    def test_add_and_list(self, db):
        db.upsert_entity(Entity(id="o1::f", type=EntityType.FUNCTION, name="f", path="o1.py"))

        add_result = json.loads(add_observation(db, "o1::f", "complex algorithm", "agent"))
        assert add_result["id"] is not None
        assert add_result["content"] == "complex algorithm"

        list_result = json.loads(list_observations(db, "o1::f"))
        assert len(list_result) == 1
        assert list_result[0]["entity_id"] == "o1::f"

    def test_list_pagination(self, db):
        db.upsert_entity(Entity(id="o2::f", type=EntityType.FUNCTION, name="f", path="o2.py"))
        for i in range(4):
            add_observation(db, "o2::f", f"note-{i}")

        page1 = json.loads(list_observations(db, "o2::f", limit=2, offset=0))
        assert len(page1) == 2
        page2 = json.loads(list_observations(db, "o2::f", limit=2, offset=2))
        assert len(page2) == 2

    def test_list_empty(self, db):
        db.upsert_entity(Entity(id="o3::f", type=EntityType.FUNCTION, name="f", path="o3.py"))
        result = json.loads(list_observations(db, "o3::f"))
        assert result == []

    def test_add_with_custom_source(self, db):
        db.upsert_entity(Entity(id="o4::f", type=EntityType.FUNCTION, name="f", path="o4.py"))
        result = json.loads(add_observation(db, "o4::f", "user note", "user"))
        assert result["source"] == "user"
