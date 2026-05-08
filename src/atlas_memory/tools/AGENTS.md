# tools - MCP 工具层

## 职责
定义并注册暴露给 LLM 的 MCP 工具 (混合模式: 4 直接 + 1 exec_code)。

## 对外接口
| 工具 | Schema 预估 Token | 说明 |
|------|-------------------|------|
| search_entities | ~90 | 搜索代码实体 (关键词/语义混合) |
| get_relations | ~85 | 查询实体间的关系 (调用/导入/继承) |
| list_observations | ~80 | 分页获取实体的观察记录 |
| add_observation | ~80 | 为实体追加观察记录 |
| exec_code | ~60 | Code Mode 入口 (JS 沙箱执行) |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | search_entities | 关键词 + 语义混合搜索 | [x] |
| 2 | get_relations | 调用/导入/继承关系查询 | [x] |
| 3 | list_observations | 分页获取实体观察记录 | [x] |
| 4 | add_observation | 为实体追加观察 | [x] |
| 5 | exec_code | JS 代码执行入口 | [ ] |

## 依赖
- storage/database.py - 数据库查询
- memory/graph.py - 图谱查询
- memory/vector.py - 语义搜索
- sandbox/executor.py - exec_code 执行

## 修改时间线
### 2026-05-08 23:00
- **[added]** 实现 4 个直接 MCP 工具：search_entities, get_relations, list_observations, add_observation
  - 文件: tools/search.py, tools/relations.py, tools/observations.py
  - 测试: 13 个工具测试全部通过

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义 5 个 MCP 工具接口和功能清单
  - 文件: src/atlas_memory/tools/AGENTS.md
