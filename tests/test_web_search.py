import os
import unittest
from unittest.mock import patch

from agent_team.web_research import SearchResultExtractor, search_public_web


class FakeResponse:
    status_code = 200
    headers = {"content-type": "text/html; charset=utf-8", "content-length": "500"}
    encoding = "utf-8"

    def __init__(self, body, status=200):
        self.body = body
        self.status_code = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def iter_content(self, chunk_size=65536):
        yield self.body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.trust_env = True
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


class WebSearchTests(unittest.TestCase):
    def test_search_parser_extracts_result_titles_and_links(self):
        parser = SearchResultExtractor()
        parser.feed('<a class="result__a" href="https://example.com/a"><b>Example</b> page</a>')
        self.assertEqual(parser.results, [{"title": "Example page", "href": "https://example.com/a"}])

    def test_search_fails_closed_without_trusted_proxy(self):
        with patch.dict(os.environ, {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": ""}):
            with self.assertRaisesRegex(ValueError, "Public web search is disabled"):
                search_public_web("test query")

    def test_search_validates_limits_before_network_access(self):
        with patch.dict(os.environ, {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://proxy.example:8080"}):
            with self.assertRaises(ValueError):
                search_public_web("x" * 301)
            with self.assertRaises(ValueError):
                search_public_web("query", max_results=9)

    def test_search_uses_proxy_and_validates_extracted_destinations(self):
        body = (
            '<a class="result__a" href="https://example.com/a">Example A</a>'
            '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fb">Example B</a>'
        ).encode()
        session = FakeSession(FakeResponse(body))
        with patch.dict(os.environ, {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://proxy.example:8080"}):
            with patch("agent_team.web_research.requests.Session", return_value=session):
                with patch("agent_team.web_research._validate_public_url") as validate:
                    results = search_public_web("test query", max_results=2)
        self.assertEqual(results, [
            {"title": "Example A", "url": "https://example.com/a"},
            {"title": "Example B", "url": "https://example.org/b"},
        ])
        self.assertFalse(session.trust_env)
        self.assertEqual(session.calls[0][1]["allow_redirects"], False)
        self.assertEqual(session.calls[0][1]["proxies"]["https"], "http://proxy.example:8080")
        self.assertEqual(validate.call_count, 2)

    def test_search_blocks_redirects(self):
        session = FakeSession(FakeResponse(b"", status=302))
        with patch.dict(os.environ, {"AGENT_TEAM_TRUSTED_EGRESS_PROXY": "http://proxy.example:8080"}):
            with patch("agent_team.web_research.requests.Session", return_value=session):
                with self.assertRaisesRegex(ValueError, "redirect blocked"):
                    search_public_web("query")


if __name__ == "__main__":
    unittest.main()
