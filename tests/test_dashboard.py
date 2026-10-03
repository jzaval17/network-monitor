"""Regression tests for dashboard rendering and live refresh."""
import unittest
from unittest.mock import patch
from app import app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_empty_dashboard(self):
        with patch('app.db.get_internet_status', return_value=None), patch('app.db.get_router_status', return_value=None), patch('app.db.get_recent_stats', return_value=[]):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Waiting for data', response.data)
        self.assertIn(b'refreshDashboard', response.data)

    def test_updated_readings_and_escaping(self):
        with patch('app.db.get_internet_status', return_value={'status': 'online', 'response_time': .125}), patch('app.db.get_router_status', return_value={'status': 'online', 'response_time': None}), patch('app.db.get_recent_stats', return_value=[{'cpu_percent': 42, 'memory_percent': 61, 'disk_percent': None}]), patch('app.db.get_events', return_value=[{'timestamp': 'today', 'event_type': 'test', 'message': '<script>alert(1)</script>', 'severity': 'info'}]):
            response = self.client.get('/dashboard/fragment')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'125.0 ms', response.data)
        self.assertIn(b'42%', response.data)
        self.assertIn(b'&lt;script&gt;', response.data)
        self.assertNotIn(b'<script>', response.data)
        self.assertNotIn(b'<!DOCTYPE', response.data)

    def test_failure_returns_error_status(self):
        with patch('app.db.get_internet_status', side_effect=RuntimeError('test failure')):
            self.assertEqual(self.client.get('/dashboard/fragment').status_code, 500)



if __name__ == "__main__":
    unittest.main()
