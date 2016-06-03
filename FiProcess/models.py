from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible  # only if you need to support Python 2
class Department(models.Model):
    name = models.CharField(max_length=128)
    secretaryId = models.IntegerField(default=-1)
    chiefId = models.IntegerField(default=-1)

    def __str__(self):
        return self.name


@python_2_unicode_compatible  # only if you need to support Python 2
class Stuff(models.Model):
    # may be change to staff :)
    username = models.CharField(max_length=64)
    name = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    workId = models.CharField(max_length=6)
    phoneNumber = models.CharField(max_length=13)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    icbcCard = models.CharField(max_length=16, blank=True, default='')
    ccbCard = models.CharField(max_length=19, blank=True, default='')

    def __str__(self):
        return self.name


class StuffCheck(models.Model):
    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)


class SchoolMaster(models.Model):
    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)
