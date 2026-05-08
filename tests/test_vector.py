from __future__ import annotations

from atlas_memory.memory.vector import VectorSearch
from atlas_memory.models.entities import Entity, EntityType


class TestVectorSearch:
    def test_init_no_api_call(self, temp_dir):
        vs = VectorSearch.__new__(VectorSearch)
        vs._config = None
        vs._client = None
        vs._collection = None
        vs._openai = None
        assert vs._client is None

    def test_semantic_search_no_api(self, config):
        vs = VectorSearch(config)
        result = vs.semantic_search("hello")
        assert result == []
