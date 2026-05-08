from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    project_root: str = field(
        default_factory=lambda: os.getenv("PROJECT_ROOT", os.getcwd())
    )
    memory_db_path: str = field(
        default_factory=lambda: os.getenv("MEMORY_DB_PATH", "./data/memory.db")
    )
    chroma_path: str = field(
        default_factory=lambda: os.getenv("CHROMA_PATH", "./data/chroma")
    )
    auto_index: bool = field(
        default_factory=lambda: os.getenv("AUTO_INDEX", "true").lower() == "true"
    )
    max_index_file_size_kb: int = field(
        default_factory=lambda: int(os.getenv("MAX_INDEX_FILE_SIZE_KB", "200"))
    )
    server_port: int = field(
        default_factory=lambda: int(os.getenv("SERVER_PORT", "8742"))
    )
    forgetting_max_age_days: int = field(
        default_factory=lambda: int(os.getenv("FORGETTING_MAX_AGE_DAYS", "90"))
    )
    forgetting_max_inactive_days: int = field(
        default_factory=lambda: int(os.getenv("FORGETTING_MAX_INACTIVE_DAYS", "30"))
    )
    forgetting_budget_keep_top_n: int = field(
        default_factory=lambda: int(os.getenv("FORGETTING_BUDGET_KEEP_TOP_N", "10000"))
    )
    forgetting_every_minutes: int = field(
        default_factory=lambda: int(os.getenv("FORGETTING_EVERY_MINUTES", "60"))
    )

    def validate(self) -> list[str]:
        errors = []
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        return errors
