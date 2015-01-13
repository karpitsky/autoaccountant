#!/usr/bin/env python
#-*- coding: utf-8 -*-
import decimal

import requests
from lxml import etree


def get_rate(date, curr_code):
    url = 'http://nbrb.by/Services/XmlExRates.aspx'
    params = {
        'ondate': date.strftime('%m/%d/%Y')
    }
    content = requests.get(url, params=params).text.strip().replace(u'\xef\xbb\xbf', '').encode('utf-8')
    tree = etree.fromstring(content)
    currency = tree.findall('.//Currency')
    for curr in currency:
        if curr.findall('CharCode')[0].text == curr_code:
            return decimal.Decimal(curr.findall('Rate')[0].text)
