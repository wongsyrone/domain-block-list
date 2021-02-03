#!/usr/bin/env python3
# Domain list fetcher from GreatFire Analyzer, use at your own risk
# and modify parameters if needed

# Use this script under clean DNS result and net tunnel

# Copyright (c) 2019-2021 wongsyrone

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

# some default values can be overwritten

# Big page count is determined by DefaultMaxPageCount
DefaultGetAllPagesEvenIfWeHaveBigPageCount = False
DefaultMaxPageCount = 100
DefaultBlockThreshold = 80

DomainListFileName = 'greatfire-domains.txt'

if UseProxy:
    # Should install dependency to support SOCKS protocol
    myProxies = {
        'http': 'http://127.0.0.1:1088',
        'https': 'http://127.0.0.1:1088',
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
hrefPageParamPattern = re.compile(r'(?<=page=)\d+')

domainDict = {}


def populate_domain_blockPercent(soup_instance):
    """
    fill blocked domain list
    :param soup_instance:
    :return: None
    """
    if soup_instance is None:
        raise TypeError
    entries = soup_instance.select('td[class="first"]')
    # table layout:
    #   domain-name  date  block-percent  tags
    for entry in entries:
        domainName = entry.text.strip()
        blockPercentElem = entry.next_sibling.next_sibling
        if "blocked" in blockPercentElem["class"]:
            # remove '%' sign
            blockPercent = int(blockPercentElem.text.strip()[:-1])
            domainDict[domainName] = blockPercent


def get_first_page_and_count(url, proxies):
    """
    get first page raw HTML and page Count
    :param url:
    :param proxies:
    :return: {rawHTML, pageCount, soupIns} or None if error occurred
    """
    try:
        print(f'handling {url} and get count')
        req = requests.get(url=url, proxies=proxies)
        if req.status_code != requests.codes.ok:
            return None
        pageRawHTML = req.text
        mysoup = bs4.BeautifulSoup(pageRawHTML, features='lxml')
        entry = mysoup.select('li[class="pager-last last"] a')
        href = entry[0].attrs["href"]
        total_page_count = int(hrefPageParamPattern.findall(href)[0])
        print(f'{url} has pageCount {total_page_count} <= plus one to get actual page count')
        return {'rawHTML': pageRawHTML, 'pageCount': total_page_count, 'soupIns': mysoup}
    except:
        traceback.print_exc(file=sys.stdout)
        return None


def get_page_content(url, pageIndex, proxies):
    """
    get the whole page via page index
    :param url:
    :param pageIndex:
    :param proxies:
    :return: BeautifulSoup Instance or None if error occurred
    """
    try:
        print(f'handling {url} page {pageIndex}')
        req = requests.get(url=url, params={"page": pageIndex}, proxies=proxies)
        if req.status_code != requests.codes.ok:
            return None
        return bs4.BeautifulSoup(req.text, features='lxml')
    except:
        traceback.print_exc(file=sys.stdout)
        return None


def do_url(url, proxies, getAllPagesEvenIfWeHaveBigPageCount=DefaultGetAllPagesEvenIfWeHaveBigPageCount,
           maxPageCount=DefaultMaxPageCount):
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
    last_page_num = tmpDict['pageCount']
    total_page_count = last_page_num + 1
    # the actual page one (it doesn't need ?page=<num> parameter)
    populate_domain_blockPercent(tmpDict['soupIns'])
    # get page range from the actual page two
    if not getAllPagesEvenIfWeHaveBigPageCount and total_page_count > maxPageCount+1:
        pageRange = range(1, maxPageCount+1)
    else:
        # only when we specify we should fetch all pages or we have only a few to fetch
        pageRange = range(1, total_page_count)
    for i in pageRange:
        soup = get_page_content(url, i, proxies)
        if soup is None:
            print(f"fail to get {url} page {i}")
            raise ConnectionError
        populate_domain_blockPercent(soup)


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

if __name__ == '__main__':
    try:
        # download and populate mapping dictionary
        do_url(AlexaTop1000URL, myProxies, getAllPagesEvenIfWeHaveBigPageCount=True)
        do_url(DomainsURL, myProxies)
        do_url(BlockedURL, myProxies, getAllPagesEvenIfWeHaveBigPageCount=True)

        # handle threshold
        filteredDict = {domainName: blockPercent for domainName, blockPercent in domainDict.items() if
                        blockPercent >= DefaultBlockThreshold}

        resultList = list(filteredDict.keys())

        # handle invalid domains
        validDomainResultList = [item for item in resultList if is_valid_domain(item)]

        # to lower
        lowerValidDomainResultList = [item.lower() for item in validDomainResultList]

        # write sorted file
        write_file('\n'.join(sorted(lowerValidDomainResultList)))
    except:
        traceback.print_exc(file=sys.stdout)
