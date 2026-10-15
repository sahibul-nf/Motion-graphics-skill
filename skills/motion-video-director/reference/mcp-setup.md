<!-- Motion Video Director · reference file, loaded on demand from SKILL.md -->
# 0b. Connecting MCPs (any agent)

Two ways — offer both:
- **Ask the agent (easiest):** the user just says *"connect the Playwright / Firecrawl MCP"*. If you can run terminal commands, add it yourself with the agent's CLI (below), reading the key from `.env` — never echo it. Then tell the user to restart/reload the agent session if the new tools don't appear.
- **Manual:** the user pastes the JSON/TOML block into the agent's MCP config file.

| Agent | Add via command | Config file (manual) |
|---|---|---|
| Claude Code | `claude mcp add <name> [-s project] -e KEY=value -- <command> <args…>` · check: `claude mcp list` / `/mcp` | `.mcp.json` in the project (project scope) or `~/.claude.json` |
| Codex CLI | `codex mcp add <name> --env KEY=value -- <command> <args…>` | `~/.codex/config.toml` → `[mcp_servers.<name>]` `command`, `args`, `env` |
| Cursor | Settings → MCP → Add | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` |
| Claude Desktop | Settings → Developer → Edit Config | `claude_desktop_config.json` |
| VS Code (Copilot agent / extensions) | Command palette → "MCP: Add Server" | `.vscode/mcp.json` |
| Claude.ai / Claude in the browser | Settings → Connectors (remote MCP URLs only) | — no local terminal: use a local agent for rendering |

Server definitions (JSON form used by `.mcp.json` / Cursor / Claude Desktop under `"mcpServers"`; same command/args/env for the CLIs and TOML):
```json
{
  "playwright": { "command": "npx", "args": ["@playwright/mcp@latest", "--user-data-dir", "<project>/../.browser-profile", "--output-dir", "<project>/cache/browser"] },
  "firecrawl":  { "command": "npx", "args": ["-y", "firecrawl-mcp"], "env": { "FIRECRAWL_API_KEY": "<from .env>" } },
  "lottiefiles":{ "command": "npx", "args": ["-y", "@lottiefiles/creator-mcp@latest"] }
}
```
Example (Claude Code, key read from `.env` without printing it): `set -a; . ./.env; set +a; claude mcp add -s project firecrawl -e FIRECRAWL_API_KEY="$FIRECRAWL_API_KEY" -- npx -y firecrawl-mcp`.
`uvx` comes with `uv` (`pip install uv`). Freesound / Pixabay / Unsplash MCPs are community servers — if none is available or it fails, **skip the MCP and call the REST APIs directly (§0c)**; that is fully supported.
Note: a project-scope `.mcp.json` containing real keys must be gitignored; prefer `-s local`/user scope or env references when the agent supports them.
