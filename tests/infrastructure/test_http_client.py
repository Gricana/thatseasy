import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import MagicMock

import requests

from bench_download.application.ports import HttpClientError
from bench_download.infrastructure.http_client import RequestsHttpClient


class RequestsHttpClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=requests.Session)
        self.session.headers = {}
        self.client = RequestsHttpClient(
            user_agent="test-agent",
            session=self.session,
        )

    def test_streams_body_uses_timeouts_and_mounts_retry_adapters(self) -> None:
        response = MagicMock()
        response.iter_content.return_value = [b"abc", b"", b"de"]
        self.session.get.return_value.__enter__.return_value = response
        self.client.configure_retries(2)

        downloaded = self.client.download(
            "https://example.test/file",
            connect_timeout=1.0,
            read_timeout=2.0,
        )

        self.assertEqual(downloaded, 5)
        self.session.get.assert_called_once_with(
            "https://example.test/file",
            timeout=(1.0, 2.0),
            stream=True,
        )
        self.assertEqual(self.session.mount.call_count, 2)
        mounted_adapters = [call.args[1] for call in self.session.mount.call_args_list]
        self.assertEqual(mounted_adapters[-1].max_retries.total, 2)
        response.raise_for_status.assert_called_once()

    def test_rejects_empty_response_body(self) -> None:
        response = MagicMock()
        response.iter_content.return_value = [b"", b""]
        self.session.get.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(HttpClientError, "empty"):
            self.client.download(
                "https://example.test/empty",
                connect_timeout=1.0,
                read_timeout=2.0,
            )

    def test_converts_http_status_error_without_exposing_url(self) -> None:
        response = MagicMock()
        response.status_code = 503
        error = requests.HTTPError("failed https://example.test/?token=secret")
        error.response = response
        mocked_response = MagicMock()
        mocked_response.raise_for_status.side_effect = error
        self.session.get.return_value.__enter__.return_value = mocked_response

        with self.assertRaisesRegex(HttpClientError, "HTTP 503") as raised:
            self.client.download(
                "https://example.test/?token=secret",
                connect_timeout=1.0,
                read_timeout=2.0,
            )

        self.assertNotIn("secret", str(raised.exception))

    def test_retries_a_transient_server_error(self) -> None:
        request_count = 0
        body = b"retried"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                nonlocal request_count
                request_count += 1
                if request_count == 1:
                    self.send_response(503)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                del format, args

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with RequestsHttpClient() as client:
                    client.configure_retries(1)
                    downloaded = client.download(
                        f"http://127.0.0.1:{server.server_port}/",
                        connect_timeout=1.0,
                        read_timeout=1.0,
                    )
            finally:
                server.shutdown()
                thread.join()

        self.assertEqual(downloaded, len(body))
        self.assertEqual(request_count, 2)


if __name__ == "__main__":
    unittest.main()
