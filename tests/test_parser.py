from __future__ import annotations

from pathlib import Path

import pytest

from atlas_memory.parser.code_parser import CodeParser


SAMPLE_CODE = '''
def login(username, password):
    """Authenticate user."""
    result = verify_credentials(username, password)
    return result

class AuthService:
    """Authentication service."""

    def verify(self, token):
        return check_token(token)

def verify_credentials(user, pwd):
    import hashlib
    h = hashlib.sha256(pwd.encode()).hexdigest()
    return h == "abc"

def check_token(token):
    from jwt import decode
    return decode(token, "secret")
'''


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    f.write_text(SAMPLE_CODE)
    return f


class TestParser:
    def test_parse_functions(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        funcs = [e for e in entities if e.type.value == "function"]
        names = {f.name for f in funcs}
        assert "login" in names
        assert "verify_credentials" in names
        assert "check_token" in names

    def test_parse_classes(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        classes = [e for e in entities if e.type.value == "class"]
        assert len(classes) == 1
        assert classes[0].name == "AuthService"

    def test_function_signature(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        login = next(e for e in entities if e.name == "login")
        assert "login" in login.signature

    def test_docstring(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        login = next(e for e in entities if e.name == "login")
        assert login.docstring is not None
        assert "Authenticate user" in login.docstring

    def test_file_entity(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        file_entities = [e for e in entities if e.type.value == "file"]
        assert len(file_entities) == 1
        assert file_entities[0].name == "sample.py"

    def test_parse_calls(self, sample_file: Path):
        parser = CodeParser()
        _, relations = parser.parse_file(sample_file)

        calls = [r for r in relations if r.type.value == "calls"]
        call_pairs = {(r.from_id.split("::")[-1], r.to_id.split("::")[-1]) for r in calls}
        assert ("login", "verify_credentials") in call_pairs

    def test_parse_imports(self, sample_file: Path):
        parser = CodeParser()
        _, relations = parser.parse_file(sample_file)

        imports = [r for r in relations if r.type.value == "imports"]
        assert len(imports) >= 1

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.py"
        f.write_text("# just a comment\n")
        parser = CodeParser()
        entities, relations = parser.parse_file(f)
        assert len(entities) == 1  # file entity only
        assert len(relations) == 0

    def test_unsupported_extension(self, tmp_path: Path):
        f = tmp_path / "nosupport.txt"
        f.write_text("hello")
        parser = CodeParser()
        entities, relations = parser.parse_file(f)
        assert entities == []
        assert relations == []

    def test_line_numbers(self, sample_file: Path):
        parser = CodeParser()
        entities, _ = parser.parse_file(sample_file)

        login = next(e for e in entities if e.name == "login")
        assert login.line_start == 2  # line after decorator in SAMPLE_CODE
