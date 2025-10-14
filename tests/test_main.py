'''
 Copyright 2025 Akamai Technologies, Inc.
 
 Licensed under the Apache License, Version 2.0 (the
 "License"); you may not use this file except in
 compliance with the License.  You may obtain a copy
 of the License at

  https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in
writing, software distributed under the License is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing
permissions and limitations under the License.
'''
 
import sys
import os
# Ensure app directory is in sys.path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

class TestMainEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("LKE DBaaS Access List Sync Service", response.text)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("app.main.manager")
    def test_force_next_update(self, mock_manager):
        mock_manager.clear_cache = AsyncMock(return_value=None)
        response = self.client.get("/force-next-update")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], "true")

if __name__ == "__main__":
    unittest.main()
