from __future__ import annotations

import pytest

from atlas_memory.models.entities import Entity, EntityType, Observation
from atlas_memory.memory.lifecycle import LifecycleManager


class TestLifecycleManager:
    def test_init(self, config, db):
        lm = LifecycleManager(config, db)
        assert lm._timer is None

    @pytest.mark.asyncio
    async def test_start_stop(self, config, db):
        lm = LifecycleManager(config, db)
        lm.start()
        assert lm._running is True
        lm.stop()
        assert lm._running is False

    @pytest.mark.asyncio
    async def test_cleanup_old_observations(self, config, db):
        config.forgetting_max_age_days = 0
        db.upsert_entity(Entity(id="lc::f", type=EntityType.FUNCTION, name="f", path="lc.py"))
        obs = Observation(entity_id="lc::f", content="old", source="agent")
        obs.created_at = 1
        db.add_observation(obs)

        lm = LifecycleManager(config, db)
        lm._cleanup()

        remaining = db.get_observations("lc::f")
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_budget_enforcement(self, config, db):
        config.forgetting_budget_keep_top_n = 2
        for i in range(5):
            db.upsert_entity(Entity(id=f"b::e{i}", type=EntityType.FUNCTION, name=f"e{i}", path="b.py"))
            db.get_entity(f"b::e{i}")  # bump access count

        assert db.count_entities() == 5

        lm = LifecycleManager(config, db)
        lm._cleanup()

        assert db.count_entities() <= 2

    @pytest.mark.asyncio
    async def test_no_op_under_budget(self, config, db):
        config.forgetting_budget_keep_top_n = 1000
        for i in range(3):
            db.upsert_entity(Entity(id=f"nb::e{i}", type=EntityType.FUNCTION, name=f"e{i}", path="nb.py"))

        lm = LifecycleManager(config, db)
        lm._cleanup()

        assert db.count_entities() == 3
