import unittest
from http.client import RemoteDisconnected
from urllib.error import URLError

from city_twin_pipeline.osm import post_overpass_query


class Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class OSMFetchTests(unittest.TestCase):
    def test_post_overpass_query_retries_transient_url_errors(self):
        calls = []

        def opener(_req, timeout):
            calls.append(timeout)
            if len(calls) == 1:
                raise URLError("temporary tls eof")
            return Response(b'{"elements": []}')

        result = post_overpass_query(
            endpoint="https://overpass-api.de/api/interpreter",
            query="[out:json];node(0,0,0,0);out;",
            timeout_seconds=3,
            opener=opener,
            retries=1,
        )

        self.assertEqual(result, {"elements": []})
        self.assertEqual(calls, [3, 3])

    def test_post_overpass_query_retries_remote_disconnects(self):
        calls = []

        def opener(_req, timeout):
            calls.append(timeout)
            if len(calls) == 1:
                raise RemoteDisconnected("remote closed")
            return Response(b'{"elements": []}')

        result = post_overpass_query(
            endpoint="http://overpass-api.de/api/interpreter",
            query="[out:json];node(0,0,0,0);out;",
            timeout_seconds=3,
            opener=opener,
            retries=1,
        )

        self.assertEqual(result, {"elements": []})
        self.assertEqual(calls, [3, 3])


if __name__ == "__main__":
    unittest.main()
