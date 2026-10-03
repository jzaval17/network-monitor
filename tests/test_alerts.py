"""Discord regression tests: temporary databases, fake time, no real HTTP."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import requests
from database.db import DatabaseManager
from modules.alerts import AlertManager


class DiscordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = DatabaseManager(str(Path(self.temp.name) / 'alerts.db'))
        self.now = 1800000000.0
        self.settings = SimpleNamespace(
            DISCORD_ENABLED=True, DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/123/test-token',
            ALERT_COOLDOWN=300, DISCORD_CONFIRM_CHECKS=2, DISCORD_RESOURCE_CHECKS=3,
            DISCORD_RESOURCE_COOLDOWN=1800, DISCORD_MIN_INTERVAL=300,
            DISCORD_BATCH_SECONDS=20, DISCORD_MAX_AGE_SECONDS=86400,
            DISCORD_SILENT=True, DISCORD_DEVICE_ALERTS=True,
            DISCORD_DEVICE_DISCONNECT_ALERTS=False, MONITOR_INTERVAL=60,
            CPU_THRESHOLD=80, MEMORY_THRESHOLD=85,
        )
        self.post = Mock(return_value=self.response(200))
        self.manager = self.new_manager()

    @staticmethod
    def response(code, data=None, headers=None):
        result = Mock(status_code=code, headers=headers or {})
        result.json.return_value = data or {}
        return result

    def new_manager(self):
        return AlertManager(database=self.db, settings=self.settings,
                            clock=lambda: self.now, post=self.post)

    def state(self):
        row = self.db.execute_query('SELECT payload FROM discord_delivery_state WHERE id=1', fetch_one=True)
        return json.loads(row[0]) if row else {}

    def tick(self, seconds=60):
        self.now += seconds

    def outage(self):
        self.manager.handle_internet_status_change(False)
        self.tick()
        self.manager.handle_internet_status_change(False)

    def test_disabled_makes_no_requests_or_state(self):
        self.manager.enabled = False
        self.manager.handle_internet_status_change(False)
        self.manager.send_alert('x', 'x', 'x')
        self.assertFalse(self.manager.flush())
        self.assertFalse(self.state())
        self.post.assert_not_called()

    def test_invalid_webhooks_are_disabled(self):
        for url in ('http://discord.com/api/webhooks/123/token', 'https://example.com/api/webhooks/123/token',
                    'https://discord.com.evil.test/api/webhooks/123/token', 'https://user@discord.com/api/webhooks/123/token'):
            with self.subTest(url=url):
                self.settings.DISCORD_WEBHOOK_URL = url
                self.assertFalse(self.new_manager().enabled)

    def test_healthy_startup_and_one_failure_are_quiet(self):
        for online in (True, False, True, True):
            self.manager.handle_internet_status_change(online)
            self.tick()
        self.assertEqual(self.state()['pending'], {})

    def test_confirmed_outage_only_queues_once(self):
        self.outage()
        self.assertEqual(len(self.state()['pending']), 1)
        version = self.state()['pending']['internet']['version']
        for _ in range(20):
            self.tick()
            self.manager.handle_internet_status_change(False)
        self.assertEqual(self.state()['pending']['internet']['version'], version)
        self.post.assert_not_called()

    def test_confirmation_survives_restart(self):
        self.manager.handle_internet_status_change(False)
        self.tick()
        self.manager = self.new_manager()
        self.manager.handle_internet_status_change(False)
        self.assertIn('internet', self.state()['pending'])

    def test_long_gap_breaks_confirmation(self):
        self.manager.handle_internet_status_change(False)
        self.tick(1000)
        self.manager.handle_internet_status_change(False)
        self.assertEqual(self.state()['pending'], {})

    def test_recovery_replaces_undelivered_outage(self):
        self.outage()
        self.manager.handle_internet_status_change(True)
        self.tick()
        self.manager.handle_internet_status_change(True)
        pending = self.state()['pending']
        self.assertEqual(list(pending), ['internet'])
        self.assertIn('restored', pending['internet']['title'])
        self.assertIn('2m 0s', pending['internet']['message'])

    def test_router_and_internet_share_digest(self):
        for _ in range(2):
            self.manager.handle_internet_status_change(False)
            self.manager.handle_router_status_change(False, '192.168.1.1')
            self.tick()
        self.assertTrue(self.manager.flush())
        self.post.assert_called_once()
        description = self.post.call_args.kwargs['json']['embeds'][0]['description']
        self.assertIn('Internet', description)
        self.assertIn('Router', description)

    def test_resource_spikes_do_not_notify(self):
        for value in (90, 90, 20, 90, 20):
            self.manager.observe_resources(value, 20)
            self.tick()
        self.assertEqual(self.state()['pending'], {})

    def test_sustained_resource_warning_and_hysteresis(self):
        for _ in range(3):
            self.manager.observe_resources(90, 90)
            self.tick()
        self.assertEqual(set(self.state()['pending']), {'cpu', 'memory'})
        for _ in range(3):
            self.manager.observe_resources(79, 84)
            self.tick()
        self.assertTrue(self.state()['observations']['cpu']['active'])
        for _ in range(3):
            self.manager.observe_resources(60, 60)
            self.tick()
        self.assertEqual(self.state()['pending'], {})

    def test_initial_device_inventory_restart_and_dhcp_are_quiet(self):
        self.manager.observe_devices([])
        self.manager.observe_devices([{'ip': '192.168.1.2', 'mac': 'AA:BB:CC:DD:EE:FF'}])
        self.manager = self.new_manager()
        self.manager.observe_devices([{'ip': '192.168.1.9', 'mac': 'aa-bb-cc-dd-ee-ff'}])
        self.assertEqual(self.state()['pending'], {})

    def test_new_devices_are_grouped(self):
        self.manager.observe_devices([{'ip': '1', 'mac': 'a'}])
        self.manager.observe_devices([{'ip': '1', 'mac': 'a'}, {'ip': '2', 'mac': 'b'}, {'ip': '3', 'mac': 'c'}])
        self.tick()
        self.manager.flush()
        self.post.assert_called_once()
        self.assertIn('2 (b)', self.post.call_args.kwargs['json']['embeds'][0]['description'])
        self.assertIn('3 (c)', self.post.call_args.kwargs['json']['embeds'][0]['description'])

    def test_disconnections_off_by_default(self):
        self.manager.observe_devices([{'ip': '1', 'mac': 'a'}])
        for _ in range(10):
            self.manager.observe_devices([])
        self.assertEqual(self.state()['pending'], {})

    def test_optional_disconnect_confirmation_and_return(self):
        self.settings.DISCORD_DEVICE_DISCONNECT_ALERTS = True
        self.manager.observe_devices([{'ip': '1', 'mac': 'a'}])
        self.manager.observe_devices([])
        self.assertEqual(self.state()['pending'], {})
        self.manager.observe_devices([])
        self.assertEqual(len(self.state()['pending']), 1)
        self.manager.observe_devices([{'ip': '1', 'mac': 'a'}])
        self.assertEqual(self.state()['pending'], {})

    def test_batch_delay_and_global_spacing(self):
        self.manager.send_alert('a', 'A', 'A')
        self.assertFalse(self.manager.flush())
        self.tick()
        self.assertTrue(self.manager.flush())
        self.manager.send_alert('b', 'B', 'B')
        self.tick()
        self.assertFalse(self.manager.flush())
        self.tick(240)
        self.assertTrue(self.manager.flush())
        self.assertEqual(self.post.call_count, 2)

    def test_payload_disables_mentions_and_push_and_requests_confirmation(self):
        self.manager.send_alert('a', '@everyone', '<@123>')
        self.tick()
        self.manager.flush()
        call = self.post.call_args
        self.assertIn('wait=true', call.args[0])
        self.assertEqual(call.kwargs['json']['allowed_mentions'], {'parse': []})
        self.assertEqual(call.kwargs['json']['flags'], 4096)
        self.assertFalse(call.kwargs['allow_redirects'])

    def test_204_is_success_too(self):
        self.post.return_value = self.response(204)
        self.manager.send_alert('a', 'A', 'A')
        self.tick()
        self.assertTrue(self.manager.flush())
        self.assertEqual(self.state()['pending'], {})

    def test_rate_limit_survives_restart(self):
        self.post.return_value = self.response(429, {'retry_after': 120.5})
        self.manager.send_alert('a', 'A', 'A')
        self.tick()
        self.assertFalse(self.manager.flush())
        self.manager = self.new_manager()
        self.tick(120)
        self.assertFalse(self.manager.flush())
        self.assertEqual(self.post.call_count, 1)
        self.tick(1)
        self.post.return_value = self.response(200)
        self.assertTrue(self.manager.flush())

    def test_transport_failure_keeps_queue_and_hides_token(self):
        self.post.side_effect = requests.ConnectionError(self.settings.DISCORD_WEBHOOK_URL)
        self.manager.send_alert('a', 'A', 'A')
        self.tick()
        with self.assertLogs('modules.alerts', level='WARNING') as logs:
            self.assertFalse(self.manager.flush())
        self.assertNotIn('test-token', str(logs.output))
        self.assertEqual(len(self.state()['pending']), 1)
        self.assertEqual(self.state()['next_attempt'], self.now + 30)
        self.manager = self.new_manager()
        self.tick(30)
        self.manager.flush()
        self.assertEqual(self.state()['next_attempt'], self.now + 60)

    def test_permanent_error_pauses_until_reset(self):
        self.post.return_value = self.response(404)
        self.manager.send_alert('a', 'A', 'A')
        self.tick()
        self.manager.flush()
        self.manager = self.new_manager()
        self.tick(3600)
        self.manager.flush()
        self.assertEqual(self.post.call_count, 1)
        self.assertTrue(self.manager.status()['blocked'])
        self.manager.reset_delivery()
        self.post.return_value = self.response(200)
        self.assertTrue(self.manager.flush())

    def test_old_queue_expires(self):
        self.manager.send_alert('a', 'A', 'A')
        self.tick(86401)
        self.assertFalse(self.manager.flush())
        self.assertEqual(self.state()['pending'], {})

    def test_queue_is_bounded_for_device_burst(self):
        self.manager.observe_devices([{'ip': '0', 'mac': '0'}])
        self.manager.observe_devices([{'ip': str(i), 'mac': str(i)} for i in range(200)])
        self.assertLessEqual(len(self.state()['pending']), 100)
        self.tick()
        self.manager.flush()
        self.assertEqual(self.state()['pending'], {})
        self.post.assert_called_once()
        self.assertIn('100 new', self.post.call_args.kwargs['json']['embeds'][0]['description'])

    def test_resource_cooldown_delays_next_episode(self):
        for _ in range(3):
            self.manager.observe_resources(90, 20)
            self.tick()
        self.assertTrue(self.manager.flush())
        sent_at = self.now
        for value in [20] * 3 + [90] * 3:
            self.manager.observe_resources(value, 20)
            self.tick()
        self.assertFalse(self.manager.flush())
        self.assertEqual(self.state()['pending']['cpu']['due'], sent_at + 1800)

    def test_http_500_retries_without_blocking(self):
        self.post.return_value = self.response(500)
        self.manager.send_alert('a', 'A', 'A')
        self.tick()
        self.assertFalse(self.manager.flush())
        self.assertFalse(self.manager.status()['blocked'])
        self.tick(30)
        self.post.return_value = self.response(200)
        self.assertTrue(self.manager.flush())

    def test_rate_limit_header_fallback_and_malformed_body(self):
        response = self.response(429, headers={'Retry-After': '90'})
        self.assertEqual(self.manager._retry_seconds(response), 90)
        response.json.side_effect = ValueError('not JSON')
        self.assertEqual(self.manager._retry_seconds(response), 90)

    def test_update_during_send_is_not_lost(self):
        self.manager.send_alert('a', 'Old', 'Old')
        def post(*args, **kwargs):
            self.manager.send_alert('a', 'New', 'New')
            return self.response(200)
        self.manager.post = post
        self.tick()
        self.manager.flush()
        self.assertEqual(self.state()['pending']['a']['message'], 'New')

    def test_status_never_exposes_webhook(self):
        self.assertNotIn('test-token', json.dumps(self.manager.status()))

    def test_changing_webhook_does_not_replay_old_channel_queue(self):
        self.manager.send_alert('a', 'A', 'A')
        self.settings.DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/456/new-token'
        self.manager = self.new_manager()
        self.tick()
        self.assertFalse(self.manager.flush())
        self.assertEqual(self.state()['pending'], {})


if __name__ == '__main__':
    unittest.main()
