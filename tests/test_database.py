from __future__ import annotations

import time

import pytest

from atlas_memory.models.entities import (
    Entity,
    EntityType,
    Relation,
    RelationType,
    Observation,
)
from atlas_memory.storage.database import Database


class TestEntityCRUD:
    def test_upsert_and_get(self, db: Database):
        e = Entity(
            id="test::main",
            type=EntityType.FUNCTION,
            name="main",
            path="test.py",
            signature="def main()",
            docstring="Entry point",
        )
        db.upsert_entity(e)

        got = db.get_entity("test::main")
        assert got is not None
        assert got.name == "main"
        assert got.type == EntityType.FUNCTION
        assert got.signature == "def main()"
        assert got.docstring == "Entry point"

    def test_get_nonexistent(self, db: Database):
        assert db.get_entity("nonexistent") is None

    def test_upsert_updates_existing(self, db: Database):
        e = Entity(id="a::f", type=EntityType.FUNCTION, name="f", path="a.py")
        db.upsert_entity(e)

        e2 = Entity(id="a::f", type=EntityType.FUNCTION, name="f_renamed", path="a.py")
        db.upsert_entity(e2)

        got = db.get_entity("a::f")
        assert got is not None
        assert got.name == "f_renamed"

    def test_delete(self, db: Database):
        e = Entity(id="del::me", type=EntityType.FILE, name="me", path="del.py")
        db.upsert_entity(e)
        assert db.delete_entity("del::me") is True
        assert db.get_entity("del::me") is None
        assert db.delete_entity("del::me") is False

    def test_query_by_keyword(self, db: Database):
        db.upsert_entity(Entity(id="a::login", type=EntityType.FUNCTION, name="login", path="auth.py"))
        db.upsert_entity(Entity(id="a::logout", type=EntityType.FUNCTION, name="logout", path="auth.py"))
        db.upsert_entity(Entity(id="b::render", type=EntityType.FUNCTION, name="render", path="ui.py"))

        results = db.query_entities(keyword="auth", limit=10)
        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"login", "logout"}

    def test_query_by_type(self, db: Database):
        db.upsert_entity(Entity(id="c::App", type=EntityType.CLASS, name="App", path="c.py"))
        db.upsert_entity(Entity(id="c::run", type=EntityType.FUNCTION, name="run", path="c.py"))

        funcs = db.query_entities(entity_type="function", limit=10)
        assert len(funcs) == 1
        assert funcs[0].name == "run"

    def test_query_by_path(self, db: Database):
        db.upsert_entity(Entity(id="d::x", type=EntityType.VARIABLE, name="x", path="src/d.py"))
        db.upsert_entity(Entity(id="e::y", type=EntityType.VARIABLE, name="y", path="lib/e.py"))

        results = db.query_entities(path="src", limit=10)
        assert len(results) == 1
        assert results[0].name == "x"

    def test_access_count_bumps_on_get(self, db: Database):
        e = Entity(id="ac::test", type=EntityType.FUNCTION, name="test", path="ac.py")
        db.upsert_entity(e)

        for _ in range(3):
            db.get_entity("ac::test")

        got = db.get_entity("ac::test")
        assert got is not None
        assert got.access_count >= 3


class TestRelationCRUD:
    def test_add_and_get_relations(self, db: Database):
        db.upsert_entity(Entity(id="a::f", type=EntityType.FUNCTION, name="f", path="a.py"))
        db.upsert_entity(Entity(id="b::g", type=EntityType.FUNCTION, name="g", path="b.py"))

        r = db.add_relation(Relation(from_id="a::f", to_id="b::g", type=RelationType.CALLS))
        assert r.id is not None

        relations = db.get_relations("a::f", direction="out")
        assert len(relations) == 1
        assert relations[0].to_id == "b::g"

    def test_get_relations_by_direction(self, db: Database):
        db.upsert_entity(Entity(id="x::a", type=EntityType.FUNCTION, name="a", path="x.py"))
        db.upsert_entity(Entity(id="x::b", type=EntityType.FUNCTION, name="b", path="x.py"))
        db.upsert_entity(Entity(id="x::c", type=EntityType.FUNCTION, name="c", path="x.py"))

        db.add_relation(Relation(from_id="x::a", to_id="x::b", type=RelationType.CALLS))
        db.add_relation(Relation(from_id="x::c", to_id="x::a", type=RelationType.CALLS))

        out = db.get_relations("x::a", direction="out")
        assert len(out) == 1

        in_ = db.get_relations("x::a", direction="in")
        assert len(in_) == 1

        both = db.get_relations("x::a", direction="both")
        assert len(both) == 2

    def test_get_relations_filter_by_type(self, db: Database):
        db.upsert_entity(Entity(id="t::a", type=EntityType.CLASS, name="A", path="t.py"))
        db.upsert_entity(Entity(id="t::b", type=EntityType.CLASS, name="B", path="t.py"))

        db.add_relation(Relation(from_id="t::a", to_id="t::b", type=RelationType.EXTENDS))
        db.add_relation(Relation(from_id="t::a", to_id="t::b", type=RelationType.CALLS))

        extends = db.get_relations("t::a", direction="out", relation_type="extends")
        assert len(extends) == 1
        assert extends[0].type == RelationType.EXTENDS


class TestObservationCRUD:
    def test_add_and_get(self, db: Database):
        db.upsert_entity(Entity(id="obs::f", type=EntityType.FUNCTION, name="f", path="obs.py"))

        o = db.add_observation(Observation(entity_id="obs::f", content="complex logic", source="agent"))
        assert o.id is not None

        obs_list = db.get_observations("obs::f")
        assert len(obs_list) == 1
        assert obs_list[0].content == "complex logic"

    def test_pagination(self, db: Database):
        db.upsert_entity(Entity(id="page::f", type=EntityType.FUNCTION, name="f", path="page.py"))

        for i in range(5):
            db.add_observation(Observation(entity_id="page::f", content=f"note {i}"))

        page1 = db.get_observations("page::f", limit=3, offset=0)
        assert len(page1) == 3

        page2 = db.get_observations("page::f", limit=3, offset=3)
        assert len(page2) == 2

    def test_empty_observations(self, db: Database):
        db.upsert_entity(Entity(id="empty::f", type=EntityType.FUNCTION, name="f", path="empty.py"))
        assert db.get_observations("empty::f") == []


class TestCascadeDelete:
    def test_delete_entity_removes_relations_and_observations(self, db: Database):
        db.upsert_entity(Entity(id="cd::a", type=EntityType.FUNCTION, name="a", path="cd.py"))
        db.upsert_entity(Entity(id="cd::b", type=EntityType.FUNCTION, name="b", path="cd.py"))
        db.add_relation(Relation(from_id="cd::a", to_id="cd::b", type=RelationType.CALLS))
        db.add_observation(Observation(entity_id="cd::a", content="note"))

        db.delete_entity("cd::a")

        assert db.get_entity("cd::a") is None
        rels = db.get_relations("cd::a")
        assert len(rels) == 0
        obs = db.get_observations("cd::a")
        assert len(obs) == 0


class TestCount:
    def test_count_entities(self, db: Database):
        assert db.count_entities() == 0
        db.upsert_entity(Entity(id="cnt::a", type=EntityType.FILE, name="a", path="cnt.py"))
        db.upsert_entity(Entity(id="cnt::b", type=EntityType.FILE, name="b", path="cnt.py"))
        assert db.count_entities() == 2
