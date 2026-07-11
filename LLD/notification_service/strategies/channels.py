"""Demo-grade channels — they 'print and succeed'. Real impls would call
SendGrid / Twilio / FCM and translate transport errors into bool/throw."""
from __future__ import annotations

from interfaces.notification_channel import INotificationChannel
from models.notification             import Notification
from models.subscription             import Channel

class EmailChannel(INotificationChannel):
    @property
    def kind(self) -> Channel: return Channel.EMAIL
    
    def send(self, address: str, n: Notification) -> bool:
        print(f"[EMAIL -> {address}] : {n.body}")
        return True

class SmsChannel(INotificationChannel):
    @property
    def kind(self) -> Channel: return Channel.SMS
    
    def send(self, address: str, n: Notification) -> bool:
        print(f"[SMS   -> {address}] : {n.body}")
        return True

class PushChannel(INotificationChannel):
    @property
    def kind(self) -> Channel: return Channel.PUSH

    def send(self, address: str, n: Notification) -> bool:
        print(f"[PUSH  -> {address}] : {n.body}")
        return True
