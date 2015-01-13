#!/usr/bin/env python
#-*- coding: utf-8 -*-
import argparse

from autoaccountant import AA


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Auto Accountant.')
    parser.add_argument('date_from', help='date from. Ex: 19/01/2014')
    parser.add_argument('to_date', help='to date. Ex: 21/01/2014')
    parser.add_argument('--book', help='generate KUDiR book')
    aa = AA(**vars(parser.parse_args()))
    aa.run()
