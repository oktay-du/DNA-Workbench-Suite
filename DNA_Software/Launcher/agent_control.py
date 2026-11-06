"""Authenticated loopback discovery and an acknowledged desktop UI event queue."""

import collections, datetime, os, threading, time, uuid
import portable_json as json
import suite_api

LOCK = threading.RLock()
EVENTS = collections.OrderedDict()
GUI = False
INSTANCE = ""
OWNER = ""
LAST_SEEN = 0
SNAPSHOT = {}


def control_path():
    return suite_api.ROOT / "DNA_Software/UserData/Launcher/control.json"


def publish(server, gui=True):
    global GUI, INSTANCE, OWNER, LAST_SEEN, SNAPSHOT
    path = control_path()
    if path.exists():
        from agent_client import Client, ClientError

        try:
            Client(path, timeout=1)
        except (ClientError, ValueError, OSError):
            pass
        else:
            raise RuntimeError(
                "A local DNA Workbench service is already running for this folder. Use it or stop the headless service before starting another instance."
            )
    GUI = gui
    INSTANCE = uuid.uuid4().hex
    OWNER = ""
    LAST_SEEN = 0
    SNAPSHOT = {}
    server.agent_instance = INSTANCE
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(
            {
                "url": "http://127.0.0.1:" + str(server.server_port),
                "token": server.token,
                "instance": INSTANCE,
                "pid": os.getpid(),
                "gui": gui,
            }
        ),
        encoding="utf-8",
    )
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    temp.replace(path)


def unpublish():
    path = control_path()
    try:
        if json.loads(path.read_text(encoding="utf-8")).get("instance") == INSTANCE:
            path.unlink()
    except (OSError, ValueError):
        pass


def state():
    with LOCK:
        return {
            "instance": INSTANCE,
            "gui_available": GUI,
            "attached": bool(OWNER and time.monotonic() - LAST_SEEN < 10),
            "view": dict(SNAPSHOT),
            "events": [
                {k: v for k, v in e.items() if k not in ("payload",)}
                for e in list(EVENTS.values())[-20:]
            ],
        }


def enqueue(payload):
    from command_bus import CommandError

    if not GUI:
        raise CommandError(
            "NO_GUI",
            "No desktop GUI is attached. Start DNA_Launcher.exe on Windows, or run dna_cli.py desktop on Linux.",
        )
    with LOCK:
        if sum(e["status"] == "pending" for e in EVENTS.values()) >= 50:
            raise CommandError("UI_QUEUE_FULL", "Too many pending GUI commands")
        id = uuid.uuid4().hex
        EVENTS[id] = {
            "event_id": id,
            "status": "pending",
            "payload": payload,
            "created": datetime.datetime.now().astimezone().isoformat(),
        }
        while len(EVENTS) > 250:
            EVENTS.popitem(last=False)
        return {
            "event_id": id,
            "status": "queued",
            "acknowledged": False,
            "payload": payload,
        }


def poll(r):
    global OWNER, LAST_SEEN, SNAPSHOT
    client = r.get("client", "")
    if not isinstance(client, str) or not 1 <= len(client) <= 80:
        raise ValueError("Invalid UI client")
    with LOCK:
        if OWNER and OWNER != client and time.monotonic() - LAST_SEEN < 10:
            return {"owner": False, "events": []}
        OWNER = client
        LAST_SEEN = time.monotonic()
        view = r.get("view", {})
        if isinstance(view, dict):
            SNAPSHOT = {
                k: v
                for k, v in view.items()
                if k
                in (
                    "route",
                    "person",
                    "workflow",
                    "inputs",
                    "language",
                    "theme",
                    "research_feature",
                    "navigation_open",
                )
            }
        events = [dict(e) for e in EVENTS.values() if e["status"] == "pending"][:1]
        return {"owner": True, "events": events}


def ack(r):
    global SNAPSHOT
    with LOCK:
        if r.get("client") != OWNER:
            raise ValueError("Not the active GUI client")
        event = EVENTS.get(r.get("event_id"))
        if not event:
            raise ValueError("Unknown GUI event")
        event.update(
            status="applied" if r.get("ok") is True else "failed",
            detail=str(r.get("detail", ""))[:1000],
            finished=datetime.datetime.now().astimezone().isoformat(),
        )
        if isinstance(r.get("view"), dict):
            SNAPSHOT = {
                k: v
                for k, v in r["view"].items()
                if k
                in (
                    "route",
                    "person",
                    "workflow",
                    "inputs",
                    "language",
                    "theme",
                    "research_feature",
                    "navigation_open",
                )
            }
        return {"event_id": event["event_id"], "status": event["status"]}


def route(handler, payload):
    import command_bus

    if handler == "ping":
        return {"instance": INSTANCE, "name": "DNA Workbench", "gui": GUI}
    if handler == "ui/poll":
        return poll(payload)
    if handler == "ui/ack":
        return ack(payload)
    if handler == "execute":
        if not isinstance(payload, dict) or set(payload) - {
            "command",
            "arguments",
            "request_id",
        }:
            raise command_bus.CommandError(
                "INVALID_REQUEST", "Expected command, arguments, optional request_id"
            )
        return command_bus.execute(
            payload.get("command"),
            payload.get("arguments", {}),
            payload.get("request_id"),
            source="local-control",
        )
    if handler.startswith("commands/"):
        return command_bus.execute(
            handler.removeprefix("commands/"), payload, source="openapi"
        )
    raise command_bus.CommandError("UNKNOWN_ENDPOINT", "Unknown control endpoint")
