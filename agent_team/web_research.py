"""Bounded public-web retrieval for an explicitly supplied URL.

This is defense-in-depth, not a hardened browser or complete SSRF defense.
Do not expose it as a public service without network-level egress controls.
"""
from __future__ import annotations
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse
import ipaddress
import socket
import os
import requests


@dataclass
class Page:
    url: str
    status: int
    title: str
    text: str


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.title_parts = []
        self.in_title = False
        # Track ignored elements by tag so a mismatched closing tag cannot
        # expose content from inside script/style/noscript/SVG elements.
        self.skip_stack = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "svg"):
            self.skip_stack.append(tag)
        if tag == "title" and not self.skip_stack:
            self.in_title = True
        if not self.skip_stack and tag in ("p", "div", "li", "h1", "h2", "h3", "br", "article"):
            self.parts.append("\\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "svg") and self.skip_stack and tag == self.skip_stack[-1]:
            self.skip_stack.pop()
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.skip_stack:
            return
        clean = " ".join(data.split())
        if not clean:
            return
        if self.in_title:
            self.title_parts.append(clean)
        else:
            self.parts.append(clean)


def _validate_public_url(url: str) -> None:
    """Reject non-public URL targets before making a request.

    This is defense-in-depth only: DNS can change between validation and the
    HTTP client's connection. Use network-level egress restrictions for hostile
    inputs or public-facing deployments.
    """
    if not isinstance(url, str) or not url or any(ord(ch) < 32 for ch in url):
        raise ValueError("URL must be a non-empty printable string.")
    p = urlparse(url)
    if p.scheme.lower() not in ("http", "https") or not p.hostname:
        raise ValueError("Use a full public http:// or https:// URL.")
    if p.username is not None or p.password is not None:
        raise ValueError("URLs containing credentials are not allowed.")
    try:
        port = p.port
    except ValueError as exc:
        raise ValueError("URL port is invalid.") from exc
    if port is not None and not (1 <= port <= 65535):
        raise ValueError("URL port is invalid.")

    host = p.hostname.rstrip(".").lower()
    if not host or host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test")):
        raise ValueError("Local network addresses are not allowed.")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        # Require a qualified DNS hostname; reject single-label internal names.
        if "." not in host:
            raise ValueError("Single-label hostnames are not allowed.")
        try:
            infos = socket.getaddrinfo(host, port or (443 if p.scheme.lower() == "https" else 80), type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("Could not resolve public hostname.") from exc
        if not infos:
            raise ValueError("Hostname did not resolve to an address.")
        for info in infos:
            try:
                addr = ipaddress.ip_address(info[4][0].split("%", 1)[0])
            except ValueError as exc:
                raise ValueError("Hostname resolved to an invalid address.") from exc
            if not addr.is_global:
                raise ValueError("Private or non-public network targets are not allowed.")
    else:
        if not literal.is_global:
            raise ValueError("Private or non-public network targets are not allowed.")


def _validate_egress_proxy(proxy_url: str) -> None:
    """Validate proxy URL syntax without claiming that the proxy is trustworthy.

    Local proxy hosts are intentionally permitted: a trusted egress proxy may
    run on the same machine. The operator must still verify destination-IP
    enforcement outside this process.
    """
    if not isinstance(proxy_url, str) or not proxy_url or any(ord(ch) < 32 for ch in proxy_url):
        raise ValueError("Trusted egress proxy URL must be a non-empty printable URL.")
    parsed = urlparse(proxy_url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise ValueError("Trusted egress proxy must be an http:// or https:// URL with a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Trusted egress proxy URL must not contain embedded credentials.")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Trusted egress proxy URL must not contain a path, query, or fragment.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Trusted egress proxy port is invalid.") from exc
    if port is not None and not (1 <= port <= 65535):
        raise ValueError("Trusted egress proxy port is invalid.")


def fetch_public_page(url: str, max_chars: int = 12000, timeout: int = 12) -> Page:
    if not (1 <= max_chars <= 20000):
        raise ValueError("max_chars must be between 1 and 20000.")
    if not (1 <= timeout <= 30):
        raise ValueError("timeout must be between 1 and 30 seconds.")
    _validate_public_url(url)
    # Fail closed unless an administrator explicitly configures a trusted egress
    # proxy that enforces destination-IP policy at connection time. Merely setting
    # a generic proxy is not enough; the proxy must block private, loopback,
    # link-local, reserved and metadata-service destinations after DNS resolution.
    egress_proxy = os.environ.get("AGENT_TEAM_TRUSTED_EGRESS_PROXY", "").strip()
    if not egress_proxy:
        raise ValueError(
            "Safe page fetching is disabled: configure AGENT_TEAM_TRUSTED_EGRESS_PROXY "
            "to a trusted egress proxy that enforces public-destination IP policy."
        )
    _validate_egress_proxy(egress_proxy)
    headers = {"User-Agent": "AgentTeamStarter/0.3 (public-page-research)"}
    proxies = {"http": egress_proxy, "https": egress_proxy}
    try:
        # Do not inherit ambient HTTP(S)_PROXY / ALL_PROXY / NO_PROXY settings.
        # In particular, NO_PROXY must not silently bypass the explicitly trusted
        # egress proxy. Configure the proxy here, and verify its network policy
        # independently. Disabling trust_env also avoids implicit netrc auth.
        with requests.Session() as session:
            session.trust_env = False
            with session.get(
                url, headers=headers, proxies=proxies, timeout=(4, timeout), allow_redirects=False, stream=True
            ) as response:
                if 300 <= response.status_code < 400:
                    raise ValueError("Redirect blocked; inspect the destination URL before requesting it.")
                response.raise_for_status()
                ctype = response.headers.get("content-type", "").lower()
                if not ("text/html" in ctype or "text/plain" in ctype):
                    raise ValueError(f"Unsupported content type: {ctype or 'unknown'}")
                declared_size = response.headers.get("content-length")
                if declared_size:
                    try:
                        if int(declared_size) > 2_000_000:
                            raise ValueError("Page response is larger than the 2 MB limit.")
                    except ValueError as exc:
                        if "larger than" in str(exc):
                            raise
                chunks, total = [], 0
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > 2_000_000:
                        raise ValueError("Page response is larger than the 2 MB limit.")
                    chunks.append(chunk)
                body = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                content = body.decode(encoding, errors="replace")
                final_url, status = response.url, response.status_code
    except requests.RequestException as exc:
        raise ValueError(f"Public page request failed: {type(exc).__name__}") from exc

    if "text/plain" in ctype:
        text = content
        title = urlparse(final_url).netloc
    else:
        parser = TextExtractor()
        parser.feed(content)
        title = " ".join(parser.title_parts).strip() or urlparse(final_url).netloc
        text = " ".join(" ".join(parser.parts).split())
    return Page(url=final_url, status=status, title=title, text=text[:max_chars])



class SearchResultExtractor(HTMLParser):
    """Extract result titles and hrefs from the DuckDuckGo HTML results page."""

    def __init__(self):
        super().__init__()
        self.results = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        href = attrs.get("href", "")
        if "result__a" in classes and href:
            self.current = {"href": href, "title_parts": []}

    def handle_data(self, data):
        if self.current is not None:
            clean = " ".join(data.split())
            if clean:
                self.current["title_parts"].append(clean)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current is not None:
            title = " ".join(self.current["title_parts"]).strip()
            if title:
                self.results.append({"title": title, "href": self.current["href"]})
            self.current = None


def search_public_web(query: str, max_results: int = 5, timeout: int = 12) -> list[dict]:
    """Search public web results through an explicitly configured trusted egress proxy.

    This intentionally uses a fixed search host, blocks redirects, caps the response,
    and validates every extracted destination. It is not a replacement for proxy-level
    destination-IP enforcement or a full browser sandbox.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise ValueError("Search query must contain 1-300 characters.")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 8:
        raise ValueError("max_results must be an integer from 1 to 8.")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 30:
        raise ValueError("timeout must be an integer from 1 to 30 seconds.")
    egress_proxy = os.environ.get("AGENT_TEAM_TRUSTED_EGRESS_PROXY", "").strip()
    if not egress_proxy:
        raise ValueError(
            "Public web search is disabled: configure AGENT_TEAM_TRUSTED_EGRESS_PROXY "
            "to a trusted egress proxy that enforces public-destination IP policy."
        )
    _validate_egress_proxy(egress_proxy)
    endpoint = "https://html.duckduckgo.com/html/"
    proxies = {"http": egress_proxy, "https": egress_proxy}
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.get(
                endpoint, params={"q": query.strip()}, headers={"User-Agent": "AgentTeamStarter/0.3"},
                proxies=proxies, timeout=(4, timeout), allow_redirects=False, stream=True,
            ) as response:
                if 300 <= response.status_code < 400:
                    raise ValueError("Search redirect blocked.")
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    raise ValueError("Search provider returned unsupported content.")
                declared_size = response.headers.get("content-length")
                if declared_size:
                    try:
                        if int(declared_size) > 2_000_000:
                            raise ValueError("Search response exceeds the 2 MB limit.")
                    except ValueError as exc:
                        if "exceeds" in str(exc):
                            raise
                chunks, total = [], 0
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > 2_000_000:
                        raise ValueError("Search response exceeds the 2 MB limit.")
                    chunks.append(chunk)
                body = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
    except requests.RequestException as exc:
        raise ValueError(f"Public web search failed ({type(exc).__name__}).") from exc

    parser = SearchResultExtractor()
    parser.feed(body)
    results, seen = [], set()
    for item in parser.results:
        href = urljoin(endpoint, item["href"])
        parsed = urlparse(href)
        destination = href
        if parsed.hostname and parsed.hostname.lower() in {"duckduckgo.com", "www.duckduckgo.com"} and parsed.path.startswith("/l/"):
            destination = parse_qs(parsed.query).get("uddg", [""])[0]
        if not destination or destination in seen:
            continue
        try:
            _validate_public_url(destination)
        except ValueError:
            continue
        seen.add(destination)
        results.append({"title": item["title"][:300], "url": destination})
        if len(results) >= max_results:
            break
    return results
