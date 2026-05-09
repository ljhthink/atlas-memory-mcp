# memory - 记忆引擎

## 职责
知识图谱查询、向量语义搜索、生命周期清理。

## 对外接口
| 接口 | 说明 |
|------|------|
| GraphEngine(Config) | 图谱：索引项目、查询实体、获取调用链 |
| VectorSearch(Config) | 向量：语义搜索、索引实体嵌入 (ChromaDB + OpenAI) |
| LifecycleManager(Config) | 生命周期：定时清理过期数据、权重衰减 |

### GraphEngine 方法
| 方法 | 说明 |
|------|------|
| index_project(root_path) | 递归索引项目目录 |
| index_file(filepath) | 解析并索引单个文件 |
| query(keyword, entity_type) | SQLite LIKE 搜索 |
| get_callers(entity_id) | 查找调用者 |
| get_dependencies(entity_id) | 查找依赖 |

### VectorSearch 方法
| 方法 | 说明 |
|------|------|
| embed(texts) | 调用 OpenAI text-embedding-3-small |
| index_entity(entity) | 为实体生成嵌入并存入 ChromaDB |
| semantic_search(query, top_k) | 返回最相关实体 ID 列表 |
| hybrid_search(query, entity_type) | 语义 + 结构化过滤 |

### LifecycleManager 方法
| 方法 | 说明 |
|------|------|
| start() | 启动异步清理循环 |
| cleanup() | 单次清理：删除过期 + 权重衰减 + 预算控制 |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | 项目索引 | 递归解析目录，提取实体+关系 | [x] |
| 2 | 调用链查询 | find_callers / find_dependencies | [x] |
| 3 | 向量嵌入 | 可配置嵌入模型 (默认 text-embedding-3-small, 支持 SiliconFlow 等兼容 API) | [x] |
| 4 | 语义搜索 | ChromaDB 查询 top-k 相似实体 | [x] |
| 5 | 混合搜索 | 语义 + 关键词合并去重 | [x] |
| 6 | 清理定时任务 | 按规则清理过期数据 | [x] |
| 7 | 权重衰减 | 不活跃实体权重降低 | [x] |

## 依赖
- storage/database.py - 持久化
- models/entities.py - 数据模型
- parser/code_parser.py - 代码解析 (GraphEngine)
- chromadb - 向量存储
- openai / 兼容 API - 嵌入生成

## 修改时间线
### 2026-05-09
- **[changed]** VectorSearch: 支持 OPENAI_BASE_URL 和 EMBEDDING_MODEL 环境变量 (SiliconFlow 兼容)
  - 文件: memory/vector.py, config.py

### 2026-05-09 00:00
- **[added]** 实现 LifecycleManager: 定时清理过期观察/衰减不活跃实体/预算控制
  - 文件: memory/lifecycle.py
  - 测试: 5 测试全过

### 2026-05-08 23:30
- **[added]** 实现 GraphEngine (索引/调用链) + VectorSearch (ChromaDB + OpenAI 嵌入, 无 API Key 优雅降级)
  - 文件: src/atlas_memory/memory/graph.py, src/atlas_memory/memory/vector.py
  - 测试: 7 测试全过, GraphEngine 94% 覆盖

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义 GraphEngine/VectorSearch/LifecycleManager 接口
  - 文件: src/atlas_memory/memory/AGENTS.md