import datetime

import requests
import lxml.etree

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from .models import Tracker, Event, Ticket
from .forms import TrackerForm


def make_request(url):
    return requests.get(url)


def extract_title(dom):
    return dom.xpath("//div[@id='sectionHead']/h1/text()")[0]


def extract_date(dom):
    extracted = dom.xpath("//aside[@id='detail']//a[@class='cat-rev']")[0]
    return datetime.date.today()


def extract_tickets(dom):
    tickets = dom.xpath("//li[@id='tickets']/ul/li")
    for ticket in tickets:
        yield {
            'title': extract_ticket_title(ticket),
            'price': extract_price(ticket),
            'available': extract_availability(ticket)
        }


def extract_ticket_title(element):
    return element.xpath('.//p/span/following-sibling::text()')[0]


def extract_price(element):
    return element.xpath('.//p/span/text()')[0]


def extract_availability(element):
    mapping = {'closed': False, 'onsale but': True}
    availability = element.xpath('./@class')[0]
    return mapping.get(availability, False)


def parse(html):
    dom = lxml.etree.HTML(html)
    title = extract_title(dom)
    date = extract_date(dom)
    tickets = extract_tickets(dom)
    return {
        'title': title,
        'date': date,
        'tickets': list(tickets)
    }


def update(request):
    tracked = Tracker.objects.values('event').distinct()
    tracked = Event.objects.filter(id__in=tracked)
    for t in tracked:
        availability = make_request(t.url)
        availability = parse(availability.text)
        t.available = availability
        t.save()
    return HttpResponse('Success')


def add_tracker(url, email):
    page = make_request(url)
    parsed = parse(page.text)

    event, _ = Event.objects.get_or_create(
        title=parsed['title'],
        url=url,
        date=parsed['date']
    )
    event.save()
    for t in parsed['tickets']:
        ticket, _ = Ticket.objects.get_or_create(
            event=event,
            title=t['title'],
            price=t['price'],
        )
        ticket.available = t['available']
        ticket.save()

    tracker, _ = Tracker.objects.get_or_create(
        email=email,
        event=event
    )
    tracker.save()


def send_mail(email, title):
    print(f"Email sent to {email}. Tickets available for {title}.")


def send(request):
    tickets = Ticket.objects.filter(available=True)
    events = list(set(ticket.event for ticket in tickets))
    trackers = Tracker.objects.filter(event__in=events, sent=False)

    for tracker in trackers:
        send_mail(tracker.email, tracker.event.title)
        tracker.sent = True
        tracker.save()

    return HttpResponse('Success')


def index(request):
    if request.method == 'POST':
        form = TrackerForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data['url']
            email = form.cleaned_data['email']
            add_tracker(url, email)
            return HttpResponseRedirect('/success')
        return HttpResponse('ERROR: Form not valid.')

    form = TrackerForm(label_suffix='')
    return render(request, 'alerts/index.html', {'form': form})


def success(request):
    return render(request, 'alerts/success.html')