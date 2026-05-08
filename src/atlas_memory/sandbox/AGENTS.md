# sandbox - JS 沙箱执行器

## 职责
在隔离的 Node.js 子进程中执行 LLM 生成的 JavaScript 代码，
通过 API 桥接与 Python 主进程通信，处理结果返回和错误。

## 对外接口
| 接口 | 说明 |
|------|------|
| SandboxExecutor(Config) | 沙箱执行器主类 |
| execute(code, api_context) -> dict | 执行 JS 代码，返回结果 JSON |

### execute 返回格式
```json
{
  "success": true,
  "result": <any>           // 用户代码返回值
}
// 或
{
  "success": false,
  "error": "错误描述",
  "hint": "修复建议"
}
```

## 安全边界
| 限制项 | 值 | 说明 |
|--------|-----|------|
| 执行超时 | 10s | 超时后 kill 子进程 |
| 输出上限 | 64KB | 防止大量数据回传 |
| 网络访问 | 禁止 | 子进程无网络权限 |
| 文件系统访问 | 禁止 | 仅通过 API 桥接间接操作 |
| 进程隔离 | subprocess | Python 主进程与 Node.js 子进程隔离 |

## API 桥接协议
JS 沙箱调用内部 API 时，通过 stdout 发送控制消息：
```
{"__api_call": "query", "args": {"keyword": "auth", "limit": 5}}
```
Python 侧拦截后执行真正的数据库操作，结果通过 stdin 回传。

### 暴露给沙箱的内部 API
| 方法 | 对应 Python 接口 |
|------|-----------------|
| mem.query(keyword, opts) | graph.query_entities |
| mem.get(entity_id) | database.get_entity |
| mem.semantic(query, top_k) | vector.semantic_search |
| mem.relations(entity_id, direction) | database.get_relations |
| mem.observations(entity_id, limit, offset) | database.get_observations |
| mem.observe(entity_id, content) | database.add_observation |

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | 子进程启动 | node -e 执行拼接脚本 | [ ] |
| 2 | API 桥接 | stdout/stdin IPC 通信管道 | [ ] |
| 3 | 超时控制 | asyncio.wait_for + kill | [ ] |
| 4 | 错误格式化 | JS 语法/运行时错误友好提示 | [ ] |
| 5 | Node.js 检测 | 启动时验证 Node 版本 >= 18 | [ ] |
| 6 | api_bridge.js | JS 侧桥接模板 | [ ] |

## 依赖
- Node.js >= 18
- asyncio (Python 标准库)
- src/sandbox/api_bridge.js (注入到子进程的 JS 模板)

## 修改时间线
### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义 SandboxExecutor 接口和安全策略
  - 文件: src/atlas_memory/sandbox/AGENTS.md
