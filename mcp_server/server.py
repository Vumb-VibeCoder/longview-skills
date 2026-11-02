#!/usr/bin/env python3
"""Longview skills as an MCP server (stdio).

Tools: get_instructions, list_skills, get_skill, get_skill_file, route, run_script.
Only this server needs the `mcp` package; the skills and scripts stay stdlib-only.
Set LONGVIEW_ROOT to point at a different checkout of the repo.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(os.environ.get("LONGVIEW_ROOT") or Path(__file__).resolve().parent.parent).resolve()
DOMAINS = ("core", "coding", "finance", "design", "ui")
TEXT_EXT = {".md", ".json", ".py", ".txt", ".yml", ".yaml", ".jsonl"}
MAX_BYTES = 200_000
SCRIPT_TIMEOUT = 60

mcp = FastMCP("longview-skills")


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t")):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def _skills() -> dict:
    found = {}
    for d in DOMAINS:
        for md in sorted((ROOT / d).glob("*/SKILL.md")):
            fm = _frontmatter(md.read_text(encoding="utf-8", errors="replace"))
            found[md.parent.name] = {
                "name": md.parent.name,
                "domain": d,
                "description": fm.get("description", ""),
                "path": md.parent,
            }
    return found


def _skill_dir(name: str) -> Path:
    s = _skills().get(name)
    if not s:
        raise ValueError(f"Unknown skill '{name}'. Call list_skills first.")
    return s["path"]


def _safe_file(skill: str, rel: str) -> Path:
    base = _skill_dir(skill).resolve()
    p = (base / rel).resolve()
    if base != p and base not in p.parents:
        raise ValueError("Path escapes the skill folder.")
    if not p.is_file():
        raise ValueError(f"No such file in {skill}: {rel}")
    return p


@mcp.tool()
def get_instructions() -> str:
    """Read this first. Returns AGENTS.md: the rules every answer must follow
    (ROUTE/CLASS lines, evidence, exit paths)."""
    return (ROOT / "AGENTS.md").read_text(encoding="utf-8")


@mcp.tool()
def list_skills(domain: str = "") -> str:
    """List skills with a one-line description. Optional domain filter:
    core, coding, finance, design, ui."""
    rows = []
    for s in _skills().values():
        if domain and s["domain"] != domain:
            continue
        desc = s["description"]
        desc = desc if len(desc) <= 220 else desc[:217] + "..."
        rows.append(f"{s['domain']}/{s['name']}: {desc}")
    return "\n".join(rows) or "No skills match."


@mcp.tool()
def get_skill(name: str) -> str:
    """Return SKILL.md for a skill plus the list of its extra files
    (scripts/, templates/) that get_skill_file / run_script can use."""
    d = _skill_dir(name)
    body = (d / "SKILL.md").read_text(encoding="utf-8")
    extra = sorted(
        str(p.relative_to(d)).replace("\\", "/")
        for p in d.rglob("*")
        if p.is_file() and p.name != "SKILL.md"
    )
    if extra:
        body += "\n\n---\nExtra files:\n" + "\n".join(f"- {e}" for e in extra)
    return body


@mcp.tool()
def get_skill_file(name: str, path: str) -> str:
    """Read a text file inside a skill folder, e.g. path='templates/model.example.json'
    or 'scripts/cashflow.py'."""
    p = _safe_file(name, path)
    if p.suffix.lower() not in TEXT_EXT:
        raise ValueError("Only text files can be read.")
    data = p.read_bytes()[:MAX_BYTES]
    return data.decode("utf-8", errors="replace")


def _run(cmd: list, timeout: int = SCRIPT_TIMEOUT) -> str:
    try:
        r = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s"
    out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
    return f"exit={r.returncode}\n{out.strip()}"[:MAX_BYTES]


@mcp.tool()
def route(request: str) -> str:
    """Suggest which skills apply to a request (keyword router, English only).
    Treat the result as a hint; core/skill-router/SKILL.md wins on disagreement."""
    return _run([sys.executable, str(ROOT / "core/skill-router/scripts/route.py"), request])


@mcp.tool()
def run_script(name: str, script: str, args: list[str] | None = None) -> str:
    """Run a skill's script (python only, from its scripts/ folder) and return
    'exit=<code>' plus output. Example: name='long-horizon-cashflow',
    script='cashflow.py', args=['finance/long-horizon-cashflow/templates/model.example.json'].
    Paths in args are relative to the repo root. Exit 2 means bad input."""
    rel = script if script.startswith("scripts/") else f"scripts/{script}"
    p = _safe_file(name, rel)
    if p.suffix != ".py":
        raise ValueError("Only .py scripts can be run.")
    return _run([sys.executable, str(p), *(args or [])])


if __name__ == "__main__":
    mcp.run()
