# models - 数据模型层

## 职责
定义项目中使用的所有数据类和枚举，零外部依赖。

## 对外接口
| 接口 | 说明 |
|------|------|
| Entity | 代码实体数据类 |
| Relation | 关系数据类 |
| Observation | 观察记录数据类 |
| EntityType | 实体类型枚举 (function/class/file/module/variable) |
| RelationType | 关系类型枚举 (calls/imports/extends/implements/depends_on) |

### Entity 字段
| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 唯一标识 (建议格式: path::name) |
| type | EntityType | 实体类型 |
| name | str | 名称 |
| path | str | 文件路径 |
| line_start | int \| None | 起始行 |
| line_end | int \| None | 结束行 |
| signature | str \| None | 函数/类签名 |
| docstring | str \| None | 文档注释 |
| embedding | list[float] \| None | 向量嵌入 (ChromaDB 管理) |
| created_at | int | 创建时间戳 |
| updated_at | int | 更新时间戳 |
| access_count | int | 访问计数 |

### Relation 字段
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int \| None | 自增 ID (插入时可选) |
| from_id | str | 源实体 ID |
| to_id | str | 目标实体 ID |
| type | RelationType | 关系类型 |

### Observation 字段
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int \| None | 自增 ID |
| entity_id | str | 关联实体 ID |
| content | str | 观察内容 |
| source | str | user/agent/analysis |
| created_at | int | 创建时间戳 |
| access_count | int | 访问计数 |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | Entity | 代码实体数据类 | [x] |
| 2 | Relation | 关系数据类 | [x] |
| 3 | Observation | 观察记录数据类 | [x] |
| 4 | EntityType | 实体类型枚举 | [x] |
| 5 | RelationType | 关系类型枚举 | [x] |
| 6 | 序列化工具 | to_dict / from_dict | [x] |

## 依赖
无外部依赖 (仅使用 Python 标准库 dataclasses + enum)

## 修改时间线
### 2026-05-08 22:30
- **[added]** 实现 Entity/Relation/Observation 数据类 + EntityType/RelationType 枚举 + to_dict/from_dict 序列化
  - 文件: src/atlas_memory/models/entities.py
  - 测试: 16 测试全部通过 (test_database.py 间接覆盖)

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义 3 个数据类和 2 个枚举
  - 文件: src/atlas_memory/models/AGENTS.md
