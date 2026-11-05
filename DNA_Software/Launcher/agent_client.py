"""Connect to the existing local suite, without proxies, redirects or tokens in output."""

from pathlib import Path
import http.client, urllib.parse
import portable_json as json

ROOT = Path(__file__).resolve().parents[2]


class ClientError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class Client:
    def __init__(self, path=None, timeout=180):
        self.path = (
            Path(path) if path else ROOT / "DNA_Software/UserData/Launcher/control.json"
        )
        self.timeout = timeout
        try:
            self.config = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ClientError(
                "APP_NOT_RUNNING", "Start DNA_Launcher.exe or run DNA.cmd serve first."
            )
        url = urllib.parse.urlsplit(self.config.get("url", ""))
        if (
            url.scheme != "http"
            or url.hostname != "127.0.0.1"
            or url.username
            or url.password
            or url.path not in ("", "/")
            or url.query
            or url.fragment
        ):
            raise ClientError(
                "INVALID_CONTROL_FILE",
                "Control endpoint must be an unredirected loopback HTTP address.",
            )
        try:
            self.port = url.port
        except ValueError:
            raise ClientError("INVALID_CONTROL_FILE", "Invalid port")
        if not self.port or not isinstance(self.config.get("token"), str):
            raise ClientError("INVALID_CONTROL_FILE", "Invalid local session metadata")
        info = self.post("/agent/ping", {})
        if info.get("instance") != self.config.get("instance"):
            raise ClientError(
                "STALE_SESSION", "The control file belongs to an older app instance."
            )

    def post(self, path, value):
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.port, timeout=self.timeout
        )
        try:
            body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode(
                "utf-8"
            )
            connection.request(
                "POST",
                path,
                body,
                {
                    "Content-Type": "application/json",
                    "X-DNA-Token": self.config["token"],
                },
            )
            response = connection.getresponse()
            raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ClientError(
                    "RESPONSE_TOO_LARGE", "Local response exceeded 16 MiB"
                )
            if 300 <= response.status < 400:
                raise ClientError(
                    "REDIRECT_REFUSED", "Local control never follows redirects"
                )
            result = json.loads(raw.decode("utf-8"))
            if response.status != 200 or result.get("error"):
                raise ClientError(
                    result.get("code", "COMMAND_FAILED"),
                    str(result.get("error", response.reason)),
                )
            return result
        except (OSError, http.client.HTTPException) as error:
            raise ClientError(
                "APP_NOT_RUNNING", "Local suite is unavailable; restart the app."
            ) from error
        finally:
            connection.close()

    def call(self, command, arguments=None, request_id=None):
        payload = {"command": command, "arguments": arguments or {}}
        if request_id:
            payload["request_id"] = request_id
        return self.post("/agent/execute", payload)
