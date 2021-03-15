import datetime
import re

import lxml.etree
import requests

EVENT_ID_PATTERN = re.compile(r"https?:\/\/(?:www\.)?ra.co\/events\/(\d+)")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
)


def make_request(url):
    headers = {'User-Agent': USER_AGENT}
    return requests.get(url, timeout=10, headers=headers)


def extract_event_id(url):
    return EVENT_ID_PATTERN.search(url)[1]


def extract_title(dom):
    return dom.xpath('//h1//text()')[0]


def extract_date(dom):
    extracted = dom.xpath("//span[text() = 'Date']/../..//a//text()")
    extracted = extracted[0].strip()
    extracted = extracted.rsplit(', ', maxsplit=1)[-1]
    return datetime.datetime.strptime(extracted, '%d %b %Y').date()


def extract_tickets(dom):
    tickets = dom.xpath("//li[@id='ticket-types']/ul/li")
    for ticket in tickets:
        yield {
            'title': extract_ticket_title(ticket),
            'price': extract_price(ticket),
            'available': extract_availability(ticket)
        }


def extract_ticket_title(element):
    path = [
        './/div[@class="pr8"]/text()',
        './/div[@class="type-title"]/text()'
    ]
    return element.xpath('|'.join(path))[0]


def extract_price(element):
    return element.xpath('.//div[@class="type-price"]/text()')[0]


def extract_availability(element):
    mapping = {'closed': False, 'onsale but': True}
    availability = element.xpath('./@class')[0]
    return mapping.get(availability, False)


def extract_resale_active(dom):
    path = '//span[text() = "resale queue is active"]//text()'
    return any(dom.xpath(path))


def parse_tickets(html):
    try:
        dom = lxml.etree.HTML(html)
        tickets = list(extract_tickets(dom))
    except IndexError:
        raise ExtractionError()
    return tickets


def parse_event(html):
    try:
        dom = lxml.etree.HTML(html)
        title = extract_title(dom)
        date = extract_date(dom)
        resale_active = extract_resale_active(dom)
    except IndexError:
        raise ExtractionError()
    return {
        'title': title,
        'date': date,
        'resale_active': resale_active,
        'tickets': []
    }


def get_tickets(url):
    event_id = extract_event_id(url)
    ticket_url = f"https://ra.co/widget/event/{event_id}/embedtickets"
    html = make_request(ticket_url)
    return parse_tickets(html.text)


def get_event(url):
    html = make_request(url)
    return parse_event(html.text)


def get_page(url):
    event = get_event(url)
    if event['resale_active']:
        tickets = get_tickets(url)
        event['tickets'] = tickets
    return event


class ExtractionError(Exception):
    pass


class ResaleInactiveError(ExtractionError):
    pass


class EventExpiredError(ExtractionError):
    pass
