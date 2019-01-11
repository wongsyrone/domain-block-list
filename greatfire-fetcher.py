#!/usr/bin/env python3
# Domain list fetcher from GreatFire Analyzer, use at your own risk
# and modify parameters if needed

# Use this script under clean DNS result and net tunnel

# Copyright (c) 2019 wongsyrone

import sys
import traceback
import re
import bs4
import requests

# https://zh.greatfire.org/analyzer
# Examples:
# https://zh.greatfire.org/search/alexa-top-1000-domains?page=8
# https://zh.greatfire.org/search/domains?page=1091

# ===============================================================
# PARAMETERS
# ===============================================================

# Whether we should use proxy
# Configure them if set to 'True'
UseProxy = False

# Big page count is determined by DefaultMaxPageCount
GetAllPagesEvenIfWeHaveBigPageCount = True

DefaultMaxPageCount = 20
DefaultBlockThreshold = 80
DomainListFileName = 'greatfire-domains.txt'

if UseProxy:
    # Should install dependency to support SOCKS protocol
    myProxies = {
        'http': 'http://127.0.0.1:1088',
        'https': 'https://127.0.0.1:1088'
    }
else:
    myProxies = None

# ===============================================================
# Do NOT change content below if you don't know the meaning
# ===============================================================
AlexaTop1000URL = 'https://zh.greatfire.org/search/alexa-top-1000-domains'
DomainsURL = 'https://zh.greatfire.org/search/domains'
BlockedURL = 'https://zh.greatfire.org/search/blocked'

domainPattern = re.compile(
    r'^(:?(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'  # domain pt.1
    r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'  # domain pt.2
    r'([a-zA-Z0-9][-_a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.)+'  # domain pt.3
    r'([a-zA-Z]{2,13}|(xn--[a-zA-Z0-9]{2,30}))$'  # TLD
)

# for page count
# max length of digits from backwards
hrefPageParamPattern = re.compile('\d+$')

domainDict = {}


def populate_domain_blockPercent(rawHTML):
    """
    fill blocked domain list
    :param rawHTML:
    :return: None
    """
    if rawHTML is None:
        raise TypeError
    mysoup = bs4.BeautifulSoup(rawHTML, features='html.parser')
    entries = mysoup.select('td[class="first"]')
    # table layout:
    #   domain-name  date  block-percent  tags
    for entry in entries:
        domainName = entry.text
        # remove '%' sign
        blockPercent = int(entry.next_sibling.next_sibling.text[:-1])
        domainDict[domainName] = blockPercent


def get_first_page_and_count(url, proxies):
    """
    get first page raw HTML and page Count
    :param url:
    :param proxies:
    :return: {rawHTML, pageCount} or None if error occurred
    """
    try:
        print(f'handling {url} and get count')
        req = requests.get(url=url, proxies=proxies)
        if req.status_code != requests.codes.ok:
            return None
        pageRawHTML = req.text
        mysoup = bs4.BeautifulSoup(pageRawHTML, features='html.parser')
        entry = mysoup.select('li[class="pager-last last"] a')
        href = entry[0].attrs["href"]
        total_page_count = int(hrefPageParamPattern.findall(href)[0])
        print(f'{url} has pageCount {total_page_count} <= plus one to get actual page count')
        return {'rawHTML': pageRawHTML, 'pageCount': total_page_count}
    except:
        traceback.print_exc(file=sys.stdout)
        return None


def get_page_content(url, pageIndex, proxies):
    """
    get the whole page via page index
    :param url:
    :param pageIndex:
    :param proxies:
    :return: HTML in str or None if error occurred
    """
    try:
        print(f'handling {url} page {pageIndex}')
        req = requests.get(url=url, params={"page": pageIndex}, proxies=proxies)
        if req.status_code != requests.codes.ok:
            return None
        return req.text
    except:
        traceback.print_exc(file=sys.stdout)
        return None


def do_url(url, proxies):
    """
    fetch, parse and populate blocked domain list
    :param url:
    :param proxies:
    :return: None
    """
    tmpDict = get_first_page_and_count(url, proxies)
    if tmpDict is None:
        print("fail to get first page")
        raise ConnectionError
    total_page_count = tmpDict['pageCount']
    # the actual page one (it doesn't need ?page=<num> parameter)
    html = tmpDict['rawHTML']
    populate_domain_blockPercent(html)
    # get page range from the actual page two
    if not GetAllPagesEvenIfWeHaveBigPageCount and total_page_count > DefaultMaxPageCount:
        pageRange = range(1, DefaultMaxPageCount)
    else:
        # only when we specify we should fetch all pages or we have only a few to fetch
        pageRange = range(1, total_page_count)
    for i in pageRange:
        html = get_page_content(url, i, proxies)
        if html is None:
            print(f"fail to get {url} page {i}")
            raise ConnectionError
        populate_domain_blockPercent(html)


def is_valid_domain(domainStr):
    try:
        return domainPattern.fullmatch(domainStr) != None
    except:
        return False


def write_file(content):
    with open(DomainListFileName, mode='w', encoding='utf-8', newline='\n') as fd:
        fd.write(content)
        fd.flush()


# ===============================================================
# PROCEDURES
# ===============================================================

try:
    # download and populate mapping dictionary
    do_url(AlexaTop1000URL, myProxies)
    do_url(DomainsURL, myProxies)
    do_url(BlockedURL, myProxies)

    # handle threshold
    filteredDict = {domainName: blockPercent for domainName, blockPercent in domainDict.items() if
                    blockPercent >= DefaultBlockThreshold}

    resultList = list(filteredDict.keys())

    # handle invalid domains
    validDomainResultList = [item for item in resultList if is_valid_domain(item)]

    # write file
    write_file('\n'.join(validDomainResultList))
except:
    traceback.print_exc(file=sys.stdout)
