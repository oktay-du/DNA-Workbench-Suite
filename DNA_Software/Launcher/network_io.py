"""Separate verified public HTTPS downloads from explicitly local HTTP services."""

import ipaddress
import http.client
import socket
import urllib.parse
import urllib.request


def validate_https(url):
    if not isinstance(url, str) or any(ord(char) < 32 for char in url):
        raise ValueError("Invalid download URL")
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Downloads require public HTTPS without URL credentials")
    public_addresses(parsed.hostname)
    return url


def public_addresses(host):
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(
        not ipaddress.ip_address(item[4][0].split("%")[0]).is_global
        for item in addresses
    ):
        raise ValueError(
            "Public downloads cannot access local or private network addresses"
        )
    return list(dict.fromkeys(item[4][0] for item in addresses))


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        addresses = public_addresses(self.host)

        def connect_address(
            target, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None
        ):
            error = None
            for address in addresses:
                try:
                    return socket.create_connection(
                        (address, target[1]), timeout, source_address
                    )
                except OSError as current:
                    error = current
            raise error or OSError("No public address is reachable")

        # Pin TCP to checked IPs; TLS still verifies the original DNS hostname.
        self._create_connection = connect_address
        return super().connect()


class PublicHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(PublicHTTPSConnection, request, context=self._context)


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        validate_https(newurl)
        return super().redirect_request(request, fp, code, message, headers, newurl)


class NoLocalRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise ValueError("Local service redirects are not accepted")


def open_https(request, *, timeout=60):
    url = request.full_url if isinstance(request, urllib.request.Request) else request
    validate_https(url)
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), PublicHTTPSHandler(), PublicRedirects()
    ).open(request, timeout=timeout)


def open_loopback(request, *, timeout=60):
    url = request.full_url if isinstance(request, urllib.request.Request) else request
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "::1")
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is None
    ):
        raise ValueError(
            "Local services require literal loopback HTTP with an explicit port"
        )
    # Loopback control traffic must never be routed through an environment proxy.
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoLocalRedirects()
    ).open(request, timeout=timeout)
