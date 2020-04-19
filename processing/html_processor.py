"""
file: html_processor.py
brief: processes the raw html files
author: S. V. Paulauskas
date: April 17, 2020
"""
from csv import DictWriter
from os import listdir
from re import compile

from bs4 import BeautifulSoup

DEBUG = False

DATA_DIR = "../data/html/"
TEST_FILES = [
    "jewelrytelevision.html",
    "alanjamesjewelersllc.html",
    "robertshapiro.html",
    "monalisafinejewelsinc.html",
    "neallitmancompany.html",
    "dallasprincecompany.html",
    "sheahanstephensapphires.html"
]

CSV_HEADER = ['company', 'address_line_1', "address_line_2", 'city', 'state', 'postal_code',
              'country', 'last_name', 'first_name', 'email', 'phone', 'phone_extension',
              'fax', 'url', 'gemstones']

URL_PATTERN = compile('http[s]?://[w]{0,3}[.]?\w+(.\w+){0,10}')
PHONE_PATTERN = compile('((\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4})')
EXTENSION_PATTERN = compile('(ext.) (\d{1,10})')
# From: https://emailregex.com/
EMAIL_PATTERN = compile('[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}')
ADDRESS_STATE_LINE_PATTERN = compile("([\w\s]+), ([\w\s]+)  (\d+)")
CONTACT_PATTERN = compile("Contact: ([a-zA-Z][0-9a-zA-Z .,'-]*)")


def process_address_line(input_line, info):
    line = [line for line in input_line.replace("\xa0", ' ').split("\n") if line]
    if len(line) == 3:
        info['address_line_1'] = line[0].strip(", ")

        if ADDRESS_STATE_LINE_PATTERN.search(line[1]):
            city, state, zcode = ADDRESS_STATE_LINE_PATTERN.findall(line[1])[0]
            info['city'] = city
            info['state'] = state
            info['postal_code'] = zcode

        info['country'] = line[2]


def process_phone_numbers(line, info):
    nums = PHONE_PATTERN.findall(line)
    info['phone'] = nums[0][0]
    if len(nums) == 2:
        info['fax'] = nums[1][0]
    if EXTENSION_PATTERN.search(line):
        info['phone_extension'] = EXTENSION_PATTERN.findall(line)[0][1]


def process_contact_info(raw_soup):
    info = {}
    for line in [tag.text for tag in raw_soup.find_all('p') if tag.text]:
        if line.find("Return to Search Page") != -1:
            continue

        if line.find('\xa0') != -1:
            process_address_line(line, info)

        if line.find("Contact:") != -1:
            name_parts = CONTACT_PATTERN.findall(line)[0].split(",")
            last_name = name_parts[0]
            if len(name_parts) == 3:
                last_name += name_parts[1]
                first_name = name_parts[2]
            else:
                first_name = name_parts[1]

            info['last_name'] = last_name
            info['first_name'] = first_name

        if EMAIL_PATTERN.search(line):
            info['email'] = EMAIL_PATTERN.search(line).group()

        if PHONE_PATTERN.search(line):
            process_phone_numbers(line, info)

        if URL_PATTERN.search(line):
            info['url'] = URL_PATTERN.search(line).group()
            break

    return info


def process_services(soup):
    pass


def process_gemstones(soup):
    gems = list()
    for row in soup.find_all('div', {'class': 'row'})[1:]:
        for child in row.children:
            if child.string == "Name:":
                gems.append(child.find_next_sibling().string)
    return gems


def process_html():
    profiles = list()

    if DEBUG:
        FILE_LIST = TEST_FILES
    else:
        FILE_LIST = sorted(listdir(DATA_DIR))

    for file in [f'{DATA_DIR}{file}' for file in FILE_LIST]:
        if DEBUG:
            print("Working on", file)
        file_handle = open(file, 'r', encoding='utf-8')
        SOUP = BeautifulSoup(file_handle, features='html.parser')

        profile = {'company': SOUP.find('h1').text}
        profile.update(process_contact_info(SOUP))

        if DEBUG:
            print(profile)

        services, gemstones = SOUP.find_all('h2')
        if services:
            process_services(SOUP)
        if gemstones:
            profile.update({'gemstones': process_gemstones(SOUP)})

        profiles.append(profile)
        file_handle.close()

    if DEBUG:
        ofile = '../data/results/poc_results_debug.csv'
    else:
        ofile = '../data/results/poc_results.csv'

    with open(ofile, 'w', newline='') as outfile:
        writer = DictWriter(outfile, fieldnames=CSV_HEADER)
        writer.writeheader()
        for profile in profiles:
            writer.writerow(profile)

    return len(profiles)


if __name__ == '__main__':
    num_records_processed = 0
    try:
        num_records_processed = process_html()
    except KeyboardInterrupt:
        pass
    finally:
        print(f"Finished processing {num_records_processed} records.")
