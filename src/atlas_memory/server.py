from __future__ import annotations

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from atlas_memory.config import Config
from atlas_memory.storage.database import Database
from atlas_memory.tools.search import search_entities as _search
from atlas_memory.tools.relations import get_relations as _get_relations
from atlas_memory.tools.observations import list_observations as _list_obs
from atlas_memory.tools.observations import add_observation as _add_obs

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

    @server.tool(
        name="search_entities",
        description="搜索代码实体。按名称/路径/类型模糊匹配，返回匹配的实体列表。"
        "参数: query(搜索关键词), entity_type(function/class/file/module/variable), limit(默认10), offset(默认0)",
    )
    async def search_entities(
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> str:
        return _search(db, query, entity_type, limit, offset)

    @server.tool(
        name="get_relations",
        description="查询实体之间的调用/导入/继承关系。"
        "参数: entity_id(实体ID), direction(out/in/both), relation_type(calls/imports/extends/implements), limit(默认20)",
    )
    async def get_relations(
        entity_id: str,
        direction: str = "both",
        relation_type: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        return _get_relations(db, entity_id, direction, relation_type, limit)

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
        return _list_obs(db, entity_id, limit, offset)

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
        return _add_obs(db, entity_id, content, source)

    return server


def main():
    config = Config()
    errors = config.validate()
    if errors:
        for e in errors:
            logger.warning(e)
        if "OPENAI_API_KEY" in str(errors):
            logger.warning("OPENAI_API_KEY not set — 语义搜索功能需要 API Key")

    server = create_server(config)
    logger.info(f"Atlas Memory MCP Server starting on port {config.server_port}")
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
