# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-05 08:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('newsroom', '0032_auto_20161105_1025'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identification', models.CharField(blank=True, help_text='SA ID, passport or some form of official identification', max_length=20)),
                ('dob', models.DateField(blank=True, help_text='Please fill this in. Required by SARS.', null=True, verbose_name='date of birth')),
                ('address', models.TextField(blank=True, help_text='Please fill this in. Required by SARS.')),
                ('bank_name', models.CharField(blank=True, max_length=20)),
                ('bank_account_number', models.CharField(blank=True, max_length=20)),
                ('bank_account_type', models.CharField(default='CURRENT', max_length=20)),
                ('bank_branch_name', models.CharField(blank=True, help_text='Unnecessary for Capitec, FNB, Standard, Nedbank and Absa', max_length=20)),
                ('bank_branch_code', models.CharField(blank=True, help_text='Unnecessary for Capitec, FNB, Standard, Nedbank and Absa', max_length=20)),
                ('swift_code', models.CharField(blank=True, help_text='Only relevant for banks outside SA', max_length=12)),
                ('iban', models.CharField(blank=True, help_text='Only relevant for banks outside SA', max_length=34)),
                ('tax_no', models.CharField(blank=True, help_text='Necessary for SARS.', max_length=50)),
                ('tax_percent', models.DecimalField(decimal_places=0, default=25, help_text='Unless you have a tax directive we have to deduct 25% PAYE for SARS.', max_digits=2, verbose_name='tax %')),
                ('paid', models.BooleanField(default=False)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0.0, max_digits=8, verbose_name='amount')),
                ('invoice', filebrowser.fields.FileBrowseField(blank=True, max_length=200, null=True)),
                ('proof', filebrowser.fields.FileBrowseField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('0', 'Unpaid'), ('1', 'Queried by reporter-unpaid'), ('2', 'Approved by reporter-unpaid'), ('3', 'Approved by editor-unpaid'), ('4', 'Paid')], default='U', max_length=2)),
                ('notes', models.TextField(blank=True)),
                ('date_time_reporter_approved', models.DateTimeField(blank=True, editable=False, null=True)),
                ('date_time_editor_approved', models.DateTimeField(blank=True, editable=False, null=True)),
                ('date_time_processed', models.DateTimeField(blank=True, editable=False, null=True)),
                ('invoice_num', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsroom.Author')),
            ],
            options={
                'ordering': ['-modified'],
            },
        ),
    ]
