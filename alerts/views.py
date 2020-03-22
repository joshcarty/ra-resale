import datetime
from django.utils import timezone
import os

from smtplib import SMTPException

import requests

from django.core import mail
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.urls import reverse

from . import get_page, ResaleInactiveError, ExtractionError, EventExpiredError
from .models import Tracker, Event, Ticket
from .forms import TrackerForm


def index(request):
    if request.method == 'POST':
        form = TrackerForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data['url']
            email = form.cleaned_data['email']

            try:
                add_tracker(url, email)
                return HttpResponseRedirect('/success')

            except requests.exceptions.MissingSchema:
                return failure_redirect('url')

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError):
                return failure_redirect('timeout')

            except EventExpiredError:
                return failure_redirect('date')

            except ResaleInactiveError:
                return failure_redirect('inactive')

            except ExtractionError:
                return failure_redirect('extract')

        else:
            return failure_redirect('form')

    form = TrackerForm(label_suffix='')
    return render(request, 'alerts/index.html', {'form': form})


def add_tracker(url, email):
    page = get_page(url)

    event = update_event(page, url)
    event.save()

    for ticket in update_tickets(page['tickets'], event):
        ticket.save()

    tracker = update_tracker(email, event, sent=False)
    tracker.save()


def failure_redirect(message):
    url = reverse(failure) + f'?message={message}'
    return HttpResponseRedirect(url)


def success(request):
    return render(request, 'alerts/success.html')


def privacy(request):
    return render(request, 'alerts/privacy.html')


def failure(request):
    raw = request.GET.get('message', 'other')
    messages = {
        'other': "Not sure what.",
        'url': "This doesn't look like a valid event page.",
        'form': ("Something in the form wasn't right. Are you sure"
                 " this is a valid email address and event page?"),
        'timeout': "RA took too long to respond. Is the site down?",
        'date': "This event has already happend.",
        'extract': "Could not extract ticket information from RA.",
        'inactive': "Resale is not active for this event."
    }
    message = messages.get(raw, messages['other'])
    return render(request, 'alerts/failure.html', {'message': message})


def app_engine_cron(fn):
    """
    Ensure that view is only accessible by Google App Engine cron job.
    """
    def wraps(request):
        is_gae = os.environ.get('GAE_APPLICATION')
        is_cron = request.META.get('HTTP_X_APPENGINE_CRON')
        if not (is_gae and is_cron):
            raise Http404('Not App Engine cron.')
        return fn(request)
    return wraps


def update(request):
    tracked = Tracker.objects.filter(sent=False).values('event').distinct()
    tracked_events = Event.objects.filter(id__in=tracked)

    for event in tracked_events:
        try:
            page = get_page(event.url)
            for ticket in update_tickets(page['tickets'], event):
                ticket.save()
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError):
                print(f"Error updating {event.title}")
                continue

    return JsonResponse({
        'response': 'success',
        'updated': [
            {'event': event.title, 'url': event.url}
            for event in tracked_events
        ]
    })


def update_tickets(tickets, event):
    for ticket in tickets:
        ticket_obj, _ = Ticket.objects.get_or_create(
            event=event,
            title=ticket['title'],
            price=ticket['price'],
        )
        ticket_obj.available = ticket['available']
        yield ticket_obj


def update_event(page, url):
    event, _ = Event.objects.get_or_create(
        title=page['title'],
        url=url,
        date=page['date'],
        resale_active=page['resale_active']
    )
    
    today = timezone.now().today().date()
    if (event.date - today).days < 0:
        event.delete()
        raise EventExpiredError()

    if event.resale_active is False:
        event.delete()
        raise ResaleInactiveError()

    return event


def update_tracker(email, event, sent):
    tracker, _ = Tracker.objects.get_or_create(
        email=email,
        event=event
    )
    tracker.sent = sent
    return tracker


@app_engine_cron
def send(request):
    tickets = Ticket.objects.filter(available=True)
    events = list(set(ticket.event for ticket in tickets))
    trackers = Tracker.objects.filter(event__in=events, sent=False)

    for tracker in trackers:
        try:
            send_mail(tracker)
            tracker.sent = True
            tracker.save()
        except SMTPException as e:
            print(f"Failed to send email to {tracker.email}.")
            print(e)
            continue

    # reset ticket availability to be updated later
    for ticket in tickets:
        ticket.available = False
        ticket.save()

    return JsonResponse({
        'response': 'success',
        'sent': [
            {'email': tracker.email, 'event': tracker.event.title}
            for tracker in trackers
        ]
    })


def create_email_body(url, title, others):
    people = 'people are'
    if others == 1:
        people = 'person is'
    return (f"Tickets available for <a href='{url}'>{title}</a>. You and "
           f"{others} other {people} subscribed to alerts for this "
           f"event.")


def send_mail(tracker):
    title = tracker.event.title
    url = tracker.event.url
    email = tracker.email
    watching = Tracker.objects.filter(event__url=url).count()
    msg = create_email_body(url, title, others=watching - 1)
    mail.send_mail(
        subject=f"Tickets available for {title}.",
        message=f"Tickets available for {title}.",
        html_message=msg,
        from_email='resale.alerts@gmail.com',
        recipient_list=[email],
        fail_silently=False,
    )
    print(f"Email sent to {email}. Tickets available for {title}.")


@app_engine_cron
def prune(request):
    expiry = datetime.date.today() - datetime.timedelta(days=5)
    expired_events = Event.objects.filter(date__lte=expiry)
    expired_trackers = Tracker.objects.filter(event__in=expired_events)
    for tracker in expired_trackers:
        tracker.delete()
    return JsonResponse({
        'response': 'success',
        'pruned': [
            {'email': tracker.email, 'event': tracker.event.title}
            for tracker in expired_trackers
        ]
    })
