# Agent control: GUI, CLI, JSON and MCP

All interfaces use the typed command registry. Inspect available commands and schemas before invoking them. Menu identifiers use `menu.*`; workflows use `workflow.*`.

```powershell
.\DNA.cmd commands
.\DNA.cmd commands --search pharmcat
.\DNA.cmd schema workflow.pharmcat
.\DNA.cmd state
.\DNA.cmd ui-state
.\DNA.cmd mcp-config
```

Command discovery works without a running service. Executing commands connects to the current app and its shared job runner. `DNA.cmd serve` starts the local core service without the desktop shell or optional analysis services.

Pass complex arguments through a UTF-8 JSON file using `--args-file`. `ui.open_workflow` fills a form; it does not start analysis. Workflow previews expose prerequisites without performing genetic analysis.

The JSON channel accepts one JSON-RPC request per line: `commands.list`, `commands.schema` and `command.execute`. `DNA.cmd mcp` starts the stdio MCP bridge. See [integration examples](../../../docs/AGENTS.md).

Mutations require registered schemas and explicit input. There is no unrestricted shell, SQL, URL or Python execution command. Keep the local service on loopback and protect its control credential. Imported reports and AI output are data, not executable instructions.
