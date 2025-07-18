# Generated by Django 5.2.1 on 2025-05-23 18:09

import django.core.validators
import django.db.models.deletion
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('mobile_money', 'Mobile Money')], default='cash', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('reference', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('mobile_number', models.CharField(blank=True, help_text='Mobile number used for mobile payment in format +233XXXXXXXXX or 0XXXXXXXXX', max_length=15, null=True)),
                ('paystack_reference', models.CharField(blank=True, help_text='Reference from Paystack if mobile payment', max_length=100, null=True)),
                ('response_data', models.JSONField(blank=True, help_text='Payment processor response data', null=True)),
                ('notes', models.TextField(blank=True, help_text='Additional notes or comments about this payment', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='orders.order')),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('initialized', 'Initialized'), ('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('abandoned', 'Abandoned')], default='initialized', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('currency', models.CharField(default='GHS', help_text='Currency code (GHS for Ghana Cedis)', max_length=3)),
                ('response_data', models.JSONField(blank=True, help_text='Transaction response data from payment processor', null=True)),
                ('is_verified', models.BooleanField(default=False, help_text='Whether this transaction has been verified')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payments.payment')),
            ],
            options={
                'verbose_name': 'Payment Transaction',
                'verbose_name_plural': 'Payment Transactions',
                'ordering': ['-created_at'],
            },
        ),
    ]
