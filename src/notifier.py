# notifier.py - sends messages to a Discord channel through a webhook
try:
    import requests
except ImportError:
    import urequests as requests

_webhook = None


def setup(webhook_url):
    global _webhook
    _webhook = webhook_url or None


def send(message):
    print("[notify]", message)
    if not _webhook:
        return False
    try:
        r = requests.post(_webhook, json={"content": message})
        ok = r.status_code in (200, 204)
        r.close()
        return ok
    except Exception as e:
        print("[notify] error:", e)
        return False
