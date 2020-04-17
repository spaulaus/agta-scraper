"""
file: agta-scraper.py
brief: Scrapes https://www.members.agta.org/assnfe/CompanySearch.asp for all participants
author: S. V. Paulauskas
date: April 17, 2020
"""
from os.path import isfile
from string import punctuation
import time

from bs4 import BeautifulSoup
import requests

BASE_URL = "https://www.members.agta.org/assnfe/"
FIRST_URL = "CompanySearch.asp?COMPNAME=&CITYNAME=&STATENAME=&CTRYID=181&LASTNAME=&GEMSTONEID=-1" \
            "&PRODUCTSID=-1&FORM=Search&MODE=FINDRESULTS&" \
            "SEARCHIDENTIFIER=207.106.153.252_4%2F16%2F2020+3%3A28%3A02+PM&TID=1"
# FIRST_URL = "CompanySearch.asp?MODE=FINDRESULTS&COMPNAME=&CITYNAME=&STATENAME=&CITYID=0" \
#             "&STATEID=0&CTRYID=181&SEARCHIDENTIFIER=207.106.153.252_4/16/2020%203:28:02%20PM" \
#             "&RETAILMBRS=0&ORGTYPE=0&GEMSTONEID=-1&PRODUCTSID=-1&COMPANYDATA=&TID=2" \
#             "&GEMCOLORID=-1&GEMCUTID=-1&GEMQUALID=A&PAGENUM=20"
RESPONSE = requests.get(BASE_URL + FIRST_URL)
SOUP = BeautifulSoup(RESPONSE.text, "html.parser")
NEXT_URL = SOUP.find('a', text="Next")['href']
PAGE_NUM = 1

# TODO: Things get a little squirrly around page 17. The "next" page takes you back to the I's even
#       though you have the correct address. I think it's a bug in their JS. I confirmed this
#       behavior manually on the website. In those cases, I modified the "first_url" to point to the
#       right page (e.g. 17). If we want to operationalize this, we'll need to handle that properly.
while NEXT_URL:
    print(f'Working on Page {PAGE_NUM}')
    for row in SOUP.find_all("div", class_='col-md-3'):
        link = row.find("a")
        print(f"Working on {link.contents[0]}")
        name = link.contents[0].translate(str.maketrans('', '', punctuation)) \
            .replace(' ', '').lower()
        if isfile(f'results/{name}.html'):
            print(f'{name} already exists! Skipping...')
            continue
        output = open(f"results/{name}.html", 'wb')
        output.write(requests.get(BASE_URL + link['href']).text.encode('utf-8'))
        output.close()
        time.sleep(1)
    SOUP = BeautifulSoup(requests.get(BASE_URL + NEXT_URL).text, "html.parser")
    NEXT_URL = SOUP.find('a', text="Next")['href']
    print(f'Finished Page {PAGE_NUM}')
    PAGE_NUM += 1
    time.sleep(10)
