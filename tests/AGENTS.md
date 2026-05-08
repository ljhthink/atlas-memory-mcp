# tests - 测试套件

## 职责
单元测试和集成测试，覆盖所有核心模块。

## 运行方式
```bash
# 全部测试
pytest tests/ -v

# 含覆盖率
pytest tests/ -v --cov=src/atlas_memory --cov-report=term-missing

# 单个文件
pytest tests/test_database.py -v
```

## 覆盖矩阵

| 测试文件 | 覆盖模块 | 类型 | 目标覆盖率 | 状态 |
|----------|----------|------|-----------|------|
| test_database.py | storage/ | 单元 | > 90% | [x] |
| test_parser.py | parser/ | 单元 | > 85% | [x] |
| test_graph.py | memory/graph | 单元 | > 85% | [x] |
| test_vector.py | memory/vector | 单元 | > 80% | [x] |
| test_sandbox.py | sandbox/ | 单元 | > 85% | [ ] |
| test_tools.py | tools/ | 单元 | > 85% | [x] |
| test_integration.py | 全链路 | 集成 | > 70% | [x] |

## 测试数据约定
- 使用 fixture 创建临时 SQLite (内存) 和 ChromaDB (临时目录)
- 测试数据放在 tests/fixtures/ 目录
- 每个测试独立，不依赖执行顺序

## 修改时间线
### 2026-05-08 23:30
- **[added]** test_parser.py (10 测试) + test_graph.py (5 测试) + test_vector.py (2 测试), 总计 46 测试全过, 83% 覆盖

### 2026-05-08 23:00
- **[added]** test_tools.py (13 测试) + test_integration.py (2 测试), 总计 29 测试全过, 91% 覆盖
  - 文件: tests/test_tools.py, tests/test_integration.py

### 2026-05-08 22:30
- **[added]** 实现 conftest.py (DB 隔离 fixture) + test_database.py (16 测试, 93% 覆盖)
  - 文件: tests/conftest.py, tests/test_database.py

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义测试覆盖矩阵和运行方式
  - 文件: tests/AGENTS.md
