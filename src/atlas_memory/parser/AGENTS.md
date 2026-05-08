# parser - 代码解析器

## 职责
使用 tree-sitter 解析源代码 AST，提取实体定义和关系。

## 对外接口
| 接口 | 说明 |
|------|------|
| CodeParser() | 解析器主类，按语言扩展名分发 |
| parse_file(filepath) -> (list[Entity], list[Relation]) | 解析单个文件 |
| SUPPORTED | 已支持的语言扩展名映射 dict |

## 解析目标

### Python (.py)
- function_definition -> Entity(type=FUNCTION) + signature + docstring
- class_definition -> Entity(type=CLASS) + docstring
- import_statement / import_from_statement -> Relation(type=IMPORTS)
- call 表达式 -> Relation(type=CALLS) (尽力解析调用目标)

### TypeScript (.ts, .tsx) - 待扩展
- function_declaration / arrow_function -> Entity(type=FUNCTION)
- class_declaration -> Entity(type=CLASS)
- import_statement -> Relation(type=IMPORTS)
- call_expression -> Relation(type=CALLS)

### JavaScript (.js, .jsx) - 待扩展
- 同 TypeScript 解析逻辑

## 功能清单
| # | 功能 | 描述 | 状态 |
|---|------|------|------|
| 1 | Python 解析 | 函数/类/变量提取 + line 定位 | [x] |
| 2 | 导入关系提取 | import / from-import -> Relation | [x] |
| 3 | 调用关系提取 | call 表达式 -> Relation | [x] |
| 4 | 语言检测 | 扩展名 -> Language 映射 | [x] |
| 5 | TypeScript 解析 | 后续扩展 | [ ] |
| 6 | JavaScript 解析 | 后续扩展 | [ ] |

## 支持语言
| 语言 | 扩展名 | tree-sitter 语法包 | 状态 |
|------|--------|-------------------|------|
| Python | .py | tree-sitter-python | [ ] 计划中 |
| TypeScript | .ts, .tsx | tree-sitter-typescript | [ ] 待扩展 |
| JavaScript | .js, .jsx | tree-sitter-javascript | [ ] 待扩展 |

## 依赖
- tree-sitter (Python binding)
- tree-sitter-python 语法文件
- models/entities.py (Entity, Relation)

## 修改时间线
### 2026-05-08 23:30
- **[added]** 实现 CodeParser: Python 解析 (函数/类/调用/导入) + tree-sitter 0.25 适配
  - 文件: src/atlas_memory/parser/code_parser.py
  - 测试: 10 测试全过, 95% 行覆盖

### 2026-05-08 22:00
- **[added]** 初始化 AGENTS.md，定义 CodeParser 接口和支持语言规划
  - 文件: src/atlas_memory/parser/AGENTS.md
