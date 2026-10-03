"""Integration tests for Flask application."""

import unittest
import json
from app import app
from config import TestingConfig


class FlaskTestCase(unittest.TestCase):
    """Test Flask application."""

    def setUp(self):
        """Set up test client."""
        app.config.from_object(TestingConfig)
        self.client = app.test_client()

    def test_dashboard_loads(self):
        """Test dashboard page loads."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_devices_page_loads(self):
        """Test devices page loads."""
        response = self.client.get("/devices")
        self.assertEqual(response.status_code, 200)

    def test_events_page_loads(self):
        """Test events page loads."""
        response = self.client.get("/events")
        self.assertEqual(response.status_code, 200)

    def test_stats_page_loads(self):
        """Test statistics page loads."""
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)

    def test_api_status_endpoint(self):
        """Test API status endpoint."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("internet", data)
        self.assertIn("router", data)

    def test_api_devices_endpoint(self):
        """Test API devices endpoint."""
        response = self.client.get("/api/devices")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("devices", data)
        self.assertIn("count", data)

    def test_api_events_endpoint(self):
        """Test API events endpoint."""
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("events", data)
        self.assertIn("count", data)

    def test_api_stats_endpoint(self):
        """Test API statistics endpoint."""
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("stats", data)
        self.assertIn("count", data)

    def test_404_not_found(self):
        """Test 404 error handling."""
        response = self.client.get("/nonexistent")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
