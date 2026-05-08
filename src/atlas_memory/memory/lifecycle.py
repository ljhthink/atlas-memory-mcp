from __future__ import annotations

import logging
import threading
import time

from atlas_memory.config import Config
from atlas_memory.storage.database import Database

logger = logging.getLogger(__name__)


class LifecycleManager:
    def __init__(self, config: Config, db: Database):
        self._config = config
        self._db = db
        self._timer: threading.Timer | None = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._schedule_next()

    def stop(self):
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self):
        if not self._running:
            return
        interval = self._config.forgetting_every_minutes * 60
        self._timer = threading.Timer(interval, self._on_tick)
        self._timer.daemon = True
        self._timer.start()

    def _on_tick(self):
        try:
            self._cleanup()
        except Exception:
            logger.exception("Cleanup failed")
        self._schedule_next()

    def _cleanup(self):
        now = int(time.time())
        max_age = self._config.forgetting_max_age_days * 86400
        inactive_threshold = self._config.forgetting_max_inactive_days * 86400

        deleted_obs = self._db.execute(
            "DELETE FROM observations WHERE created_at < ?", (now - max_age,)
        ).rowcount

        self._db.execute(
            "UPDATE entities SET access_count = MAX(access_count / 2, 0) WHERE updated_at < ?",
            (now - inactive_threshold,),
        )

        count = self._db.count_entities()
        budget = self._config.forgetting_budget_keep_top_n
        excess = 0
        if count > budget:
            excess = count - budget
            self._db.execute(
                "DELETE FROM entities WHERE id IN ("
                "SELECT id FROM entities ORDER BY access_count ASC LIMIT ?"
                ")",
                (excess,),
            )
            self._db.commit()

        if deleted_obs or count > budget:
            logger.info(
                "Cleanup: removed %d old observations, trimmed %d entities",
                deleted_obs,
                max(0, excess),
            )
