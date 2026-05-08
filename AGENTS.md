# Atlas Memory MCP Server

## 项目概述
高 Token 优化的记忆增强 MCP Server，为 OpenCode / Cline / Claude Code
提供代码知识图谱、会话持久记忆、语义搜索能力。

- 语言: Python 3.9+ (+ Node.js >= 18 用于 exec_code 沙箱)
- 框架: FastMCP + SQLite + ChromaDB
- 对外工具: 混合模式 (4 直接 + 1 exec_code)

---

## 总体进度

| 阶段 | 内容 | 状态 | 开始 | 完成 |
|------|------|------|------|------|
| 一 | 核心骨架 (MCP Server + SQLite + 4 直接工具) | [x] 已完成 | 2026-05-08 | 2026-05-08 |
| 二 | 代码解析 + 知识图谱 (tree-sitter + ChromaDB) | [x] 已完成 | 2026-05-08 | 2026-05-08 |
| 三 | exec_code 沙箱 + 生命周期管理 | [x] 已完成 | 2026-05-08 | 2026-05-08 |
| 四 | 测试完善 + 跨客户端验证 + 发布 | [ ] 未开始 | - | - |

进度: 3 / 4 阶段 (阶段一 100%, 阶段二 100%, 阶段三 100%)

---

## 模块状态一览

| 模块 | 路径 | 状态 | 功能完成度 |
|------|------|------|-----------|
| 配置管理 | src/atlas_memory/config.py | [x] 已完成 | 100% |
| 数据模型 | src/atlas_memory/models/ | [x] 已完成 | 100% |
| 存储层 | src/atlas_memory/storage/ | [x] 已完成 | 100% |
| 工具层 | src/atlas_memory/tools/ | [x] 已完成 | 100% |
| 代码解析 | src/atlas_memory/parser/ | [x] 已完成 | 100% |
| 记忆引擎 | src/atlas_memory/memory/ | [x] 已完成 | 100% |
| JS 沙箱 | src/atlas_memory/sandbox/ | [x] 已完成 | 100% |
| MCP 入口 | src/atlas_memory/server.py | [x] 已完成 | 100% |
| 测试 | tests/ | [~] 进行中 | 60% |

---

## 修改记录

| 日期 | 变更 | 影响范围 | 状态 |
|------|------|----------|------|
| 2026-05-08 | 阶段三完成：exec_code 沙箱 + 生命周期 + 58 测试全过 (82% 覆盖) | 根 | ✅ |
| 2026-05-08 | 阶段二完成：代码解析 + 知识图谱 + 向量搜索 + 46 测试全过 (83% 覆盖) | 根 | ✅ |
| 2026-05-08 | 阶段一完成：4 直接工具 + FastMCP Server + 集成测试 (29 测试全过, 91% 覆盖) | 根 | ✅ |
| 2026-05-08 | 阶段一启动：项目初始化、数据模型、存储层完成 (16 测试全过, 93% 覆盖) | 根 | ✅ |

---

## 开发约定

### 代码修改流程
每次修改代码后，必须同步更新对应层级的 AGENTS.md：

1. **修改文件** -> 找到最近的 AGENTS.md (同目录或父目录)
2. **更新时间线** -> 在 "修改时间线" 顶部追加条目, 格式:
   ```
   ### YYYY-MM-DD HH:MM
   - **[added/fixed/changed/removed]** 描述 (原因)
     - 文件: path/to/file.py
   ```
3. **更新功能状态** -> 如果功能完成/变更，修改功能清单中的状态
4. **更新根进度** -> 如果影响阶段进度，同步更新根 AGENTS.md 的阶段表格

### 状态标记
- [ ] 未开始
- [~] 进行中
- [x] 已完成
- [-] 已废弃

### 子目录 AGENTS.md
每个子目录必须包含 AGENTS.md，记录:
- 模块职责和对外接口
- 功能清单 (含完成状态)
- 依赖关系
- 修改时间线

---

## 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| OPENAI_API_KEY | 是 | - | OpenAI API 密钥 |
| PROJECT_ROOT | 否 | ./ | 要索引的项目根目录 |
| MEMORY_DB_PATH | 否 | ./data/memory.db | SQLite 路径 |
| CHROMA_PATH | 否 | ./data/chroma | ChromaDB 持久化目录 |
| AUTO_INDEX | 否 | true | 启动时自动索引 |
| MAX_INDEX_FILE_SIZE_KB | 否 | 200 | 跳过大文件阈值 |
| SERVER_PORT | 否 | 8742 | MCP Server 端口 |
| FORGETTING_MAX_AGE_DAYS | 否 | 90 | 观察记录最大保留天数 |
| FORGETTING_MAX_INACTIVE_DAYS | 否 | 30 | 实体不活跃阈值 |
| FORGETTING_BUDGET_KEEP_TOP_N | 否 | 10000 | 实体总数上限 |
| FORGETTING_EVERY_MINUTES | 否 | 60 | 清理间隔 |

---

## 当前阻塞项
无

## 下一步计划
阶段四：测试完善 + 跨客户端验证 (OpenCode/Cline) + 发布
