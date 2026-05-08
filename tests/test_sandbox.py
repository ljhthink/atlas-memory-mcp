from __future__ import annotations

import json

import pytest

from atlas_memory.models.entities import Entity, EntityType, Relation, RelationType, Observation
from atlas_memory.sandbox.executor import SandboxExecutor


class TestSandboxExecutor:
    @pytest.mark.asyncio
    async def test_execute_query(self, db):
        db.upsert_entity(Entity(id="sb::login", type=EntityType.FUNCTION, name="login", path="auth.py"))
        db.upsert_entity(Entity(id="sb::logout", type=EntityType.FUNCTION, name="logout", path="auth.py"))

        executor = SandboxExecutor(db)
        code = """
const results = mem.query('login');
return results.map(r => r.name);
"""
        result = await executor.execute(code)
        assert result["success"] is True
        assert "login" in result["result"]

    @pytest.mark.asyncio
    async def test_execute_get(self, db):
        db.upsert_entity(Entity(id="sb::get_test", type=EntityType.FUNCTION, name="get_test", path="gt.py"))
        executor = SandboxExecutor(db)
        code = """
const e = mem.get('sb::get_test');
return e ? e.name : null;
"""
        result = await executor.execute(code)
        assert result["success"] is True
        assert result["result"] == "get_test"

    @pytest.mark.asyncio
    async def test_execute_relations(self, db):
        db.upsert_entity(Entity(id="sb::caller", type=EntityType.FUNCTION, name="caller", path="sb.py"))
        db.upsert_entity(Entity(id="sb::callee", type=EntityType.FUNCTION, name="callee", path="sb.py"))
        db.add_relation(Relation(from_id="sb::caller", to_id="sb::callee", type=RelationType.CALLS))

        executor = SandboxExecutor(db)
        code = """
const rels = mem.relations('sb::caller', 'out');
return rels.map(r => r.to_name);
"""
        result = await executor.execute(code)
        assert result["success"] is True
        assert "callee" in result["result"]

    @pytest.mark.asyncio
    async def test_execute_observations(self, db):
        db.upsert_entity(Entity(id="sb::obs_test", type=EntityType.FUNCTION, name="obs_test", path="sb.py"))
        db.add_observation(Observation(entity_id="sb::obs_test", content="important function"))

        executor = SandboxExecutor(db)
        code = """
const obs = mem.observations('sb::obs_test');
return obs.map(o => o.content);
"""
        result = await executor.execute(code)
        assert result["success"] is True
        assert "important function" in result["result"]

    @pytest.mark.asyncio
    async def test_execute_observe_pending(self, db):
        db.upsert_entity(Entity(id="sb::pend", type=EntityType.FUNCTION, name="pend", path="sb.py"))
        executor = SandboxExecutor(db)
        code = """
const r = mem.observe('sb::pend', 'needs review');
return r;
"""
        result = await executor.execute(code)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_syntax_error(self, db):
        executor = SandboxExecutor(db)
        code = "return 1 +"  # invalid syntax
        result = await executor.execute(code)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_with_filter_and_type(self, db):
        db.upsert_entity(Entity(id="sb::f1", type=EntityType.FUNCTION, name="helper_a", path="utils.py"))
        db.upsert_entity(Entity(id="sb::f2", type=EntityType.CLASS, name="helper_b", path="utils.py"))

        executor = SandboxExecutor(db)
        code = """
const results = mem.query('helper', {type: 'function'});
return results.map(r => r.type);
"""
        result = await executor.execute(code)
        assert result["success"] is True
        assert all(t == "function" for t in result["result"])
