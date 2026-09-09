import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

import server


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / "test.db"
        cls.db_patch = patch.object(server, "DB_PATH", cls.db)
        cls.db_patch.start()
        server.init_db()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.db_patch.stop(); cls.tmp.cleanup()

    def request(self, method, path, body=None):
        conn = HTTPConnection("127.0.0.1", self.port)
        payload = json.dumps(body).encode() if body is not None else None
        conn.request(method, path, payload, {"Content-Type": "application/json"})
        res = conn.getresponse(); data = json.loads(res.read())
        return res.status, data

    def test_dashboard_has_stats(self):
        status, data = self.request("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertGreater(data["stats"]["books"], 0)

    def test_minidb_api_exposes_plan_catalog_and_pages(self):
        status,data=self.request("POST","/api/minidb/inspect",{"sql":"SELECT name FROM student ORDER BY age DESC;"})
        self.assertEqual(status,200);self.assertIn("Sort",data["result"][0]["plan_after"])
        self.assertEqual(data["result"][0]["semantic"],"passed")
        self.assertIn("catalog",data["system"]);self.assertGreaterEqual(len(data["system"]["allocated_pages"]),2)

    def test_create_book(self):
        status, data = self.request("POST", "/api/books", {"isbn":"TEST-001","title":"测试书","author":"测试者","total_copies":2})
        self.assertEqual(status, 201)
        self.assertIn("id", data)

    def test_borrow_and_return_updates_inventory(self):
        _, books = self.request("GET", "/api/books?q=" + quote("活着"))
        _, readers = self.request("GET", "/api/readers?q=" + quote("张雨桐"))
        before = books[0]["available_copies"]
        status, loan = self.request("POST", "/api/loans", {"book_id":books[0]["id"],"reader_id":readers[0]["id"],"days":7})
        self.assertEqual(status, 201)
        _, after_borrow = self.request("GET", "/api/books?q=" + quote("活着"))
        self.assertEqual(after_borrow[0]["available_copies"], before - 1)
        status, _ = self.request("PUT", f"/api/loans/{loan['id']}/return", {})
        self.assertEqual(status, 200)
        _, after_return = self.request("GET", "/api/books?q=" + quote("活着"))
        self.assertEqual(after_return[0]["available_copies"], before)


if __name__ == "__main__": unittest.main()
