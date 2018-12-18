import datetime

import lxml.etree
import requests


def make_request(url):
    return requests.get(url, timeout=10)


def extract_title(dom):
    return dom.xpath("//div[@id='sectionHead']/h1/text()")[0]


def extract_date(dom):
    extracted = dom.xpath("//aside[@id='detail']//a[@class='cat-rev']/text()")
    extracted = extracted[0]
    return datetime.datetime.strptime(extracted, '%d %b %Y').date()


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


def extract_resale_active(dom):
    return 'Resale active' in dom.xpath('//input[@id="resaleMessage"]/@value')


def parse(html):
    try:
        dom = lxml.etree.HTML(html)
        title = extract_title(dom)
        date = extract_date(dom)
        resale_active = extract_resale_active(dom)
        tickets = list(extract_tickets(dom))
    except IndexError:
        raise ValueError('Extraction failed')
    return {
        'title': title,
        'date': date,
        'tickets': tickets,
        'resale_active': resale_active
    }


def get_page(url):
    html = make_request(url)
    return parse(html.text)
