import pytest

from backend.logic.push_subscriptions import db, send_push_notification, store_push_subscription
from backend.schemas.notification import NotificationBanner


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._SUBSCRIPTIONS.clear()
    yield
    db._SUBSCRIPTIONS.clear()


def test_store_push_subscription_persists_the_raw_subscription_json():
    subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "keys": {"p256dh": "fake-p256dh-key", "auth": "fake-auth-secret"},
    }

    store_push_subscription("student-1", subscription)

    stored = db.get_subscription("student-1")
    assert stored == subscription


def test_store_push_subscription_overwrites_prior_subscription_for_same_student():
    store_push_subscription("student-1", {"endpoint": "https://old-endpoint"})
    store_push_subscription("student-1", {"endpoint": "https://new-endpoint"})

    stored = db.get_subscription("student-1")
    assert stored["endpoint"] == "https://new-endpoint"


def test_unknown_student_has_no_subscription():
    assert db.get_subscription("never-subscribed") is None


def test_send_push_notification_does_not_crash_on_valid_pair():
    subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "keys": {"p256dh": "fake-p256dh-key", "auth": "fake-auth-secret"},
    }
    banner = NotificationBanner(type="streak-at-risk", message="Your streak is at risk!", priority=1)

    result = send_push_notification(subscription, banner)

    assert result is True


def test_send_push_notification_handles_missing_endpoint_gracefully():
    banner = NotificationBanner(type="reminder", message="Assignment due tomorrow", priority=3)

    result = send_push_notification({}, banner)

    assert result is True
