from __future__ import annotations

from atlas_memory.config import Config
from atlas_memory.server import create_server


class TestServer:
    def test_create_server(self, config: Config):
        server = create_server(config)
        assert server.name == "Atlas Memory MCP"

    def test_tools_registered(self, config: Config):
        server = create_server(config)
        tool_names = [t.name for t in server._tool_manager._tools.values()]
        assert "search_entities" in tool_names
        assert "get_relations" in tool_names
        assert "list_observations" in tool_names
        assert "add_observation" in tool_names
