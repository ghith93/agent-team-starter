import unittest
from unittest.mock import patch, MagicMock
from agent_team.web_research import _validate_public_url, _validate_egress_proxy, TextExtractor, fetch_public_page


class WebResearchTests(unittest.TestCase):
    def test_rejects_non_http(self):
        with self.assertRaises(ValueError):
            _validate_public_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            _validate_public_url("http://localhost/admin")

    def test_rejects_private_ip_literal(self):
        with self.assertRaises(ValueError):
            _validate_public_url("http://127.0.0.1/")

    def test_rejects_url_credentials(self):
        with self.assertRaises(ValueError):
            _validate_public_url("https://user:pass@example.com")

    def test_rejects_invalid_port(self):
        with self.assertRaisesRegex(ValueError, "port is invalid"):
            _validate_public_url("https://example.com:99999/")

    def test_rejects_single_label_host(self):
        with self.assertRaisesRegex(ValueError, "Single-label"):
            _validate_public_url("http://intranet/")

    def test_rejects_dns_name_resolving_to_private_ip(self):
        private = [(None, None, None, None, ("10.0.0.5", 443))]
        with patch("agent_team.web_research.socket.getaddrinfo", return_value=private):
            with self.assertRaisesRegex(ValueError, "non-public"):
                _validate_public_url("https://example.com/")

    def test_rejects_mixed_public_and_private_dns_answers(self):
        mixed = [
            (None, None, None, None, ("93.184.216.34", 443)),
            (None, None, None, None, ("192.168.1.2", 443)),
        ]
        with patch("agent_team.web_research.socket.getaddrinfo", return_value=mixed):
            with self.assertRaisesRegex(ValueError, "non-public"):
                _validate_public_url("https://example.com/")

    def test_extracts_title_and_text(self):
        p = TextExtractor()
        p.feed("<html><title>Demo page</title><p>Hello world</p><script>secret()</script></html>")
        self.assertEqual(" ".join(p.title_parts), "Demo page")
        self.assertIn("Hello world", " ".join(p.parts))
        self.assertNotIn("secret", " ".join(p.parts))

    def test_fetch_fails_closed_without_trusted_egress_proxy(self):
        with patch.dict("os.environ", {}, clear=True), patch("agent_team.web_research._validate_public_url"), patch("agent_team.web_research.requests.Session") as session_factory:
            with self.assertRaisesRegex(ValueError, "Safe page fetching is disabled"):
                fetch_public_page("https://example.com")
            session_factory.assert_not_called()

    def test_rejects_malformed_egress_proxy(self):
        with patch.dict("os.environ", {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "127.0.0.1:8080"}, clear=True), patch("agent_team.web_research._validate_public_url"), patch("agent_team.web_research.requests.Session") as session_factory:
            with self.assertRaisesRegex(ValueError, "must be an http"):
                fetch_public_page("https://example.com")
            session_factory.assert_not_called()

    def test_proxy_rejects_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "embedded credentials"):
            _validate_egress_proxy("http://user:secret@proxy.example:8080")

    def test_proxy_rejects_invalid_port(self):
        with self.assertRaisesRegex(ValueError, "port is invalid"):
            _validate_egress_proxy("http://proxy.example:99999")

    def test_proxy_rejects_path_query_and_fragment(self):
        for url in ("http://proxy.example/path", "http://proxy.example/?x=1", "http://proxy.example/#frag"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "must not contain"):
                _validate_egress_proxy(url)

    def test_proxy_rejects_control_characters(self):
        with self.assertRaisesRegex(ValueError, "printable URL"):
            _validate_egress_proxy("http://proxy.example:8080\n")

    def test_proxy_allows_localhost_for_explicit_local_proxy(self):
        # Syntax validation is separate from the external proxy trust decision.
        _validate_egress_proxy("http://127.0.0.1:8080")

    def test_ambient_no_proxy_cannot_bypass_trusted_egress_proxy(self):
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "text/plain", "content-length": "5"}
        response.iter_content.return_value = [b"hello"]
        response.url = "https://example.com/"
        response.encoding = "utf-8"
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        session.get.return_value = response
        env = {
            "AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://egress-proxy.invalid:8080",
            "NO_PROXY": "*",
            "no_proxy": "example.com",
            "HTTP_PROXY": "http://ambient-proxy.invalid:3128",
            "HTTPS_PROXY": "http://ambient-proxy.invalid:3128",
            "ALL_PROXY": "http://ambient-proxy.invalid:3128",
        }
        with patch.dict("os.environ", env, clear=True), patch("agent_team.web_research._validate_public_url"), patch("agent_team.web_research.requests.Session", return_value=session):
            page = fetch_public_page("https://example.com/")
        self.assertEqual(page.text, "hello")
        self.assertFalse(session.trust_env)
        self.assertEqual(session.get.call_args.kwargs["proxies"], {
            "http": "http://egress-proxy.invalid:8080",
            "https": "http://egress-proxy.invalid:8080",
        })

    def test_blocks_redirects(self):
        response = MagicMock()
        response.status_code = 302
        response.headers = {"content-type": "text/html", "location": "http://127.0.0.1/"}
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        session.get.return_value = response
        with patch.dict("os.environ", {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://egress-proxy.invalid:8080", "NO_PROXY": "example.com", "HTTPS_PROXY": "http://ambient-proxy.invalid:3128"}, clear=True), patch("agent_team.web_research._validate_public_url"), patch("agent_team.web_research.requests.Session", return_value=session):
            with self.assertRaisesRegex(ValueError, "Redirect blocked"):
                fetch_public_page("https://example.com")
            self.assertFalse(session.trust_env)
            self.assertEqual(session.get.call_args.kwargs["proxies"]["https"], "http://egress-proxy.invalid:8080")

    def test_rejects_oversized_content_length(self):
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "text/html", "content-length": "2000001"}
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        session.get.return_value = response
        with patch.dict("os.environ", {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://egress-proxy.invalid:8080"}, clear=True), patch("agent_team.web_research._validate_public_url"), patch("agent_team.web_research.requests.Session", return_value=session):
            with self.assertRaisesRegex(ValueError, "2 MB limit"):
                fetch_public_page("https://example.com")
            self.assertFalse(session.trust_env)


if __name__ == "__main__":
    unittest.main()
