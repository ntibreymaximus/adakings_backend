#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.payments.models import Transaction
from django.utils import timezone
from datetime import date

print('=== TRANSACTION DEBUG ===')
print(f'Total transactions in database: {Transaction.objects.count()}')

today = date.today()
print(f'Today\'s date: {today}')

# Get today's transactions
today_transactions = Transaction.objects.filter(created_at__date=today)
print(f'Today\'s transactions count: {today_transactions.count()}')

# Get all transactions with their dates
all_transactions = Transaction.objects.all().order_by('-created_at')[:10]
print('\nLast 10 transactions:')
for t in all_transactions:
    print(f'ID: {t.id}, Amount: {t.amount}, Date: {t.created_at}, Today: {t.created_at.date() == today}')

# Check date formats
print('\nDate format analysis:')
for t in all_transactions[:3]:
    print(f'Transaction {t.id}:')
    print(f'  created_at: {t.created_at}')
    print(f'  created_at.date(): {t.created_at.date()}')
    print(f'  ISO format: {t.created_at.isoformat()}')
    print(f'  ISO date only: {t.created_at.date().isoformat()}')
    print(f'  Matches today: {t.created_at.date().isoformat() == today.isoformat()}')
    print()
