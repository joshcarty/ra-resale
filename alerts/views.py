import datetime

from smtplib import SMTPException

import requests

from django.core import mail
from django.http import HttpResponseRedirect, JsonResponse
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
        'form': "Something in the form isn't right.",
        'timeout': "RA took too long to respond. Is the site down?",
        'date': "This event has already happend.",
        'extract': "Could not extract ticket information from RA.",
        'inactive': "Resale is not active for this event."
    }
    message = messages.get(raw, messages['other'])
    return render(request, 'alerts/failure.html', {'message': message})


def update(request):
    tracked = Tracker.objects.values('event').distinct()
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

    today = datetime.date.today()
    if (event.date - today).days < 0:
        raise EventExpiredError()

    if event.resale_active is False:
        raise ResaleInactiveError()

    return event


def update_tracker(email, event, sent):
    tracker, _ = Tracker.objects.get_or_create(
        email=email,
        event=event,
        sent=sent
    )
    return tracker


def send(request):
    tickets = Ticket.objects.filter(available=True)
    events = list(set(ticket.event for ticket in tickets))
    trackers = Tracker.objects.filter(event__in=events, sent=False)

    for tracker in trackers:
        try:
            send_mail(tracker.email, tracker.event.title)
            tracker.sent = True
            tracker.save()
        except SMTPException as e:
            print(f"Failed to send email to {tracker.email}.")
            print(e)
            continue

    return JsonResponse({
        'response': 'success',
        'sent': [
            {'email': tracker.email, 'event': tracker.event.title}
            for tracker in trackers
        ]
    })


def send_mail(recipient, title):
    mail.send_mail(
        f"Tickets available for {title}.",
        f"Tickets available for {title}.",
        'resale.alerts@gmail.com',
        [recipient],
        fail_silently=False,
    )
    print(f"Email sent to {recipient}. Tickets available for {title}.")


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
