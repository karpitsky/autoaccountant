import os
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(os.path.join(PROJECT_DIR, 'autoaccountant'))

STATEMENT_DIR = os.path.join(PROJECT_DIR, 'statement')

REFUNDED_PAYMENTS = []

try:
	from config_local import *
except:
	pass
