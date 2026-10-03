"""Local Discord diagnostics. Queue a test only when explicitly requested."""
import argparse
import json
from modules.alerts import alert_manager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--queue-test', action='store_true',
                        help='Queue one silent test message for the running monitor to deliver.')
    action.add_argument('--reset-delivery', action='store_true',
                        help='Resume delivery after fixing a rejected webhook or channel permission.')
    args = parser.parse_args()
    if args.reset_delivery:
        alert_manager.reset_delivery()
    if args.queue_test:
        if not alert_manager.send_alert('test', 'Discord integration test',
                                       'Network Monitor is connected. This is a manually requested test.'):
            print('Discord is disabled or the webhook is missing/invalid. Check .env locally.')
            return 1
        print('Test queued. Keep monitor.py running; delivery respects batching and cooldowns.')
    print(json.dumps(alert_manager.status(), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
