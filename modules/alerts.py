"""Durable, coalesced Discord notifications. No HTTP requests during collection."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import re
import threading
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import requests
from config import config
from database.db import db

logger = logging.getLogger(__name__)


class AlertManager:
    """One delivery worker per monitor process; SQLite state survives restarts."""

    def __init__(self, webhook_url=None, cooldown_seconds=None, database=None,
                 settings=None, clock=None, post=None):
        self.settings = settings or config
        self.db = database or db
        self.clock = clock or time.time
        self.post = post or requests.post
        self.webhook_url = (webhook_url if webhook_url is not None else self.settings.DISCORD_WEBHOOK_URL).strip()
        self.enabled = self.settings.DISCORD_ENABLED and bool(self.webhook_url)
        self.cooldown = max(0, cooldown_seconds if cooldown_seconds is not None else self.settings.ALERT_COOLDOWN)
        self._lock = threading.RLock()
        self._delivery_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._fingerprint = hashlib.sha256(self.webhook_url.encode()).hexdigest()
        if self.enabled and not self._valid_url():
            logger.error('Discord disabled: configure a valid HTTPS Discord webhook URL.')
            self.enabled = False

    def _valid_url(self):
        try:
            url = urlsplit(self.webhook_url)
            return (url.scheme == 'https' and url.hostname in
                    {'discord.com', 'discordapp.com', 'canary.discord.com', 'ptb.discord.com'}
                    and not url.username and not url.password and url.port in (None, 443)
                    and not url.fragment
                    and re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[\w-]+', url.path) is not None)
        except ValueError:
            return False

    @contextmanager
    def _state(self):
        with self._lock, self.db.get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT payload FROM discord_delivery_state WHERE id = 1').fetchone()
            state = json.loads(row[0]) if row else {}
            if state.get('webhook') != self._fingerprint:
                state = {'webhook': self._fingerprint}
            for key in ('observations', 'pending', 'sent'):
                state.setdefault(key, {})
            try:
                yield state
                encoded = json.dumps(state)
                if not row or row[0] != encoded:
                    conn.execute('INSERT INTO discord_delivery_state (id, payload) VALUES (1, ?) '
                                 'ON CONFLICT(id) DO UPDATE SET payload = excluded.payload', (encoded,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _queue(self, state, key, title, message, severity='info', cooldown=None):
        now = self.clock()
        delay = self.cooldown if cooldown is None else cooldown
        prior = state['pending'].get(key)
        due = prior['due'] if prior else now + self.settings.DISCORD_BATCH_SECONDS
        due = max(due, state['sent'].get(key, 0) + delay)
        state['pending'][key] = {
            'key': key, 'title': title[:180], 'message': message[:700],
            'severity': severity, 'due': due, 'updated': now,
            'version': (prior['version'] + 1) if prior else 1,
        }
        if len(state['pending']) > 100:
            oldest = min((k for k in state['pending'] if k.startswith('device:')),
                         key=lambda k: state['pending'][k]['updated'], default=None)
            if oldest:
                del state['pending'][oldest]

    def send_alert(self, alert_type, title, message, severity='info'):
        """Queue an alert. True means queued, not yet delivered."""
        if not self.enabled:
            return False
        with self._state() as state:
            self._queue(state, alert_type, title, message, severity)
        return True

    def _observe(self, state, key, bad, label, checks, detail='', recovery=True):
        now = self.clock()
        item = state['observations'].setdefault(key, {'active': False, 'count': 0})
        if now - item.get('sample_at', now) > max(180, self.settings.MONITOR_INTERVAL * 3):
            item['count'] = 0
        item['sample_at'] = now
        if bad == item['active']:
            item['count'] = 0
            return
        item['count'] += 1
        if item['count'] == 1:
            item['candidate_since'] = now
        if item['count'] < checks:
            return
        item['count'] = 0
        item['active'] = bad
        if bad:
            item['since'] = item['candidate_since']
            self._queue(state, key, label + (' unavailable' if recovery else ' warning'),
                        detail or f'{label} failed {checks} consecutive checks.',
                        'critical' if recovery else 'warning',
                        None if recovery else self.settings.DISCORD_RESOURCE_COOLDOWN)
        elif recovery:
            duration = max(0, int(now - item.get('since', now)))
            self._queue(state, key, label + ' restored',
                        f'{label} is back. Observed outage lasted about {duration // 60}m {duration % 60}s. '
                        'This summary replaces any undelivered outage notice.')
        else:
            state['pending'].pop(key, None)

    def handle_internet_status_change(self, is_online):
        """Receive every actual connectivity sample, not just transitions."""
        self._network_sample('internet', is_online, 'Internet')

    def handle_router_status_change(self, is_online, router_ip=None):
        self._network_sample('router', is_online, f'Router ({router_ip})')

    def _network_sample(self, key, online, label):
        if self.enabled:
            with self._state() as state:
                self._observe(state, key, not online, label, self.settings.DISCORD_CONFIRM_CHECKS)

    def observe_resources(self, cpu_percent, memory_percent):
        if not self.enabled:
            return
        with self._state() as state:
            for key, label, value, threshold in (
                ('cpu', 'CPU', cpu_percent, self.settings.CPU_THRESHOLD),
                ('memory', 'Memory', memory_percent, self.settings.MEMORY_THRESHOLD),
            ):
                if value is None or not math.isfinite(value):
                    continue
                active = state['observations'].get(key, {}).get('active', False)
                bad = value > (threshold - 5 if active else threshold)
                self._observe(state, key, bad, label, self.settings.DISCORD_RESOURCE_CHECKS,
                              f'{label} remains high at {value:.1f}% (threshold {threshold}%).', False)

    def handle_public_ip_change(self, old_ip, new_ip):
        self.send_alert('public_ip', 'Public IP changed', f'{old_ip} -> {new_ip}', 'warning')

    def observe_devices(self, devices):
        """Successful scans only. MAC identity prevents DHCP changes appearing as new devices."""
        if not self.enabled:
            return
        current = {d['mac'].lower().replace('-', ':'): d['ip'] for d in devices
                   if d.get('ip') and d.get('mac')}
        with self._state() as state:
            if 'devices' not in state:
                if current:
                    state['devices'] = {mac: {'ip': ip, 'misses': 0} for mac, ip in current.items()}
                return
            known = state['devices']
            for mac, ip in current.items():
                if mac not in known and self.settings.DISCORD_DEVICE_ALERTS:
                    self._queue(state, 'device:' + mac, 'New device', f'{ip} ({mac})')
                elif mac in known and known[mac].get('misses', 0):
                    pending = state['pending'].get('device:' + mac)
                    if pending and pending['title'] == 'Device disconnected':
                        state['pending'].pop('device:' + mac)
                known[mac] = {'ip': ip, 'misses': 0}
            for mac in known.keys() - current.keys():
                item = known[mac]
                item['misses'] = min(item.get('misses', 0) + 1, self.settings.DISCORD_CONFIRM_CHECKS + 1)
                if item['misses'] == self.settings.DISCORD_CONFIRM_CHECKS and self.settings.DISCORD_DEVICE_DISCONNECT_ALERTS:
                    self._queue(state, 'device:' + mac, 'Device disconnected',
                                f"{item['ip']} ({mac}) absent from {item['misses']} successful scans.", 'warning')

    def _delivery_url(self):
        url = urlsplit(self.webhook_url)
        query = dict(parse_qsl(url.query))
        query['wait'] = 'true'
        return urlunsplit(url._replace(query=urlencode(query)))

    @staticmethod
    def _retry_seconds(response):
        try:
            body = response.json()
        except ValueError:
            body = {}
        try:
            value = body.get('retry_after', response.headers.get('Retry-After', 60))
            value = float(value)
            return max(1, value) if math.isfinite(value) else 60
        except (ValueError, TypeError, AttributeError):
            return 60

    def flush(self):
        """Send at most one digest; retries are scheduled, never slept through."""
        if not self.enabled or not self._delivery_lock.acquire(blocking=False):
            return False
        try:
            return self._flush()
        finally:
            self._delivery_lock.release()

    def _flush(self):
        now = self.clock()
        with self._state() as state:
            state['pending'] = {k: v for k, v in state['pending'].items()
                                if now - v['updated'] < self.settings.DISCORD_MAX_AGE_SECONDS}
            state['sent'] = {k: v for k, v in state['sent'].items()
                            if now - v < max(self.cooldown, self.settings.DISCORD_RESOURCE_COOLDOWN, 86400)}
            if state.get('blocked') or now < state.get('next_attempt', 0):
                return False
            eligible = sorted((v for v in state['pending'].values() if v['due'] <= now),
                              key=lambda v: (v['severity'] != 'critical', v['updated']))
            # A large device burst is one summary, not a backlog of tiny digests.
            devices = [v for v in eligible if v['key'].startswith('device:')]
            pending = [v for v in eligible if not v['key'].startswith('device:')][:3 if devices else 4]
            pending += devices
        if not pending:
            return False
        lines = []
        for item in pending:
            if item['key'].startswith('device:'):
                continue
            stamp = datetime.fromtimestamp(item['updated'], timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
            lines.append(f"**{item['title']}** ({stamp})\n{item['message']}")
        if devices:
            new_count = sum(v['title'] == 'New device' for v in devices)
            examples = '; '.join(v['message'][:60] for v in devices[:6])
            lines.append(f'**Device changes**\n{new_count} new; {len(devices) - new_count} disconnected. '
                         f'{examples}' + ('; see the Devices page for the full list.' if len(devices) > 6 else ''))
        payload = {
            'allowed_mentions': {'parse': []}, 'tts': False,
            'flags': 4096 if self.settings.DISCORD_SILENT else 0,
            'embeds': [{'title': 'Network Monitor', 'description': '\n\n'.join(lines)[:4096],
                        'color': 0xc0392b if any(v['severity'] == 'critical' for v in pending) else 0x3498db,
                        'footer': {'text': 'Grouped alerts - no repeated ongoing warnings'}}],
        }
        response = None
        try:
            response = self.post(self._delivery_url(), json=payload, timeout=(3, 5), allow_redirects=False)
            success = response.status_code in (200, 204)
        except requests.RequestException:
            # Exceptions may contain the secret webhook URL. Do not log their text.
            success = False
        with self._state() as state:
            if success:
                for item in pending:
                    current = state['pending'].get(item['key'])
                    if current == item:
                        state['pending'].pop(item['key'], None)
                    elif current:
                        current['due'] = max(current['due'], now + self.cooldown)
                    state['sent'][item['key']] = now
                state['failures'] = 0
                state['next_attempt'] = now + self.settings.DISCORD_MIN_INTERVAL
                state['last_success'] = now
                state['last_error'] = None
                logger.info('Discord digest delivered (%s updates).', len(pending))
            elif response is not None and response.status_code == 429:
                state['next_attempt'] = now + self._retry_seconds(response)
                state['last_error'] = 'Rate limited; waiting before retry.'
            elif response is not None and 300 <= response.status_code < 500:
                state['blocked'] = True
                state['last_error'] = f'Discord rejected delivery (HTTP {response.status_code}); fix webhook/configuration and reset delivery.'
                logger.error('%s', state['last_error'])
            else:
                state['failures'] = min(state.get('failures', 0) + 1, 7)
                state['next_attempt'] = now + min(30 * 2 ** (state['failures'] - 1), 1800)
                state['last_error'] = 'Discord unreachable; alerts queued for retry.'
                if state['failures'] == 1:
                    logger.warning('%s', state['last_error'])
        return success

    def status(self):
        """Local diagnostics; no webhook token or network requests."""
        if not self.enabled:
            return {'enabled': False, 'configured': bool(self.webhook_url)}
        with self._state() as state:
            return {'enabled': True, 'pending': len(state['pending']),
                    'blocked': state.get('blocked', False), 'last_error': state.get('last_error'),
                    'last_success': state.get('last_success'), 'next_attempt': state.get('next_attempt'),
                    'silent': self.settings.DISCORD_SILENT}

    def reset_delivery(self):
        with self._state() as state:
            state.pop('blocked', None)
            state.pop('last_error', None)
            state['next_attempt'] = 0
            state['failures'] = 0

    def start(self):
        if not self.enabled or (self._thread and self._thread.is_alive()):
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name='discord-delivery', daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                self.flush()
            except Exception:
                logger.error('Discord delivery worker error; retrying on the next tick.')
            self._stop.wait(5)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)


alert_manager = AlertManager()
