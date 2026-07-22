"""VAPID Subscription Storage + push-send stub (PRD §5, §20 — stretch scope).

store_push_subscription() persists the raw browser PushSubscription JSON
(endpoint + keys) that Thaariha's frontend will POST after the VAPID
subscribe flow. Subhiksha's DB isn't live yet, so storage is an
in-memory _StubDB, same pattern as prior phases.

send_push_notification() is a LOGGING STUB, not a real pywebpush/web-push
call: an actual send needs real VAPID keys (not yet generated or
provisioned) and a live browser-registered subscription endpoint
(Thaariha's frontend half isn't built yet), so a real call here would
have nothing valid to send to — and could reach out to an arbitrary
external push service unexpectedly. Swap this for a real
pywebpush.webpush() call once both of those exist.
"""

from typing import Any

from pydantic import BaseModel

from backend.schemas.notification import NotificationBanner


class PushSubscriptionRecord(BaseModel):
    student_id: str
    subscription: dict[str, Any]


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (push_subscriptions table)."""

    def __init__(self) -> None:
        self._SUBSCRIPTIONS: dict[str, dict[str, Any]] = {}

    def insert(self, record: PushSubscriptionRecord) -> None:
        self._SUBSCRIPTIONS[record.student_id] = record.subscription

    def get_subscription(self, student_id: str) -> dict[str, Any] | None:
        return self._SUBSCRIPTIONS.get(student_id)


db = _StubDB()


def store_push_subscription(student_id: str, subscription: dict[str, Any]) -> None:
    db.insert(PushSubscriptionRecord(student_id=student_id, subscription=subscription))


def send_push_notification(subscription: dict[str, Any], banner: NotificationBanner) -> bool:
    """Logging stub — see module docstring for why this isn't a real pywebpush call yet."""
    endpoint = subscription.get("endpoint", "<unknown endpoint>")
    print(f"[push-stub] would send to {endpoint}: [{banner.type}] {banner.message}")
    return True
