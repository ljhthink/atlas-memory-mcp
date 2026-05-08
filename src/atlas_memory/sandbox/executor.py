from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path

from atlas_memory.storage.database import Database
from atlas_memory.memory.vector import VectorSearch

logger = logging.getLogger(__name__)

_bridge_template = None


def _get_bridge_template() -> str:
    global _bridge_template
    if _bridge_template is None:
        _bridge_template = (Path(__file__).parent / "api_bridge.js").read_text()
    return _bridge_template


class SandboxExecutor:
    TIMEOUT_SEC = 10
    MAX_OUTPUT_BYTES = 64 * 1024

    def __init__(self, db: Database, vector: VectorSearch | None = None):
        self._db = db
        self._vector = vector
        self._node_path = shutil.which("node")

    def _build_context(self) -> dict:
        entities = self._db.query_entities(limit=500)
        relations = []
        for e in entities[:100]:
            rels = self._db.get_relations(e.id, direction="both", limit=100)
            relations.extend(rels)
        observations = []
        for e in entities[:50]:
            obs = self._db.get_observations(e.id, limit=20)
            observations.extend(obs)

        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations],
            "observations": [o.to_dict() for o in observations],
        }

    def _build_script(self, code: str, context: dict) -> str:
        template = _get_bridge_template()
        marker = "// __USER_CODE__"
        idx = template.find(marker)
        if idx == -1:
            raise RuntimeError("Invalid bridge template")
        prefix = template[: idx + len(marker)]
        prefix = prefix.replace("__API_CONTEXT__", json.dumps(context))
        wrapped = (
            prefix
            + "\n(async () => {\n"
            + code
            + "\n})().then(r => console.log(JSON.stringify(r))).catch(e => { console.error(e.message); process.exit(1); });\n"
        )
        return wrapped

    async def execute(self, code: str) -> dict:
        if self._node_path is None:
            return {
                "success": False,
                "error": "Node.js not found. exec_code requires Node.js >= 18.",
                "hint": "Install Node.js from https://nodejs.org/",
            }

        context = self._build_context()
        script = self._build_script(code, context)

        try:
            proc = await asyncio.create_subprocess_exec(
                self._node_path,
                "-e",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.TIMEOUT_SEC
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.TIMEOUT_SEC}s",
                    "hint": "Simplify your code or split into multiple exec_code calls",
                }

            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", errors="replace")[:500]
                return {
                    "success": False,
                    "error": err_text or f"Exit code {proc.returncode}",
                    "hint": "Check JavaScript syntax",
                }

            output = stdout.decode("utf-8", errors="replace")
            if len(output) > self.MAX_OUTPUT_BYTES:
                output = output[: self.MAX_OUTPUT_BYTES] + "\n... [truncated]"

            try:
                result = json.loads(output)
            except json.JSONDecodeError:
                return {"success": True, "result": output}

            if isinstance(result, dict) and result.get("__op") == "observe":
                self._apply_pending(result)

            return {"success": True, "result": result}

        except FileNotFoundError:
            return {
                "success": False,
                "error": "Node.js not found",
                "hint": "Install Node.js >= 18",
            }
        except Exception as e:
            logger.exception("Sandbox execution failed")
            return {
                "success": False,
                "error": str(e),
                "hint": "Internal sandbox error",
            }

    def _apply_pending(self, pending: dict):
        if not isinstance(pending, dict):
            return
        eid = pending.get("entity_id")
        content = pending.get("content")
        if eid and content:
            from atlas_memory.models.entities import Observation

            obs = Observation(
                entity_id=eid,
                content=content,
                source="agent",
            )
            self._db.add_observation(obs)
