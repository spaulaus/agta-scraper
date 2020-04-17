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
from pycountry import countries

DEBUG = False

DATA_DIR = "data/html/"
TEST_FILE = "data/html/jewelrytelevision.html"

TEST_FILES = [
    "data/html/jewelrytelevision.html",
    "data/html/alanjamesjewelersllc.html",
    "data/html/robertshapiro.html",
    "data/html/monalisafinejewelsinc.html",
    "data/html/neallitmancompany.html"
]

CSV_HEADER = ['company', 'address1', 'city', 'state', 'zip', 'country', 'last_name', 'first_name',
              'email', 'phone', 'phone_extension', 'fax', 'url']

ADDRESS1_LABELS = ["Avenue", "Lane", "Road", "Boulevard", "Drive", "Street", "Ave.", "Dr.", "Rd.",
                   "Blvd.", "Ln.", "St.", "PO Box"]

URL_PATTERN = compile('http[s]?://[w]{0,3}[.]?\w+(.\w+){0,10}')
PHONE_PATTERN = compile('((\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4})')
EXTENSION_PATTERN = compile('(ext.) (\d{1,10})')
# From: https://emailregex.com/
EMAIL_PATTERN = compile('[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}')
ADDRESS_STATE_LINE_PATTERN = compile("([\w\s]+), ([\w\s]+)  (\d+)")
CONTACT_PATTERN = compile("Contact: ([a-zA-Z][0-9a-zA-Z .,'-]*)")


def process_address_line(input_line, info):
    for line in [line.replace("\xa0", ' ') for line in input_line.split("\n") if line]:
        if any(label in line for label in ADDRESS1_LABELS):
            info['address1'] = line.strip(", ")

        if ADDRESS_STATE_LINE_PATTERN.search(line):
            city, state, zcode = ADDRESS_STATE_LINE_PATTERN.findall(line)[0]
            info['city'] = city
            info['state'] = state
            info['zip'] = zcode

        try:
            countries.search_fuzzy(line)
            info['country'] = line
        except LookupError:
            pass


def process_phone_numbers(line, info):
    nums = PHONE_PATTERN.findall(line)
    info['phone'] = nums[0][0]
    if len(nums) == 2:
        info['fax'] = nums[1][0]
    if EXTENSION_PATTERN.search(line):
        info['phone_extension'] = EXTENSION_PATTERN.findall(line)[0][1]


contacts = list()
if DEBUG:
    FILE_LIST = TEST_FILES
else:
    FILE_LIST = listdir('data/html/')

for file in [f'{DATA_DIR}{file}' for file in FILE_LIST]:
    print("Working on", file)
    file_handle = open(file, 'r')
    SOUP = BeautifulSoup(file_handle, features='html.parser')

    contact_info = {'company': SOUP.find('h1').text}

    for line in [tag.text for tag in SOUP.find_all('p') if tag.text]:
        if line.find("Return to Search Page") != -1:
            continue

        if line.find('\xa0') != -1:
            process_address_line(line, contact_info)

        if line.find("Contact:") != -1:
            name_parts = CONTACT_PATTERN.findall(line)[0].split(",")
            last_name = name_parts[0]
            if len(name_parts) == 3:
                last_name += name_parts[1]
                first_name = name_parts[2]
            else:
                first_name = [1]

            contact_info['last_name'] = last_name
            contact_info['first_name'] = first_name

        if EMAIL_PATTERN.search(line):
            contact_info['email'] = EMAIL_PATTERN.search(line).group()

        if PHONE_PATTERN.search(line):
            process_phone_numbers(line, contact_info)

        if URL_PATTERN.search(line):
            contact_info['url'] = URL_PATTERN.search(line).group()
            break

    contacts.append(contact_info)
    file_handle.close()

with open('data/results/basic_info.csv', 'w', newline='') as outfile:
    writer = DictWriter(outfile, fieldnames=CSV_HEADER)
    writer.writeheader()
    for row in contacts:
        writer.writerow(row)
