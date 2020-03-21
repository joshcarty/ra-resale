from datetime import date

from django.core import mail
from django.test import TestCase

from .models import Tracker, Event
from .views import send_mail


class EmailTest(TestCase):
    test_event_url = 'https://www.residentadvisor.net/events/1234567'
    test_event_title = 'Resident Advisor Event'

    def test_send_email(self):
        # Create test event
        e = Event(url=self.test_event_url,
                  title=self.test_event_title,
                  date=date.today())
        e.save()

        # Create test tracker.
        t = Tracker(email=f'example@example.com', event=e, sent=False)
        t.save()

        # Create other trackers.
        others = 2
        for i in range(others):
            Tracker(email=f'example{i}@example.com', event=e, sent=False).save()
        send_mail(t)

        # Test that the email is sent.
        self.assertEqual(len(mail.outbox), 1)

        # Test that the body template is correctly filled.
        body = ("Tickets available for <a href='https://www.residentadvisor"
                ".net/events/1234567'>Resident Advisor Event</a>. You "
                f"and {others} other people are subscribed to alerts for this "
                "event.")
        self.assertEqual(mail.outbox[0].alternatives[0][0], body)



