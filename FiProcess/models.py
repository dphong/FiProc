from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

# Create your models here.
@python_2_unicode_compatible  # only if you need to support Python 2
class Department(models.Model):
    name = models.CharField(max_length=128)
    secretaryId = models.IntegerField(default=-1)
    chiefId = models.IntegerField(default=-1)
    def __str__(self):
        return self.name

@python_2_unicode_compatible  # only if you need to support Python 2
class Stuff(models.Model):
    name = models.CharField(max_length=64)
    workId = models.CharField(max_length=6)
    phoneNumber = models.CharField(max_length=13)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    icbcCard = models.CharField(max_length=16)
    ccbCard = models.CharField(max_length=19)
    def __str__(self):
        return self.name