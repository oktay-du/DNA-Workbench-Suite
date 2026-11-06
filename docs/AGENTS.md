# GUI, CLI, JSON and MCP

On Windows, start `DNA_Launcher.exe`. On Linux, run `python3 DNA_Software/Launcher/dna_cli.py desktop` or `./DNA-Workbench.sh` from the Linux zip. `python DNA_Software/Launcher/dna_cli.py serve` starts the service without a window. The local control file contains a credential; keep it private. GUI commands can require the desktop owner to be connected. Mutations use registered schemas/effects rather than arbitrary shell execution.

```powershell
.\DNA.cmd commands
.\DNA.cmd schema sample.create
.\DNA.cmd call sample.info
.\DNA.cmd call sample.create
.\DNA.cmd call app.versions
.\DNA.cmd state
.\DNA.cmd ui-state
.\DNA.cmd mcp-config
```

The `commands` and `schema` operations do not need a running service. `mcp-config` prints the local interpreter/script configuration for your MCP client; `mcp` starts the stdio bridge. `json` accepts newline-delimited JSON-RPC using `commands.list`, `commands.schema` and `command.execute`. Call `openapi` for generated API descriptions. See [implementation details](../DNA_Software/Launcher/AGENT_CONTROL.md).

Discover current names and argument schemas instead of inventing parameters. Read workspace/profile state, select suitable evidence, preview requirements, then queue a named workflow. Sample creation and other mutations are explicit. A local AI assistant can help inspect tool/result context but its text is not evidence of a scientific calculation. Keep the API on loopback; never expose its control credential through screenshots or public logs.

Sequence-lab commands include `workflow.variant_evidence_audit`, `workflow.sequence_explore`, `workflow.model_readiness`, `workflow.dna_message` and `workflow.agent_handoff`. `research.projects` returns the reviewed architecture catalog without reading profile data. Handoff exports are local snapshots, not authorization to upload their contents. See [Sequence lab](RESEARCH_LAB.md) for coordinate conventions and limits.
