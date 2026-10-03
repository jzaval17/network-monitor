"""Check real collector entry points with measurements and delivery mocked."""
import unittest
from unittest.mock import Mock, patch

from modules.internet import InternetMonitor
from modules.router import RouterMonitor
from modules.public_ip import PublicIPMonitor
from modules.system_monitor import SystemMonitor
from modules.devices import DeviceDiscovery
from monitor import MonitorScheduler


class AlertWiringTests(unittest.TestCase):
    @patch('modules.internet.alert_manager')
    @patch('modules.internet.db')
    def test_internet_passes_every_sample(self, database, alerts):
        monitor = InternetMonitor()
        with patch.object(monitor, 'check_connectivity', return_value=(False, 0, 'test')):
            monitor.monitor()
            monitor.monitor()
        self.assertEqual(alerts.handle_internet_status_change.call_count, 2)
        alerts.handle_internet_status_change.assert_called_with(False)

    @patch('modules.router.alert_manager')
    @patch('modules.router.db')
    def test_router_passes_every_sample(self, database, alerts):
        monitor = RouterMonitor('192.168.1.1')
        with patch.object(monitor, 'ping_router', return_value=(True, 1)):
            monitor.monitor()
            monitor.monitor()
        self.assertEqual(alerts.handle_router_status_change.call_count, 2)
        alerts.handle_router_status_change.assert_called_with(True, '192.168.1.1')

    @patch('modules.public_ip.alert_manager')
    @patch('modules.public_ip.db')
    def test_public_ip_only_alerts_on_change(self, database, alerts):
        database.get_latest_public_ip.return_value = '203.0.113.1'
        monitor = PublicIPMonitor()
        with patch.object(monitor, 'get_public_ip', side_effect=['203.0.113.1', '203.0.113.2', None]):
            for _ in range(3):
                monitor.monitor()
        alerts.handle_public_ip_change.assert_called_once_with('203.0.113.1', '203.0.113.2')

    @patch('modules.public_ip.requests.get')
    def test_ip_service_error_page_is_not_a_new_ip(self, get):
        invalid = Mock(text='<html>service unavailable</html>')
        invalid.json.return_value = {'ip': 'not an IP'}
        valid = Mock(text='203.0.113.2\n')
        get.side_effect = [invalid, valid]
        self.assertEqual(PublicIPMonitor().get_public_ip(), '203.0.113.2')

    @patch('modules.system_monitor.alert_manager')
    @patch('modules.system_monitor.db')
    def test_system_passes_high_and_normal_samples(self, database, alerts):
        monitor = SystemMonitor()
        with patch.object(monitor, 'get_cpu_stats', side_effect=[90, 20]), \
             patch.object(monitor, 'get_memory_stats', return_value={'percent': 30}), \
             patch.object(monitor, 'get_disk_stats', return_value=10), \
             patch.object(monitor, 'get_network_stats', return_value={}):
            monitor.monitor()
            monitor.monitor()
        self.assertEqual(alerts.observe_resources.call_count, 2)
        alerts.observe_resources.assert_called_with(20, 30)

    @patch('modules.devices.alert_manager')
    @patch('modules.devices.db')
    def test_failed_scan_does_not_disconnect_devices(self, database, alerts):
        monitor = DeviceDiscovery()
        monitor.known_devices = {'192.168.1.2': True}
        with patch.object(monitor, 'scan_network', return_value=None):
            monitor.monitor()
        database.update_device_online_status.assert_not_called()
        alerts.observe_devices.assert_not_called()

    @patch('modules.devices.alert_manager')
    @patch('modules.devices.db')
    def test_successful_scan_reaches_alert_manager(self, database, alerts):
        monitor = DeviceDiscovery()
        devices = [{'ip': '192.168.1.2', 'mac': 'aa:bb:cc:dd:ee:ff'}]
        with patch.object(monitor, 'scan_network', return_value=devices):
            monitor.monitor()
        alerts.observe_devices.assert_called_once_with(devices)

    @patch('modules.devices.subprocess.run', return_value=Mock(returncode=1, stdout=''))
    def test_nonzero_scan_exit_is_failure(self, run):
        monitor = DeviceDiscovery()
        self.assertIsNone(monitor.scan_arp_linux())
        self.assertIsNone(monitor.scan_arp_windows())

    @patch('monitor.signal.signal')
    @patch('monitor.alert_manager')
    @patch('monitor.schedule.run_pending', side_effect=KeyboardInterrupt)
    def test_scheduler_stops_delivery_worker_on_exit(self, pending, alerts, signals):
        monitor = MonitorScheduler()
        with patch.object(monitor, 'setup_schedule'):
            with self.assertRaises(SystemExit):
                monitor.run()
        alerts.start.assert_called_once()
        alerts.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
