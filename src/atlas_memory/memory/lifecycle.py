from __future__ import annotations

import asyncio
import logging
import time

from atlas_memory.config import Config
from atlas_memory.storage.database import Database

logger = logging.getLogger(__name__)


class LifecycleManager:
    def __init__(self, config: Config, db: Database):
        self._config = config
        self._db = db
        self._task: asyncio.Task | None = None

    def start(self):
        if self._task is not None:
            return
        try:
            ev_loop = asyncio.get_running_loop()
            self._task = ev_loop.create_task(self._cleanup_loop())
        except RuntimeError:
            pass  # no event loop (testing)

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _cleanup_loop(self):
        interval = self._config.forgetting_every_minutes * 60
        while True:
            try:
                await self._cleanup()
            except Exception:
                logger.exception("Cleanup failed")
            await asyncio.sleep(interval)

    async def _cleanup(self):
        now = int(time.time())
        max_age = self._config.forgetting_max_age_days * 86400
        inactive_threshold = self._config.forgetting_max_inactive_days * 86400

        deleted_obs = self._db._conn.execute(
            "DELETE FROM observations WHERE created_at < ?", (now - max_age,)
        ).rowcount

        self._db._conn.execute(
            "UPDATE entities SET access_count = MAX(access_count / 2, 0) WHERE updated_at < ?",
            (now - inactive_threshold,),
        )

        count = self._db._conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        budget = self._config.forgetting_budget_keep_top_n
        excess = 0
        if count > budget:
            excess = count - budget
            self._db._conn.execute(
                "DELETE FROM entities WHERE id IN ("
                "SELECT id FROM entities ORDER BY access_count ASC LIMIT ?"
                ")",
                (excess,),
            )

        self._db._conn.commit()

        if deleted_obs or count > budget:
            logger.info(f"Cleanup: removed {deleted_obs} old observations, trimmed {max(0, excess)} entities")
