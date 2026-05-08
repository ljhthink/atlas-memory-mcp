# storage - 存储层

## 职责
SQLite 数据库的建表、迁移、CRUD 操作封装。

## 对外接口
| 接口 | 说明 |
|------|------|
| Database(Config) | 连接管理 + 建表 |
| upsert_entity(e) | 插入或更新实体 |
| get_entity(id) | 按 ID 查询 |
| query_entities(filters) | 多条件查询 (名称/路径/类型) |
| delete_entity(id) | 删除实体 |
| add_relation(r) | 添加关系 |
| get_relations(id, direction) | 按方向查关系 (out/in/both) |
| add_observation(o) | 添加观察 |
| get_observations(id, limit, offset) | 分页取观察 |
| execute(sql, params) | 原始 SQL 执行 |

## 表结构

### entities
| 列 | 类型 | 说明 |
|----|------|------|
| id | TEXT PK | 唯一标识 |
| type | TEXT | function/class/file/module/variable |
| name | TEXT | 名称 |
| path | TEXT | 文件路径 |
| line_start | INTEGER | 起始行 |
| line_end | INTEGER | 结束行 |
| signature | TEXT | 函数/类签名 |
| docstring | TEXT | 文档注释 |
| embedding | BLOB | 序列化向量 (早期用 ChromaDB 替代) |
| created_at | INTEGER | 创建时间戳 |
| updated_at | INTEGER | 更新时间戳 |
| access_count | INTEGER | 访问次数 |

### relations
| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增 ID |
| from_id | TEXT FK | 源实体 |
| to_id | TEXT FK | 目标实体 |
| type | TEXT | calls/imports/extends/implements/depends_on |

### observations
| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增 ID |
| entity_id | TEXT FK | 关联实体 |
| content | TEXT | 观察内容 |
| source | TEXT | user/agent/analysis |
| created_at | INTEGER | 创建时间戳 |
| access_count | INTEGER | 访问次数 |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | 数据库连接 | 创建/打开 SQLite 文件 (WAL + FK) | [x] |
| 2 | 建表 + 索引 | 初始化 entities/relations/observations 表 + 6 个索引 | [x] |
| 3 | 实体 CRUD | upsert/get/query/delete | [x] |
| 4 | 关系 CRUD | add + 双向查询 + 类型过滤 | [x] |
| 5 | 观察 CRUD | add + 分页查询 | [x] |
| 6 | 查询构建器 | 动态 WHERE + LIMIT/OFFSET | [x] |

## 依赖
- models/entities.py - 数据类定义 (Entity/Relation/Observation)

## 修改时间线
### 2026-05-08 22:30
- **[added]** 实现 Database 类: 连接管理 + 建表 + 实体 CRUD + 关系 CRUD + 观察 CRUD + 级联删除 + access_count 自动递增
  - 文件: src/atlas_memory/storage/database.py
  - 测试: 16 测试全部通过, 98% 行覆盖

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义存储层接口、表结构和功能清单
  - 文件: src/atlas_memory/storage/AGENTS.md
