"""
Phase 5A tests — sandbox jail + tool dispatch. No API calls.
Run:  pytest test_phase5a.py -v
"""
import pytest

import sandbox_tools
from sandbox_tools import list_files, read_file, run_tool, write_file


# ---------- path jail ----------

def test_write_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    assert "OK" in write_file("src/app.js", "console.log('hi');")
    assert read_file("src/app.js") == "console.log('hi');"

def test_path_jail_blocks_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    with pytest.raises(ValueError):
        write_file("../evil.txt", "nope")

def test_path_jail_blocks_absolute(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    with pytest.raises(ValueError):
        write_file("C:/Windows/evil.txt", "nope")

def test_read_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    assert "ERROR" in read_file("ghost.txt")

def test_list_files(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    assert "(sandbox empty)" in list_files()
    write_file("a.txt", "x")
    write_file("b/c.txt", "y")
    listing = list_files()
    assert "a.txt" in listing and "b/c.txt" in listing


# ---------- dispatch ----------

def test_dispatch_write(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    result = run_tool("write_file", '{"path": "x.txt", "content": "hello"}')
    assert result.startswith("OK")
    assert read_file("x.txt") == "hello"

def test_dispatch_finish(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    import json
    out = json.loads(run_tool("finish", '{"summary": "done"}'))
    assert out["finished"] is True and out["summary"] == "done"

def test_dispatch_unknown_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    assert "ERROR" in run_tool("delete_everything", "{}")

def test_dispatch_bad_json(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_tools, "SANDBOX", tmp_path)
    assert "ERROR" in run_tool("write_file", "{not json")