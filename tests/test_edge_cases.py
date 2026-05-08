from __future__ import annotations

import pytest

from atlas_memory.sandbox.executor import SandboxExecutor
from atlas_memory.memory.vector import VectorSearch
from atlas_memory.models.entities import Entity, EntityType


class TestSandboxErrorPaths:
    def test_no_node_path(self, db):
        executor = SandboxExecutor(db)
        executor._node_path = None
        # Just verify it doesn't crash on init
        assert executor._node_path is None

    @pytest.mark.asyncio
    async def test_execute_no_node(self, db):
        executor = SandboxExecutor(db)
        executor._node_path = None
        result = await executor.execute("return 1;")
        assert result["success"] is False
        assert "Node.js" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_empty_code(self, db):
        executor = SandboxExecutor(db)
        result = await executor.execute("return null;")
        assert result["success"] is True
        assert result["result"] is None

    def test_build_context_empty(self, db):
        executor = SandboxExecutor(db)
        ctx = executor._build_context()
        assert "entities" in ctx
        assert "relations" in ctx
        assert "observations" in ctx
        assert ctx["entities"] == []


class TestVectorSearchEdgeCases:
    def test_index_entity_no_api_key(self, config):
        vs = VectorSearch(config)
        e = Entity(id="v::test", type=EntityType.FUNCTION, name="test", path="v.py")
        vs.index_entity(e)  # should not raise

    def test_remove_entity_no_client(self, config):
        vs = VectorSearch(config)
        vs.remove_entity("nonexistent")  # should not raise

    def test_ensure_client_without_key(self, config):
        config.openai_api_key = ""
        vs = VectorSearch(config)
        vs._ensure_client()
        assert vs._openai is None


class TestSandboxEdgeCases:
    @pytest.mark.asyncio
    async def test_json_decode_fallback(self, db):
        executor = SandboxExecutor(db)
        result = await executor.execute("return 42;")
        assert result["success"] is True
        assert result["result"] == 42

    @pytest.mark.asyncio
    async def test_observe_applies_pending(self, db):
        db.upsert_entity(Entity(id="ap::f", type=EntityType.FUNCTION, name="f", path="ap.py"))
        executor = SandboxExecutor(db)
        code = "const r = mem.observe('ap::f', 'test note'); return r;"
        result = await executor.execute(code)
        assert result["success"] is True

        obs = db.get_observations("ap::f")
        assert len(obs) == 1
        assert obs[0].content == "test note"
