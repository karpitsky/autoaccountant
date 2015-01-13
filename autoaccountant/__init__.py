#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import re
import datetime
import decimal
import locale
import math

from lxml import etree

from .config import STATEMENT_DIR, REFUNDED_PAYMENTS
from .helpers import get_rate

locale.setlocale(locale.LC_ALL, 'ru_RU')


class AA(object):
    def __init__(self, date_from, to_date, book=False):
        date_format = '%d/%m/%Y'
        self.date_from = datetime.datetime.strptime(date_from, date_format)
        self.to_date = datetime.datetime.strptime(to_date, date_format)
        self.book = bool(book)

    def fix_string(self, string):
        if not string:
            return ''
        return string.encode('utf-8')

    def fix_number(self, number):
        return locale.format('%.2f', number, 1)

    def format_ground(self, ground):
        match = re.search(r'([\d.]+)=USD по курсу (\d+)', ground.encode('utf-8'))
        if not match:
            match = re.search(r'([\d.]+) USD по курсу (\d+)', ground.encode('utf-8'))
            amount, rate = match.group().split('USD по курсу ')
        else:
            amount, rate = match.group().split('=USD по курсу ')
        return decimal.Decimal(amount), decimal.Decimal(rate)

    def load_statements(self):
        statements = []
        for filename in os.listdir(STATEMENT_DIR):
            path = os.path.join(STATEMENT_DIR, filename)
            f = open(path)
            data = f.read()
            f.close()

            data = data.split('<?xml version = "1.0" encoding="CP866"?>')
            for xml_doc in data:
                if not xml_doc or len(xml_doc) <= 1:
                    continue
                xml_doc = xml_doc.replace('<?xml:stylesheet type="text/xsl" ?>', '')
                xml_doc = xml_doc.decode('cp866').encode('utf-8')
                tree = etree.fromstring(xml_doc)

                statement = {}
                st = tree.findall('Statement')[0]
                statement.update({
                    'account': decimal.Decimal(st.findall('Account')[0].text),
                    'curr_code_iso': st.findall('CurrCodeISO')[0].text,
                    'date': datetime.datetime.strptime(st.findall('DateClosing')[0].text, '%d.%m.%Y'),
                })
                credit_documents = []
                crd = st.findall('CreditDocuments')[0]
                docs = crd.findall('.//Document')
                for doc in docs:
                    if doc.findall('OperType')[0].text not in ['1', '6']:
                        continue
                    if doc.findall('DocumentNumber')[0].text in REFUNDED_PAYMENTS:
                        continue

                    credit_document = {}
                    if statement['curr_code_iso'] == 'USD':
                        credit_document.update({
                            'amount': decimal.Decimal(doc.findall('Amount')[0].text.replace(',', '.')),
                            'document_id': doc.findall('DocumentNumber')[0].text
                        })
                    if statement['curr_code_iso'] == 'BYR':
                        payer = doc.findall('Payer')[0]
                        amount, rate = self.format_ground(payer.findall('Ground')[0].text)
                        credit_document.update({
                            'amount': amount,
                            'rate': rate
                        })
                    credit_documents.append(credit_document)
                statement.update({
                    'credit_documents': credit_documents
                })
                statements.append(statement)
        return statements

    def process(self, statements):
        result = []
        for statement in statements:
            if not statement['credit_documents']:
                continue
            if statement['date'] < self.date_from or statement['date'] > self.to_date:
                continue
            nbrb_rate = get_rate(statement['date'], 'USD')
            if statement['curr_code_iso'] == 'USD':
                for doc in statement['credit_documents']:
                    amount = doc['amount'] * nbrb_rate
                    result.append({
                        'amount': amount.to_integral_exact(rounding=decimal.ROUND_HALF_EVEN),
                        'ground': 'Перечисление №%s' % doc['document_id'],
                        'type': 1,
                        'date': statement['date']
                    })
            if statement['curr_code_iso'] == 'BYR':
                for doc in statement['credit_documents']:
                    rate = doc['rate'] - nbrb_rate
                    if rate > 0:
                        amount = doc['amount'] * rate
                        result.append({
                            'amount': amount.to_integral_exact(rounding=decimal.ROUND_HALF_EVEN),
                            'ground': 'Продажа валюты',
                            'type': 2,
                            'date': statement['date']
                        })
        return result

    def view(self, result):
        total = decimal.Decimal(0.0)
        for doc in result:
            total += doc['amount']

        sorted_result = sorted(result, key=lambda k: k['date'])
        print 'Details:'
        for doc in sorted_result:
            print doc['date'].strftime('%d/%m/%Y'), '\t', self.fix_number(doc['amount']), '\t', doc['ground']
        print ' '
        print '--- \t\t\t ---'
        print 'Total:\t\t', self.fix_number(total)
        print '5% of Total: \t', self.fix_number(total * decimal.Decimal(5.0) / decimal.Decimal(100.0))

    def run(self):
        statements = self.load_statements()
        result = self.process(statements)
        self.view(result)
