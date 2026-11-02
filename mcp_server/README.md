# Longview MCP server

Exposes the skills in this repo over MCP (stdio), so an assistant loads only the skill it needs.

## Install

```sh
pip install -r mcp_server/requirements.txt
```

## Add to a client

Claude Code:

```sh
claude mcp add longview -- python /absolute/path/to/longview-skills/mcp_server/server.py
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "longview": {
      "command": "python",
      "args": ["/absolute/path/to/longview-skills/mcp_server/server.py"]
    }
  }
}
```

Set `LONGVIEW_ROOT` if the server file lives outside the checkout.

## Tools

| Tool | Purpose |
|---|---|
| `get_instructions` | Returns `AGENTS.md`. Call first. |
| `list_skills(domain?)` | One line per skill. |
| `get_skill(name)` | `SKILL.md` plus its extra files. |
| `get_skill_file(name, path)` | A text file inside the skill folder. |
| `route(request)` | Keyword router hint (English only). |
| `run_script(name, script, args?)` | Runs a `.py` from that skill's `scripts/` (60 s timeout). |

`run_script` executes code from this repo with your user rights. Only point `LONGVIEW_ROOT` at a checkout you trust.
