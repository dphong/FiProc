# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-06 15:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('FiProcess', '0004_schoolmaster'),
    ]

    operations = [
        migrations.CreateModel(
            name='cashPay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receiverWorkId', models.CharField(max_length=16)),
                ('receiverName', models.CharField(max_length=64)),
                ('receiveCard', models.CharField(max_length=19)),
                ('receiverBelong', models.CharField(max_length=256)),
                ('receiverTitle', models.CharField(max_length=64)),
                ('bankName', models.CharField(max_length=128)),
                ('workDate', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='CompanyPayRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('companyName', models.CharField(max_length=256)),
                ('bankName', models.CharField(max_length=128)),
                ('bankAccount', models.CharField(max_length=24)),
            ],
        ),
        migrations.CreateModel(
            name='FiStream',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applyDate', models.DateTimeField()),
                ('currentStage', models.CharField(max_length=64)),
                ('projectName', models.CharField(max_length=256)),
                ('streamDiscript', models.CharField(max_length=4096)),
                ('applicante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applicante', to='FiProcess.Stuff')),
                ('projectLeader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projectLeader', to='FiProcess.Stuff')),
                ('supportDept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.Department')),
            ],
        ),
        migrations.CreateModel(
            name='IcbcCardRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('spendAmount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cantApplyAmount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cantApplyReason', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='SpendProof',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spendType', models.CharField(max_length=64)),
                ('spendAmount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('proofDiscript', models.CharField(max_length=4096)),
                ('fiStream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.FiStream')),
            ],
        ),
        migrations.CreateModel(
            name='TravelRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leaveDate', models.DateTimeField()),
                ('returnDate', models.DateTimeField()),
                ('destination', models.CharField(max_length=128)),
                ('startPosition', models.CharField(max_length=128)),
                ('travelGrant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('foodGrant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fiStream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.FiStream')),
            ],
        ),
        migrations.AddField(
            model_name='icbccardrecord',
            name='spendProof',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.SpendProof'),
        ),
        migrations.AddField(
            model_name='icbccardrecord',
            name='stuff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.Stuff'),
        ),
        migrations.AddField(
            model_name='companypayrecord',
            name='spendProof',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.SpendProof'),
        ),
        migrations.AddField(
            model_name='cashpay',
            name='spendProof',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='FiProcess.FiStream'),
        ),
    ]
