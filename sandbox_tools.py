"""
sandbox_tools.py — Safe file tools for the demo agent.
All paths are jailed inside sandbox/ (no "..", no absolute paths).
"""
import json
from pathlib import Path

SANDBOX = Path("sandbox")


def _safe_path(path: str) -> Path:
    p = SANDBOX / path
    resolved = p.resolve()
    if not str(resolved).startswith(str(SANDBOX.resolve())):
        raise ValueError(f"path escapes sandbox: {path}")
    return resolved


def write_file(path: str, content: str) -> str:
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"OK: wrote {len(content)} chars to {path}"


def read_file(path: str) -> str:
    p = _safe_path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    return p.read_text(encoding="utf-8")

def list_files() -> str:
    if not SANDBOX.exists():
        return "(sandbox empty)"
    files = sorted(str(p.relative_to(SANDBOX).as_posix())
                   for p in SANDBOX.rglob("*") if p.is_file())
    return "\n".join(files) if files else "(sandbox empty)"

# --- OpenAI function-calling schema ---
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Create or overwrite a file inside the project sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the project sandbox.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    }},
    {"type": "function", "function": {
        "name": "list_files",
        "description": "List all files in the project sandbox.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "finish",
        "description": "Call when the goal is fully achieved. Provide a short summary of what was built.",
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    }},
]


def run_tool(name: str, arguments: str) -> str:
    """Execute a tool call by name with a JSON arguments string."""
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return f"ERROR: invalid tool arguments: {arguments[:100]}"
    try:
        if name == "write_file":
            return write_file(args["path"], args["content"])
        if name == "read_file":
            return read_file(args["path"])
        if name == "list_files":
            return list_files()
        if name == "finish":
            return json.dumps({"finished": True, "summary": args.get("summary", "")})
        return f"ERROR: unknown tool {name}"
    except (KeyError, ValueError) as e:
        return f"ERROR: {e}"