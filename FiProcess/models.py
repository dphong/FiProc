from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from datetime import datetime


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
    workId = models.CharField(max_length=10)
    phoneNumber = models.CharField(max_length=13)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    icbcCard = models.CharField(max_length=24, blank=True, default='')
    ccbCard = models.CharField(max_length=24, blank=True, default='')

    def __str__(self):
        return self.name


class StaffCheck(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)


@python_2_unicode_compatible  # only if you need to support Python 2
class SchoolMaster(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    # duty: 'school1' 'school2' 'school3'
    duty = models.CharField(max_length=16)
    dutyDescript = models.CharField(max_length=64, default="")

    def __str__(self):
        return self.staff.name


class FiStream(models.Model):
    applicante = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="applicante")
    applyDate = models.DateTimeField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    projectLeader = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="projectLeader")
    # stage: 'create' 'project' 'department1' 'department2' 'projectDepartment' 'school1' 'school2' 'school3'
    #        'financial' 'finish' 'refused' 'cwcSubmit' 'cwcChecking' 'cwcpaid' 'cantModify'
    # approval before create: 'unapprove' 'approvalDepartment' 'approvalSchool' 'approved'
    stage = models.CharField(max_length=64)
    projectName = models.CharField(max_length=256)
    descript = models.CharField(max_length=4096)
    # type: 'common' 'travel' 'labor' 'travelApproval' 'receptApproval' 'contractApproval'
    streamType = models.CharField(max_length=16)
    number = models.CharField(max_length=12, null=True)
    cwcSumbitDate = models.DateTimeField(null=True)
    cwcDealer = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="cwcDealer", null=True)


class SignRecord(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE, null=True)
    signer = models.ForeignKey(Staff, on_delete=models.CASCADE)
    signedTime = models.DateTimeField(null=True)
    signed = models.BooleanField(default=False)
    refused = models.BooleanField(default=False)
    signImage = models.CharField(max_length=10000, default="")
    # type: 'department1' 'department2' 'school1' 'school2' 'school3'
    #       'approvalDepartment' 'approvalSchool'
    stage = models.CharField(max_length=64)
    descript = models.CharField(max_length=1024, default="")


class SpendProof(models.Model):
    fiStream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    # spendType: form '1' to '15'
    spendType = models.CharField(max_length=64)
    spendAmount = models.DecimalField(max_digits=15, decimal_places=2)
    proofDescript = models.CharField(max_length=4096)


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
    approvalSign = models.ForeignKey(SignRecord, on_delete=models.CASCADE, null=True)
    fiStream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    duty = models.CharField(max_length=32)
    companionCnt = models.IntegerField()
    leaveDate = models.DateTimeField()
    returnDate = models.DateTimeField()
    destination = models.CharField(max_length=128)
    startPosition = models.CharField(max_length=128)
    travelGrant = models.DecimalField(max_digits=10, decimal_places=2)
    foodGrant = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=1024)
    # plane train car ship officialCar selfCar else
    travelType = models.CharField(max_length=64)
    travelDescript = models.CharField(max_length=128)


class Traveler(models.Model):
    record = models.ForeignKey(TravelRecord, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    duty = models.CharField(max_length=32)


class TravelRoute(models.Model):
    record = models.ForeignKey(TravelRecord, on_delete=models.CASCADE)
    date = models.DateTimeField()
    start = models.CharField(max_length=128)
    end = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class StaffLaborPay(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    duty = models.CharField(max_length=32)
    date = models.DateTimeField()
    reason = models.CharField(max_length=1024)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bankName = models.CharField(max_length=128)


class HireLaborPay(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    card = models.CharField(max_length=24)
    belong = models.CharField(max_length=256)
    bankName = models.CharField(max_length=128)
    personId = models.CharField(max_length=24)
    accountName = models.CharField(max_length=128)
    duty = models.CharField(max_length=32)
    date = models.DateTimeField()
    reason = models.CharField(max_length=1024)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class Recept(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    person = models.CharField(max_length=64)
    company = models.CharField(max_length=256)
    date = models.DateTimeField()
    target = models.CharField(max_length=1024)
    position = models.CharField(max_length=1024)
    standard = models.CharField(max_length=128)


class ReceptPerson(models.Model):
    recept = models.ForeignKey(Recept, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    position = models.CharField(max_length=256)
    duty = models.CharField(max_length=32)
    company = models.CharField(max_length=256)


class ReceptStaff(models.Model):
    recept = models.ForeignKey(Recept, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    duty = models.CharField(max_length=32)


class Contract(models.Model):
    stream = models.ForeignKey(FiStream, on_delete=models.CASCADE)
    number = models.CharField(max_length=128)
    target = models.CharField(max_length=256)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    projectCom = models.CharField(max_length=1024)
    lawyer = models.CharField(max_length=256)
    content = models.CharField(max_length=20000)
