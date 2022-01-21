#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import re
import requests as requests
from bs4 import BeautifulSoup as bs

BASE_URL = "https://www.hacico.de/en/Cigars"

# field names
fields = [
    'title',
    'type',
    'price',
    'in_stock',
    'image',
    'size',
    'length',
    'diameter',
    'url',
    'country',
]
skip_sizes = [
    'Cigarillo',
    'cigarillos',
    'Mini',
    'Puros',
    'Purito',
    'Puritos',
    'Minutos',
    'Panatella',
    'Panatela',
    'Panetela',
    'Panetelas',
    'Coronita',
    'Short',
    'Shorts',
    'Petit Royales',
    'Senoritas',
]

def main():
    countries = parse_page(BASE_URL, '.meineListe > div > a')

    for country in countries:
        categories = parse_page(country['href'], '.list_left > div > a')

        for category in categories:
            parse_items_on_page(country['title'], category['href'])

            # check if category has multiple pages and parse all
            next_pages = get_next_pages(category['href'])
            for page_url in next_pages:
                parse_items_on_page(country['title'], page_url)


def parse_cigar_page_info(country_title, href):
    req = requests.get(href)
    soup = bs(req.content, 'html.parser')
    cigar_info = soup.select_one('.product_info_box')

    if not cigar_info:
        return False

    photo = cigar_info.select('.product_info_box_middle_left img')
    title_h1 = cigar_info.select('.product_info_box_middle_left h1')
    listings = soup.findAll('tr', {'class': 'tableListingI'})

    extra_info = cigar_info.select('.product_info_box_middle_right > div > div')
    length = re.findall("(?<=Länge in cm: ).*?(?=<br/>)", str(extra_info))
    diameter = re.findall("(?<=Durchmesser in cm: ).*?(?=<br/>)", str(extra_info))
    size = re.findall("(?<=Fabrikformat: ).*?(?=<br/>)", str(extra_info))

    length_inch = number_format(length[0]) / 2.54 if length else 0
    diameter_inch = number_format(diameter[0]) / 2.54 if diameter else 0

    for listing in listings:
        row = listing.select('td')
        cigar_price = number_format(row[6].select('b')[0].text.replace('EUR', ''))
        cigar_name = str(title_h1[0].text)
        cigar_type = str(row[3].text)
        buy_button = row[10].select('input')
        is_in_skipped = [ele for ele in skip_sizes if (ele in cigar_name)]

        if bool(is_in_skipped):
            continue

        if len(buy_button) > 0:
            writer.writerow({
                "title": cigar_name,
                "type": cigar_type,  # single / box 5 / box 10
                "price": cigar_price,
                "in_stock": len(buy_button) > 0,
                "image": 'https://www.hacico.de/' + str(photo[0]['src']),
                "size": size if size else '',
                "length": round(length_inch, 2),
                "diameter": round(diameter_inch, 2),
                "url": href,
                "country": country_title,
            })
            print(cigar_name + ' ' + cigar_type + ' parsed.')


def parse_items_on_page(country_title, cigar_url):
    cigar_links = parse_page(cigar_url, '.product_listing_box_name a')
    for cigar in cigar_links:
        try:
            parse_cigar_page_info(country_title, cigar['href'])
        except:
            continue


def get_next_pages(cigar_url):
    pages = []
    next_pages = parse_page(cigar_url, '.centerbox .pageResults')
    for page in next_pages:
        if page['title'] != ' next page ':
            pages.append(page['href'])

    return pages


def parse_page(url, selector, href=True):
    req = requests.get(url)
    soup = bs(req.content, 'html.parser')
    return soup.select(selector, href=href)


def number_format(price):
    # reset price format
    price = price.replace('.', ',')
    # check if it's x,xx or x,xxx.xx
    parts = price.split(",")
    if len(parts) == 2:
        price = price.replace(',', '.')
    if len(parts) == 3:
        price = price.replace(',', '', 1)
        price = price.replace(',', '.')

    return float(price.strip())


if __name__ == '__main__':
    # writing to csv file
    with open("hacico.csv", 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        # writing headers (field names)
        writer.writeheader()

        main()
