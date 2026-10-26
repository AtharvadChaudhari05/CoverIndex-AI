from __future__ import annotations

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from policy_rag import server as server_module
from policy_rag.models import QueryResult, QueryRoute
from policy_rag.rate_limit import RateLimiter, resolve_client_ip


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class RateLimiterTests(unittest.TestCase):
    def test_allows_twenty_then_blocks(self) -> None:
        limiter = RateLimiter(limit=20, window_seconds=86400, clock=FakeClock())
        results = [limiter.consume("1.2.3.4") for _ in range(20)]
        self.assertTrue(all(allowed for allowed, _, _ in results))
        self.assertEqual(results[-1][1], 0)
        allowed, remaining, retry_after = limiter.consume("1.2.3.4")
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(retry_after, 0)

    def test_window_slides(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(limit=2, window_seconds=60, clock=clock)
        limiter.consume("ip")
        clock.now += 30
        limiter.consume("ip")
        self.assertFalse(limiter.consume("ip")[0])
        clock.now += 31  # the first request is now older than the window
        self.assertTrue(limiter.consume("ip")[0])

    def test_clients_are_counted_separately(self) -> None:
        limiter = RateLimiter(limit=1, window_seconds=60, clock=FakeClock())
        self.assertTrue(limiter.consume("a")[0])
        self.assertTrue(limiter.consume("b")[0])
        self.assertFalse(limiter.consume("a")[0])

    def test_remaining_does_not_consume(self) -> None:
        limiter = RateLimiter(limit=3, window_seconds=60, clock=FakeClock())
        limiter.consume("ip")
        self.assertEqual(limiter.remaining("ip"), 2)
        self.assertEqual(limiter.remaining("ip"), 2)

    def test_retry_after_reports_reset_time(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
        self.assertEqual(limiter.retry_after("ip"), 0)
        limiter.consume("ip")
        clock.now += 20
        self.assertEqual(limiter.retry_after("ip"), 41)

    def test_zero_limit_disables(self) -> None:
        limiter = RateLimiter(limit=0, window_seconds=60, clock=FakeClock())
        self.assertTrue(all(limiter.consume("ip")[0] for _ in range(100)))


class ClientIpTests(unittest.TestCase):
    def test_proxy_headers_are_ignored_by_default(self) -> None:
        with patch.dict(os.environ, {"PROXY_SHARED_SECRET": "", "TRUST_X_FORWARDED_FOR": ""}):
            ip = resolve_client_ip("10.0.0.1", {"X-Forwarded-For": "6.6.6.6", "X-Client-IP": "7.7.7.7"})
        self.assertEqual(ip, "10.0.0.1")

    def test_worker_header_needs_the_right_secret(self) -> None:
        with patch.dict(os.environ, {"PROXY_SHARED_SECRET": "s3cret"}):
            trusted = resolve_client_ip("10.0.0.1", {"X-Proxy-Secret": "s3cret", "X-Client-IP": "8.8.8.8"})
            spoofed = resolve_client_ip("10.0.0.1", {"X-Proxy-Secret": "guess", "X-Client-IP": "8.8.8.8"})
        self.assertEqual(trusted, "8.8.8.8")
        self.assertEqual(spoofed, "10.0.0.1")

    def test_forwarded_for_uses_the_entry_added_by_the_proxy(self) -> None:
        # A client can prepend fake entries; the proxy appends the address it actually saw
        with patch.dict(os.environ, {"PROXY_SHARED_SECRET": "", "TRUST_X_FORWARDED_FOR": "true"}):
            ip = resolve_client_ip("10.0.0.1", {"X-Forwarded-For": "1.1.1.1, 9.9.9.9"})
        self.assertEqual(ip, "9.9.9.9")


class EndpointLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.PolicyLensHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.patches = [
            patch.object(server_module, "REQUEST_LIMITER", RateLimiter(limit=2, window_seconds=86400)),
            patch.object(server_module, "ensure_index", return_value=None),
            patch.object(server_module, "rewrite_query_with_history", side_effect=lambda q, h: q),
            patch.object(
                server_module,
                "answer_query",
                return_value=QueryResult(answer="ok", confidence=0.9, route=QueryRoute(None, None, "general", ""), sources=[], trace=[]),
            ),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.server.shutdown()
        self.server.server_close()

    def _ask(self, payload: dict) -> tuple[int, dict, dict]:
        request = urllib.request.Request(
            f"{self.base}/api/ask", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read()), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read()), dict(error.headers)

    def test_third_question_gets_429(self) -> None:
        question = {"query": "What is the waiting period in my HDFC policy?", "session_id": "limit"}
        first = self._ask(question)
        second = self._ask(question)
        third = self._ask(question)
        self.assertEqual((first[0], first[1]["requests_remaining"]), (200, 1))
        self.assertEqual((second[0], second[1]["requests_remaining"]), (200, 0))
        self.assertEqual(third[0], 429)
        self.assertIn("Retry-After", third[2])
        self.assertIn("2 requests", third[1]["error"])

    def test_invalid_requests_do_not_count(self) -> None:
        self._ask({"query": ""})
        self._ask({"query": "hi", "answer_language": "xx"})
        status, body, _ = self._ask({"query": "What is the waiting period in my HDFC policy?"})
        self.assertEqual(status, 200)
        self.assertEqual(body["requests_remaining"], 1)

    def test_status_reports_remaining_without_counting(self) -> None:
        self._ask({"query": "What is the waiting period in my HDFC policy?"})
        index = type("Index", (), {"source_path": None, "records": [], "document_count": 0, "signature": "x"})()
        with patch.object(server_module, "ensure_index", return_value=index):
            for _ in range(3):
                with urllib.request.urlopen(f"{self.base}/api/status") as response:
                    status = json.loads(response.read())
        self.assertEqual((status["requests_remaining"], status["request_limit"]), (1, 2))

    def test_upload_counts_toward_the_limit(self) -> None:
        self._ask({"query": "What is the waiting period in my HDFC policy?"})
        self._ask({"query": "What is the waiting period in my HDFC policy?"})
        request = urllib.request.Request(
            f"{self.base}/api/upload", data=b"--x--", headers={"Content-Type": "multipart/form-data; boundary=x"}
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 429)


if __name__ == "__main__":
    unittest.main()
