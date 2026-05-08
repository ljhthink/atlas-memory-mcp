from __future__ import annotations

from pathlib import Path

from atlas_memory.memory.graph import GraphEngine


SAMPLE_CODE = '''
def login(user, pwd):
    return verify(user, pwd)

def verify(u, p):
    return check(u)

def check(u):
    return True
'''


class TestGraphEngine:
    def test_index_project(self, config, db, tmp_path: Path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "a.py").write_text(SAMPLE_CODE)
        (project / "b.py").write_text("def helper(): pass\n")

        config.project_root = str(project)
        engine = GraphEngine(config, db)
        count = engine.index_project()
        assert count >= 2

    def test_index_file(self, config, db, tmp_path: Path):
        f = tmp_path / "test.py"
        f.write_text(SAMPLE_CODE)
        config.project_root = str(tmp_path)
        engine = GraphEngine(config, db)
        count = engine.index_file(f)
        assert count >= 3  # file + 3 functions

    def test_get_callers(self, config, db, tmp_path: Path):
        f = tmp_path / "call.py"
        f.write_text(SAMPLE_CODE)
        config.project_root = str(tmp_path)
        engine = GraphEngine(config, db)
        engine.index_file(f)

        verify_eid = None
        all_entities = db.query_entities(keyword="verify")
        for e in all_entities:
            if e.name == "verify":
                verify_eid = e.id
                break
        assert verify_eid is not None

        callers = engine.get_callers(verify_eid)
        caller_names = {c.name for c in callers}
        assert "login" in caller_names

    def test_get_dependencies(self, config, db, tmp_path: Path):
        f = tmp_path / "dep.py"
        f.write_text(SAMPLE_CODE)
        config.project_root = str(tmp_path)
        engine = GraphEngine(config, db)
        engine.index_file(f)

        login_eid = None
        all_entities = db.query_entities(keyword="login")
        for e in all_entities:
            if e.name == "login":
                login_eid = e.id
                break
        assert login_eid is not None

        deps = engine.get_dependencies(login_eid)
        dep_names = {d.name for d in deps}
        assert "verify" in dep_names

    def test_index_nonexistent_project(self, config, db):
        config.project_root = "/nonexistent/path"
        engine = GraphEngine(config, db)
        count = engine.index_project()
        assert count == 0
