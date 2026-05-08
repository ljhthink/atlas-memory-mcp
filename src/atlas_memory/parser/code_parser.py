from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython

from atlas_memory.models.entities import Entity, EntityType, Relation, RelationType

PY_LANG = Language(tspython.language())
_PARSER = Parser(PY_LANG)


def _make_id(path: str, name: str) -> str:
    h = hashlib.md5(path.encode()).hexdigest()[:8]
    return f"{h}::{name}"


def _extract_docstring(body_node) -> Optional[str]:
    for child in body_node.children:
        if child.type == "expression_statement":
            for sub in child.children:
                if sub.type == "string":
                    text = sub.text.decode()
                    if text.startswith('"""') or text.startswith("'''"):
                        return text.strip('"').strip("'")
    return None


FUNC_QUERY = Query(
    PY_LANG,
    "(function_definition name: (identifier) @func.name) @func.def",
)
CLASS_QUERY = Query(
    PY_LANG,
    "(class_definition name: (identifier) @class.name) @class.def",
)


class CodeParser:
    SUPPORTED = {".py": "python"}

    def parse_file(self, filepath: Path) -> tuple[list[Entity], list[Relation]]:
        if filepath.suffix not in self.SUPPORTED:
            return [], []

        code = filepath.read_bytes()
        tree = _PARSER.parse(code)

        path_str = filepath.as_posix()
        entities: list[Entity] = []
        relations: list[Relation] = []

        entities.append(
            Entity(
                id=_make_id(path_str, filepath.stem),
                type=EntityType.FILE,
                name=filepath.name,
                path=path_str,
            )
        )

        file_eid = _make_id(path_str, filepath.stem)

        functions = self._extract_functions(tree.root_node, path_str, code)
        entities.extend(functions)

        classes = self._extract_classes(tree.root_node, path_str, code)
        entities.extend(classes)

        import_rels = self._extract_imports(tree.root_node, path_str)
        relations.extend(import_rels)

        call_rels = self._extract_calls(tree.root_node, path_str, code)
        relations.extend(call_rels)

        for e in functions + classes:
            relations.append(
                Relation(
                    from_id=e.id,
                    to_id=file_eid,
                    type=RelationType.DEPENDS_ON,
                )
            )

        return entities, relations

    def _extract_functions(
        self, root_node, path_str: str, code: bytes
    ) -> list[Entity]:
        results: list[Entity] = []
        cursor = QueryCursor(FUNC_QUERY)
        caps = cursor.captures(root_node)

        def_nodes = caps.get("func.def", [])
        name_nodes = caps.get("func.name", [])

        for def_node, name_node in zip(def_nodes, name_nodes):
            name = name_node.text.decode()
            sig = code[def_node.start_byte : def_node.end_byte].decode().split(":")[0].strip()
            body = def_node.child_by_field_name("body")
            docstring = _extract_docstring(body) if body else None

            results.append(
                Entity(
                    id=_make_id(path_str, name),
                    type=EntityType.FUNCTION,
                    name=name,
                    path=path_str,
                    line_start=def_node.start_point[0] + 1,
                    line_end=def_node.end_point[0] + 1,
                    signature=sig,
                    docstring=docstring,
                )
            )
        return results

    def _extract_classes(
        self, root_node, path_str: str, code: bytes
    ) -> list[Entity]:
        results: list[Entity] = []
        cursor = QueryCursor(CLASS_QUERY)
        caps = cursor.captures(root_node)

        def_nodes = caps.get("class.def", [])
        name_nodes = caps.get("class.name", [])

        for def_node, name_node in zip(def_nodes, name_nodes):
            name = name_node.text.decode()
            body = def_node.child_by_field_name("body")
            docstring = _extract_docstring(body) if body else None

            results.append(
                Entity(
                    id=_make_id(path_str, name),
                    type=EntityType.CLASS,
                    name=name,
                    path=path_str,
                    line_start=def_node.start_point[0] + 1,
                    line_end=def_node.end_point[0] + 1,
                    signature=f"class {name}",
                    docstring=docstring,
                )
            )
        return results

    def _extract_imports(
        self, root_node, path_str: str
    ) -> list[Relation]:
        results: list[Relation] = []

        for node in self._walk(root_node):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        module = child.text.decode()
                        target_id = _make_id(module, module)
                        results.append(
                            Relation(
                                from_id=_make_id(path_str, path_str.rsplit("/", 1)[-1]),
                                to_id=target_id,
                                type=RelationType.IMPORTS,
                            )
                        )

            elif node.type == "import_from_statement":
                module_name = None
                imported_names = []
                for child in node.children:
                    if child.type == "dotted_name" and module_name is None:
                        module_name = child.text.decode()
                    elif child.type == "dotted_name":
                        imported_names.append(child.text.decode())
                    elif child.type == "aliased_import":
                        for sub in child.children:
                            if sub.type == "dotted_name":
                                imported_names.append(sub.text.decode())

                for name in imported_names:
                    target_id = (
                        _make_id(module_name, name)
                        if module_name
                        else _make_id(name, name)
                    )
                    results.append(
                        Relation(
                            from_id=_make_id(path_str, path_str.rsplit("/", 1)[-1]),
                            to_id=target_id,
                            type=RelationType.IMPORTS,
                        )
                    )

        return results

    def _extract_calls(
        self, root_node, path_str: str, code: bytes
    ) -> list[Relation]:
        results: list[Relation] = []
        seen = set()

        for node in self._walk(root_node):
            if node.type == "call":
                func_node = node.child_by_field_name("function")
                if func_node is not None:
                    if func_node.type == "identifier":
                        name = func_node.text.decode()
                    elif func_node.type == "attribute":
                        name_parts = []
                        for sub in func_node.children:
                            if sub.type == "identifier":
                                name_parts.append(sub.text.decode())
                        name = ".".join(name_parts)
                    else:
                        continue

                    caller_name = self._find_enclosing_function(node)
                    if caller_name is None:
                        continue

                    pair = (caller_name, name)
                    if pair in seen:
                        continue
                    seen.add(pair)

                    caller_id = _make_id(path_str, caller_name)
                    callee_id = _make_id(path_str, name)
                    results.append(
                        Relation(
                            from_id=caller_id,
                            to_id=callee_id,
                            type=RelationType.CALLS,
                        )
                    )
        return results

    def _find_enclosing_function(self, node) -> Optional[str]:
        current = node.parent
        while current is not None:
            if current.type in ("function_definition", "class_definition"):
                name_node = current.child_by_field_name("name")
                if name_node is not None:
                    return name_node.text.decode()
            current = current.parent
        return None

    def _walk(self, node):
        yield node
        for child in node.children:
            yield from self._walk(child)
