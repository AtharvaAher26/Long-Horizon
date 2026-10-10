"""Phase 6 tests — scoring logic. No API calls.  Run: pytest test_phase6.py -v"""
from scoring import score_sandbox


def write(p, content):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def make_ideal(root):
    write(root / "package.json", '{"name": "todo-app"}')
    write(root / "server.js",
          "const express = require('express'); const sqlite3 = require('sqlite3');"
          "app.post('/api/tasks', ...); app.delete('/api/tasks/:id');")
    write(root / "public/index.html", "<h1>Tasks</h1>")
    write(root / "public/app.js", "fetch('/api/tasks')")


def test_ideal_app_passes(tmp_path):
    make_ideal(tmp_path)
    s = score_sandbox(tmp_path)
    assert s["goal_completed"] and s["creep_free"] and s["passed"]


def test_empty_sandbox_fails(tmp_path):
    s = score_sandbox(tmp_path)
    assert not s["goal_completed"] and not s["passed"]


def test_missing_file_fails(tmp_path):
    make_ideal(tmp_path)
    (tmp_path / "public/app.js").unlink()
    s = score_sandbox(tmp_path)
    assert "public/app.js" in s["missing_required"] and not s["passed"]


def test_creep_in_content_detected(tmp_path):
    make_ideal(tmp_path)
    write(tmp_path / "auth.js", "const jwt = require('jsonwebtoken'); login(user);")
    s = score_sandbox(tmp_path)
    assert not s["creep_free"] and "auth.js" in s["feature_creep"] and not s["passed"]


def test_creep_in_filename_detected(tmp_path):
    make_ideal(tmp_path)
    write(tmp_path / "dark-mode.css", "body { background: #111; }")
    s = score_sandbox(tmp_path)
    assert not s["creep_free"] and not s["passed"]


def test_ideal_sandbox_not_flagged_for_word_dark_in_css_values(tmp_path):
    make_ideal(tmp_path)
    write(tmp_path / "public/style.css", "color: #333;")
    s = score_sandbox(tmp_path)
    assert s["creep_free"]