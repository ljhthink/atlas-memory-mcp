from __future__ import annotations

import json
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from atlas_memory.config import Config
from atlas_memory.storage.database import Database
from atlas_memory.memory.graph import GraphEngine
from atlas_memory.memory.vector import VectorSearch
from atlas_memory.models.entities import Observation

logger = logging.getLogger(__name__)


def create_server(config: Config) -> FastMCP:
    server = FastMCP(
        "Atlas Memory MCP",
        instructions="Atlas Memory MCP Server — 记忆增强知识图谱",
        host="127.0.0.1",
        port=config.server_port,
        log_level="WARNING",
    )
    db = Database(config)
    graph = GraphEngine(config, db)
    vector = VectorSearch(config)

    @server.tool(
        name="search_entities",
        description="搜索代码实体。支持关键词匹配和语义搜索。"
        "参数: query(搜索关键词), entity_type(function/class/file/module/variable), "
        "mode(keyword/semantic/hybrid, 默认keyword), limit(默认10), offset(默认0)",
    )
    async def search_entities(
        query: str,
        entity_type: Optional[str] = None,
        mode: str = "keyword",
        limit: int = 10,
        offset: int = 0,
    ) -> str:
        if mode in ("semantic", "hybrid"):
            sem_ids = vector.semantic_search(query, top_k=limit)
            if mode == "semantic" and sem_ids:
                results = []
                for eid in sem_ids:
                    e = db.get_entity(eid)
                    if e:
                        results.append(e)
                return json.dumps([e.to_dict() for e in results], ensure_ascii=False)
            elif mode == "hybrid" and sem_ids:
                k = max(limit // 2, 1)
                kw_results = db.query_entities(
                    keyword=query, entity_type=entity_type, limit=k, offset=offset
                )
                sem_results = []
                for eid in sem_ids[:k]:
                    e = db.get_entity(eid)
                    if e:
                        sem_results.append(e)
                merged = {e.id: e for e in kw_results}
                for e in sem_results:
                    if e.id not in merged:
                        merged[e.id] = e
                results = list(merged.values())[:limit]
                return json.dumps([e.to_dict() for e in results], ensure_ascii=False)

        keyword_results = db.query_entities(
            keyword=query,
            entity_type=entity_type,
            limit=limit,
            offset=offset,
        )
        return json.dumps([e.to_dict() for e in keyword_results], ensure_ascii=False)

    @server.tool(
        name="get_relations",
        description="查询实体之间的关系。"
        "参数: entity_id(实体ID), direction(out/in/both), "
        "relation_type(calls/imports/extends/implements/depends_on), limit(默认20)",
    )
    async def get_relations(
        entity_id: str,
        direction: str = "both",
        relation_type: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        results = db.get_relations(
            entity_id=entity_id,
            direction=direction,
            relation_type=relation_type,
            limit=limit,
        )
        return json.dumps([r.to_dict() for r in results], ensure_ascii=False)

    @server.tool(
        name="list_observations",
        description="获取实体的观察记录（用户或Agent之前添加的笔记），支持分页。"
        "参数: entity_id(实体ID), limit(默认10), offset(默认0)",
    )
    async def list_observations(
        entity_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> str:
        results = db.get_observations(
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
        return json.dumps([o.to_dict() for o in results], ensure_ascii=False)

    @server.tool(
        name="add_observation",
        description="为实体添加一条观察记录（笔记/发现/建议）。"
        "参数: entity_id(实体ID), content(观察内容), source(user/agent/analysis, 默认agent)",
    )
    async def add_observation(
        entity_id: str,
        content: str,
        source: str = "agent",
    ) -> str:
        obs = Observation(
            entity_id=entity_id,
            content=content,
            source=source,
        )
        result = db.add_observation(obs)
        return json.dumps(result.to_dict(), ensure_ascii=False)

    if config.auto_index:
        try:
            count = graph.index_project()
            logger.info(f"Auto-indexed {count} files")
        except Exception as e:
            logger.warning(f"Auto-index skipped: {e}")

    return server


def main():
    config = Config()
    errors = config.validate()
    if errors:
        for e in errors:
            logger.warning(e)

    server = create_server(config)
    logger.info(f"Atlas Memory MCP Server starting on port {config.server_port}")
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
