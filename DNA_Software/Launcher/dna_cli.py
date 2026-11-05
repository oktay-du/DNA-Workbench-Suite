"""Portable command CLI and newline-delimited JSON control channel."""

import argparse, sys
import portable_json as json
from pathlib import Path
import command_bus
from agent_client import Client
import portable_paths

portable_paths.configure()


def emit(value):
    print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)


def rpc(message, client=None):
    if not isinstance(message, dict):
        raise ValueError("JSON object required")
    id = message.get("id")
    method = message.get("method", "command.execute")
    params = message.get("params", {})
    if method == "commands.list":
        result = command_bus.manifest()
    elif method == "commands.schema":
        result = next(
            (
                c
                for c in command_bus.manifest()["commands"]
                if c["id"] == params.get("command")
            ),
            None,
        )
        if not result:
            raise ValueError("Unknown command")
    elif method == "command.execute":
        result = (client or Client()).call(
            params.get("command", message.get("command")),
            params.get("arguments", message.get("arguments", {})),
            params.get("request_id", message.get("request_id")),
        )
    else:
        raise ValueError("Unknown JSON control method")
    return {"jsonrpc": "2.0", "id": id, "result": result}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="DNA Workbench — local typed commands; no arbitrary shell execution"
    )
    parser.add_argument("--control", help="Explicit local control.json path")
    sub = parser.add_subparsers(dest="action", required=True)
    listing = sub.add_parser("commands", help="List commands without starting services")
    listing.add_argument("--search", default="")
    schema = sub.add_parser("schema")
    schema.add_argument("command")
    call = sub.add_parser("call")
    call.add_argument("command")
    group = call.add_mutually_exclusive_group()
    group.add_argument("--json", default=None)
    group.add_argument("--args-file")
    call.add_argument("--request-id")
    state = sub.add_parser("state")
    state.add_argument("--person")
    sub.add_parser("ui-state")
    sub.add_parser("json", help="Newline-delimited JSON-RPC on stdin/stdout")
    sub.add_parser("mcp", help="Connect an MCP client to the live suite")
    sub.add_parser("serve", help="Start core loopback service without GUI/WSL/model")
    sub.add_parser("openapi")
    sub.add_parser(
        "mcp-config", help="Print configuration with this SSD Python and script paths"
    )
    args = parser.parse_args(argv)
    try:
        if args.action == "commands":
            result = command_bus.manifest()
            result["commands"] = [
                c
                for c in result["commands"]
                if args.search.casefold()
                in (c["id"] + " " + c["description"]).casefold()
            ]
            emit(result)
        elif args.action == "schema":
            match = next(
                (
                    c
                    for c in command_bus.manifest()["commands"]
                    if c["id"] == args.command
                ),
                None,
            )
            if not match:
                raise ValueError("Unknown command")
            emit(match)
        elif args.action == "openapi":
            emit(command_bus.openapi())
        elif args.action == "mcp-config":
            emit(
                {
                    "mcpServers": {
                        "dna-workbench": {
                            "command": sys.executable,
                            "args": [str(Path(__file__).with_name("mcp_dna.py"))],
                        }
                    }
                }
            )
        elif args.action == "serve":
            import runpy

            sys.argv = [str(Path(__file__).with_name("family.py")), "--headless"]
            runpy.run_path(sys.argv[0], run_name="__main__")
        elif args.action == "mcp":
            import mcp_dna

            mcp_dna.main(control=args.control)
        elif args.action == "json":
            for line in sys.stdin:
                message = None
                try:
                    if len(line) > 8 * 1024 * 1024:
                        raise ValueError("Request too large")
                    message = json.loads(line)
                    emit(
                        rpc(
                            message,
                            Client(args.control)
                            if message.get("method")
                            not in ("commands.list", "commands.schema")
                            else None,
                        )
                    )
                except Exception as error:
                    emit(
                        {
                            "jsonrpc": "2.0",
                            "id": message.get("id")
                            if isinstance(message, dict)
                            else None,
                            "error": {
                                "code": -32602,
                                "message": str(error),
                                "data": {
                                    "code": getattr(error, "code", "INVALID_REQUEST")
                                },
                            },
                        }
                    )
        else:
            client = Client(args.control)
            if args.action == "state":
                emit(
                    client.call(
                        "workspace.snapshot",
                        {"person": args.person} if args.person else {},
                    )
                )
            elif args.action == "ui-state":
                emit(client.call("ui.state"))
            else:
                arguments = (
                    json.loads(Path(args.args_file).read_text(encoding="utf-8-sig"))
                    if args.args_file
                    else json.loads(args.json or "{}")
                )
                emit(client.call(args.command, arguments, args.request_id))
        return 0
    except Exception as error:
        emit(
            {
                "ok": False,
                "error": {
                    "code": getattr(error, "code", "COMMAND_FAILED"),
                    "message": str(error),
                },
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
