# atlas_memory 主包

## 职责
MCP Server 入口、配置管理、子模块编排。

## 对外接口
| 接口 | 类型 | 说明 |
|------|------|------|
| main() | 函数 | fastmcp.run() 入口 |
| Config | 类 | 环境变量读取 + 默认值 |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | 配置管理 | 读取环境变量, 验证必需项 | [x] |
| 2 | Server 入口 | FastMCP 启动 + 工具注册 | [x] |
| 3 | 启动时自动索引 | auto_index 逻辑 | [ ] |

## 依赖
- tools/ - 注册 5 个 MCP 工具
- memory/ - 引擎初始化
- storage/ - 数据库连接

## 修改时间线
### 2026-05-08 23:00
- **[added]** 实现 FastMCP Server + 4 工具注册 (search_entities, get_relations, list_observations, add_observation)
  - 文件: src/atlas_memory/server.py

### 2026-05-08 22:30
- **[added]** 实现 Config 配置管理类 (11 个环境变量 + validate)
  - 文件: src/atlas_memory/config.py
- **[added]** 实现数据模型 + 存储层 (16 测试全过)

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义主包结构和功能清单
  - 文件: src/atlas_memory/AGENTS.md
