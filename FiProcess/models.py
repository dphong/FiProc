from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible  # only if you need to support Python 2
class Department(models.Model):
    name = models.CharField(max_length=128)
    secretary = models.ForeignKey('Staff', blank=True, null=True, related_name='secretary')
    chief = models.ForeignKey('Staff', blank=True, null=True, related_name='chief')

    def __str__(self):
        return self.name


@python_2_unicode_compatible  # only if you need to support Python 2
class Staff(models.Model):
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


class StaffCheck(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)


@python_2_unicode_compatible  # only if you need to support Python 2
class SchoolMaster(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    # duty: 'school1' 'school2' 'school3'
    duty = models.CharField(max_length=16)

    def __str__(self):
        return self.staff.name


class FiStream(models.Model):
    applicante = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="applicante")
    applyDate = models.DateTimeField()
    supportDept = models.ForeignKey(Department, on_delete=models.CASCADE)
    projectLeader = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="projectLeader")
    # stage: 'create' 'project' 'department1' 'department2' 'projectDepartment' 'school1' 'school2' 'school3'
    #        'financial' 'finish'
    currentStage = models.CharField(max_length=64)
    projectName = models.CharField(max_length=256)
    streamDiscript = models.CharField(max_length=4096)
    # type: 'common' 'travel' 'labor'
    streamType = models.CharField(max_length=16)


class SignRecord(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    signer = models.ForeignKey(Staff, on_delete=models.CASCADE)
    signTime = models.DateTimeField()
    signed = models.BooleanField(default=False)
    signImage = models.CharField(max_length=10000)


class SpendProof(models.Model):
    fiStream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    # spendType: form '1' to '15'
    spendType = models.CharField(max_length=64)
    spendAmount = models.DecimalField(max_digits=15, decimal_places=2)
    proofDiscript = models.CharField(max_length=4096)


class CashPay(models.Model):
    spendProof = models.ForeignKey(SpendProof, on_delete=models.CASCADE)
    receiverWorkId = models.CharField(max_length=16)
    receiverName = models.CharField(max_length=64)
    receiveCard = models.CharField(max_length=19)
    receiverBelong = models.CharField(max_length=256)
    receiverTitle = models.CharField(max_length=64)
    bankName = models.CharField(max_length=128)
    workDate = models.DateTimeField()


class IcbcCardRecord(models.Model):
    spendProof = models.ForeignKey(SpendProof, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateTimeField()
    cantApplyAmount = models.DecimalField(max_digits=10, decimal_places=2)
    cantApplyReason = models.CharField(max_length=1024)


class CompanyPayRecord(models.Model):
    spendProof = models.ForeignKey(SpendProof, on_delete=models.CASCADE)
    companyName = models.CharField(max_length=256)
    bankName = models.CharField(max_length=128)
    bankAccount = models.CharField(max_length=24)


class TravelRecord(models.Model):
    fiStream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    leaveDate = models.DateTimeField()
    returnDate = models.DateTimeField()
    destination = models.CharField(max_length=128)
    startPosition = models.CharField(max_length=128)
    travelGrant = models.DecimalField(max_digits=10, decimal_places=2)
    foodGrant = models.DecimalField(max_digits=10, decimal_places=2)
