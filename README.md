# Atlas Memory MCP Server

高 Token 优化的记忆增强 MCP Server，为 AI 编程工具自动提供项目知识图谱、会话记忆和语义搜索能力。

<div align="center">

**支持 OpenCode | Cline | Claude Code**

[特性](#特性) · [安装](#安装) · [配置](#客户端配置) · [工具](#mcp-工具) · [故障排查](#故障排查)

</div>

---

## 特性

- **5 个 MCP 工具** — 4 个直接工具降低 token 消耗，1 个 `exec_code` 沙箱处理复杂查询
- **代码知识图谱** — tree-sitter 解析 Python AST，自动提取函数/类/调用/导入关系
- **语义搜索** — ChromaDB + OpenAI text-embedding-3-small，支持自然语言搜索代码
- **自动遗忘机制** — TTL 清理过期观察记录 + 实体权重衰减 + 预算控制
- **JS 沙箱** — `exec_code` 工具在隔离 Node.js 子进程中执行自定义 JavaScript 代码
- **零配置启动** — 启动时自动索引项目，开箱即用

---

## 系统要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | >= 3.10 | 主运行环境 |
| Node.js | >= 18 | 仅 `exec_code` 工具需要（可选） |
| pip | 任意 | 包管理 |
| Git | 任意 | 克隆项目用（可选） |

---

## 安装

### 方式一：Git 克隆安装（推荐）

```bash
# 克隆项目
git clone https://github.com/LJHTHINK/atlas-memory-mcp.git atlas-memory-mcp
cd atlas-memory-mcp

# 安装核心依赖
pip install -e .

# 安装全部依赖（含 AI 功能）
pip install -e ".[ai]"

# 安装开发依赖（含测试工具）
pip install -e ".[ai,dev]"
```

### 方式二：拷贝目录安装

从已配置好的电脑拷贝整个 `atlas-memory-mcp` 目录到目标电脑，然后：

```bash
cd atlas-memory-mcp
pip install -e ".[ai]"
```

### 验证安装

```bash
python -c "from atlas_memory.server import main; print('OK')"
```

---

## 获取 OpenAI API Key

语义搜索功能需要 OpenAI API Key。**没有 Key 也可以使用**，只是语义搜索返回空结果。

1. 访问 [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. 注册或登录 OpenAI 账号
3. 点击 **Create new secret key**
4. 复制密钥（**只显示一次，必须立即保存**）
5. 建议设置每月使用限额（Settings → Billing → Usage limits）

> **成本参考**：`text-embedding-3-small` 约 \$0.02/百万 token。索引 100 文件项目通常不到 \$0.01。

### 使用其他嵌入提供商

如果不方便注册 OpenAI，可以改为国内兼容接口：

**硅基流动（SiliconFlow）** — 支持 OpenAI 兼容接口，有免费额度：

修改 `src/atlas_memory/memory/vector.py` 第 32 行附近：

```python
# 原代码
self._openai = OpenAI(api_key=self._config.openai_api_key)

# 改为
self._openai = OpenAI(
    api_key="sk-your-siliconflow-key",
    base_url="https://api.siliconflow.cn/v1",
)
environment = "OPENAI_API_KEY=sk-your-siliconflow-key"
```

**阿里百炼** — 有免费额度，需安装 dashscope：

```python
# 替换 _embed 方法中的 OpenAI 调用
import dashscope
resp = dashscope.TextEmbedding.call(
    model=dashscope.TextEmbedding.Models.text_embedding_v2,
    input=texts,
)
```

---

## 客户端配置

### OpenCode

编辑项目根目录下的 `opencode.jsonc`（没有则新建）：

```jsonc
{
  "mcpServers": {
    "atlas-memory": {
      "command": "python",
      "args": ["-m", "atlas_memory.server"],
      "cwd": "/path/to/atlas-memory-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-xxxxxxxxxxxxxxxx",
        "PROJECT_ROOT": "${workspaceFolder}",
        "AUTO_INDEX": "true"
      }
    }
  }
}
```

> **`cwd`** 必须指向本项目所在的绝对路径。`${workspaceFolder}` 是 OpenCode 变量，指向当前打开的项目。

### Cline

编辑 VS Code 的 `mcp_settings.json`（路径：`~/.vscode/mcp_settings.json` 或通过 Cline 设置面板）：

```json
{
  "mcpServers": {
    "atlas-memory": {
      "command": "python",
      "args": ["-m", "atlas_memory.server"],
      "cwd": "/absolute/path/to/atlas-memory-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-xxxxxxxxxxxxxxxx",
        "PROJECT_ROOT": "/absolute/path/to/your/project",
        "AUTO_INDEX": "true"
      }
    }
  }
}
```

### Claude Code

编辑项目根目录下的 `.mcp.json`：

```json
{
  "mcpServers": {
    "atlas-memory": {
      "command": "python",
      "args": ["-m", "atlas_memory.server"],
      "cwd": "/absolute/path/to/atlas-memory-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-xxxxxxxxxxxxxxxx",
        "PROJECT_ROOT": "/absolute/path/to/your/project"
      }
    }
  }
}
```

### 使用虚拟环境（推荐生产环境）

```jsonc
{
  "mcpServers": {
    "atlas-memory": {
      // 使用 venv 中的 Python
      "command": "/path/to/venv/bin/python",      // Linux/macOS
      "command": "D:\\venv\\Scripts\\python.exe", // Windows
      "args": ["-m", "atlas_memory.server"],
      ...
    }
  }
}
```

---

## MCP 工具

### 1. search_entities

搜索代码实体，支持三种模式。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索关键词 |
| `entity_type` | string | `null` | 过滤类型：`function`/`class`/`file`/`module`/`variable` |
| `mode` | string | `keyword` | 搜索模式：`keyword`/`semantic`/`hybrid` |
| `limit` | int | `10` | 返回数量上限 |
| `offset` | int | `0` | 分页偏移 |

**使用示例：**

LLM 会这样调用（无需手动输入）：

```
# 关键词搜索（默认）
search_entities(query="authentication", entity_type="function", limit=5)

# 语义搜索（需要 OPENAI_API_KEY）
search_entities(query="how does login work", mode="semantic", limit=5)

# 混合搜索（关键词 + 语义，去重合并）
search_entities(query="token validation", mode="hybrid")
```

返回 JSON 数组，每个实体包含 `id`、`name`、`path`、`type`、`signature`、`docstring` 等字段。

### 2. get_relations

查询实体之间的调用、导入、继承关系。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `entity_id` | string | 必填 | 实体 ID |
| `direction` | string | `both` | 方向：`out`（我调用了谁）/ `in`（谁调用了我）/ `both` |
| `relation_type` | string | `null` | 过滤：`calls`/`imports`/`extends`/`implements`/`depends_on` |
| `limit` | int | `20` | 返回数量上限 |

**使用示例：**

```
# 查询 login 函数调用了哪些其他函数
get_relations(entity_id="abc123::login", direction="out", relation_type="calls")

# 查询谁调用了 login
get_relations(entity_id="abc123::login", direction="in", relation_type="calls")
```

### 3. list_observations

获取某个实体的观察记录（LLM 之前添加的笔记）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `entity_id` | string | 必填 | 实体 ID |
| `limit` | int | `10` | 返回数量上限 |
| `offset` | int | `0` | 分页偏移 |

### 4. add_observation

为实体添加一条观察记录（记忆）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `entity_id` | string | 必填 | 实体 ID |
| `content` | string | 必填 | 观察内容 |
| `source` | string | `agent` | 来源：`user`/`agent`/`analysis` |

### 5. exec_code

执行自定义 JavaScript 代码，访问预加载的实体、关系和观察记录。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code` | string | 必填 | JavaScript 代码 |

**可用的内置 API：**

```
mem.query(keyword, {type?, limit?, offset?})   → 关键词搜索实体
mem.get(entity_id)                              → 按 ID 取实体
mem.relations(entity_id, direction)             → 获取关系
mem.observations(entity_id, limit, offset)      → 获取观察记录
mem.observe(entity_id, content)                 → 添加观察记录
mem.semantic(query, top_k)                      → 语义搜索（无 OPENAI_KEY 时返回空）
```

**使用示例：**

```javascript
// 查找所有认证相关函数
const results = mem.query('auth', {type: 'function', limit: 10});
return results.map(r => ({
  name: r.name,
  file: r.path,
  signature: r.signature
}));

// 获取函数的调用关系链
const rels = mem.relations('abc123::login', 'out');
return rels.map(r => ({
  from: r.from_name,
  to: r.to_name,
  type: r.type
}));

// 组合查询：找所有被超过 2 个函数调用的函数
const allFuncs = mem.query('', {type: 'function', limit: 100});
return allFuncs.filter(f => {
  const callers = mem.relations(f.id, 'in').filter(r => r.type === 'calls');
  return callers.length > 2;
}).map(f => ({name: f.name, callers: callers.length}));
```

---

## 环境变量完整参考

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 否* | `""` | OpenAI API 密钥。\*不设置时语义搜索返回空，其他功能正常 |
| `PROJECT_ROOT` | 否 | `./` | 要索引的项目根目录的绝对路径 |
| `MEMORY_DB_PATH` | 否 | `./data/memory.db` | SQLite 数据库文件路径 |
| `CHROMA_PATH` | 否 | `./data/chroma` | ChromaDB 向量数据库持久化目录 |
| `AUTO_INDEX` | 否 | `true` | 启动时是否自动索引项目 |
| `MAX_INDEX_FILE_SIZE_KB` | 否 | `200` | 超过此大小（KB）的文件跳过索引 |
| `SERVER_PORT` | 否 | `8742` | MCP Server 端口（SSE/HTTP 模式） |
| `FORGETTING_MAX_AGE_DAYS` | 否 | `90` | 观察记录最大保留天数 |
| `FORGETTING_MAX_INACTIVE_DAYS` | 否 | `30` | 实体不活跃天数阈值（超过则权重减半） |
| `FORGETTING_BUDGET_KEEP_TOP_N` | 否 | `10000` | 实体总数上限（超过则删除低权重实体） |
| `FORGETTING_EVERY_MINUTES` | 否 | `60` | 自动清理间隔（分钟） |

---

## 使用流程

典型的首次使用流程：

```
1. 安装依赖: pip install -e ".[ai]"
2. 配置 AI 客户端（opencode.jsonc / mcp_settings.json / .mcp.json）
3. 打开 AI 编程工具，确认 Atlas Memory MCP 已连接
4. 启动时自动索引项目（AUTO_INDEX=true，默认行为）
5. 开始使用 —— LLM 会自动调用工具来搜索和理解你的代码
```

### 正常使用时的交互模式

```
你: "解释一下这个项目的认证逻辑"

LLM 内部会:
  1. search_entities("auth", mode="keyword")      → 找到 auth.py 和 login/logout 函数
  2. get_relations("xxx::login", direction="out")  → 查看 login 调用了哪些函数
  3. list_observations("xxx::login")               → 查看之前的笔记
  → 返回: "认证逻辑在 auth.py 中，login 函数调用 verify_credentials..."
```

---

## 数据存储

所有数据保存在 `data/` 目录下（由 `.gitignore` 忽略）：

```
data/
├── memory.db       # SQLite 数据库：实体、关系、观察记录
└── chroma/         # ChromaDB：向量嵌入持久化
```

- **SQLite**：本地文件数据库，结构化查询快速，无需额外服务
- **ChromaDB**：本地持久化向量数据库，存储代码实体的嵌入向量

如果多人协作需要共享记忆，可以将 `data/` 目录放到共享目录，通过 `MEMORY_DB_PATH` 和 `CHROMA_PATH` 配置指向。

---

## 故障排查

### MCP Server 未在客户端显示

1. 确认 Python >= 3.10：`python --version`
2. 确认安装成功：`python -c "from atlas_memory.server import main"`
3. 确认客户端配置中 `cwd` 路径正确（推荐用绝对路径）
4. 查看客户端日志，搜索 "atlas-memory" 相关错误

### Node.js 未安装（exec_code 不可用）

- 下载安装：https://nodejs.org/（版本 >= 18）
- 安装后重启 AI 客户端
- 没有 Node.js 不影响其他 4 个工具

### 语义搜索不工作

- 确认 `OPENAI_API_KEY` 已正确设置
- 确认 API Key 有余额
- 网络需能访问 `api.openai.com`
- 企业网络可能需要配置代理：设置 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量

### 索引速度慢

- 减小 `MAX_INDEX_FILE_SIZE_KB`（默认 200KB），跳过更大的文件
- 在项目根目录排除不必要的目录（`.gitignore` 中的文件不会被索引）
- 设置 `AUTO_INDEX=false` 禁用自动索引，手动通过项目索引

### Windows 下中文路径乱码

- 确保命令行使用 UTF-8 编码
- 或者在启动前执行：`chcp 65001`

### 数据库锁定错误

- 不要同时运行多个 Atlas Memory MCP 实例
- 删除 `data/memory.db` 后重新启动可重置数据库

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[ai,dev]"

# 运行全部测试
pytest tests/ -v

# 含覆盖率报告
pytest tests/ -v --cov=src/atlas_memory --cov-report=term-missing

# 单个测试文件
pytest tests/test_database.py -v
```

### 项目结构

```
atlas-memory-mcp/
├── src/atlas_memory/
│   ├── server.py              # FastMCP 入口 + 5 个 MCP 工具注册
│   ├── config.py              # 11 个环境变量的配置管理
│   ├── models/
│   │   └── entities.py        # Entity / Relation / Observation 数据模型
│   ├── storage/
│   │   └── database.py        # SQLite CRUD（三个表 + 6 个索引）
│   ├── tools/
│   │   ├── search.py          # search_entities 实现
│   │   ├── relations.py       # get_relations 实现
│   │   └── observations.py    # list/add_observations 实现
│   ├── memory/
│   │   ├── graph.py           # 知识图谱引擎（索引 + 调用链查询）
│   │   ├── vector.py          # ChromaDB + OpenAI 向量搜索
│   │   └── lifecycle.py       # threading.Timer 自动清理
│   ├── parser/
│   │   └── code_parser.py     # tree-sitter Python AST 解析
│   └── sandbox/
│       ├── api_bridge.js      # JS 侧 API 桥接模板
│       └── executor.py        # Node.js 子进程执行管理
├── tests/
│   ├── conftest.py            # 测试 fixtures（隔离 DB + 临时目录）
│   ├── test_database.py       # 数据库 CRUD 测试（16 个）
│   ├── test_parser.py         # 代码解析测试（10 个）
│   ├── test_graph.py          # 知识图谱测试（5 个）
│   ├── test_vector.py         # 向量搜索测试（2 个）
│   ├── test_tools.py          # 工具测试（13 个）
│   ├── test_sandbox.py        # JS 沙箱测试（7 个）
│   ├── test_lifecycle.py      # 生命周期测试（5 个）
│   ├── test_integration.py    # 集成测试（2 个）
│   └── test_edge_cases.py     # 边界测试（7 个）
├── pyproject.toml
├── setup.py
└── AGENTS.md                  # 项目进度追踪
```
