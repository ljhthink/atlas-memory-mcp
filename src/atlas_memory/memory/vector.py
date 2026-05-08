from __future__ import annotations

import logging

from atlas_memory.config import Config
from atlas_memory.models.entities import Entity

logger = logging.getLogger(__name__)


class VectorSearch:
    def __init__(self, config: Config):
        self._config = config
        self._client = None
        self._collection = None
        self._openai = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if not self._config.openai_api_key:
            self._client = False  # sentinel, but don't import chromadb
            return
        import chromadb
        from openai import OpenAI

        self._client = chromadb.PersistentClient(path=self._config.chroma_path)
        self._collection = self._client.get_or_create_collection(
            name="entities",
            metadata={"hnsw:space": "cosine"},
        )
        self._openai = OpenAI(api_key=self._config.openai_api_key)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_client()
        if self._openai is None:
            return []
        resp = self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in resp.data]

    def index_entity(self, entity: Entity):
        self._ensure_client()
        if self._collection is None:
            return
        text = f"[{entity.type.value}] {entity.name}"
        if entity.signature:
            text += f": {entity.signature}"
        if entity.docstring:
            text += f". {entity.docstring}"

        embedding = self._embed([text])
        if not embedding:
            return

        self._collection.upsert(
            ids=[entity.id],
            embeddings=[embedding[0]],
            metadatas=[{
                "name": entity.name,
                "path": entity.path,
                "type": entity.type.value,
            }],
        )

    def semantic_search(self, query: str, top_k: int = 10) -> list[str]:
        self._ensure_client()
        embeddings = self._embed([query])
        if not embeddings:
            return []
        try:
            results = self._collection.query(
                query_embeddings=[embeddings[0]],
                n_results=top_k,
            )
            ids = results.get("ids", [[]])[0]
            return list(ids)
        except Exception:
            logger.warning("Semantic search failed, returning empty")
            return []

    def remove_entity(self, entity_id: str):
        self._ensure_client()
        if self._collection is None:
            return
        try:
            self._collection.delete(ids=[entity_id])
        except Exception:
            pass
