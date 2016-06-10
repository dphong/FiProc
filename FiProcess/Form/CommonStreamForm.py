# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.forms import ModelForm
from datetime import datetime
from decimal import Decimal

from ..models import Stuff, FiStream, SpendProof, CashPay, IcbcCardRecord, CompanyPayRecord


class CommonStreamForm(ModelForm):

    class Meta:
        model = FiStream
        fields = ['applyDate', 'supportDept', 'projectName', 'streamDiscript']
        labels = {
            'applyDate': u'报销日期',
            'supportDept': u'经费来源所属部门',
            'projectName': u'经费来源项目名称',
            'streamDiscript': u'经费使用目的',
        }
        field_classes = {
            'applyDate': forms.DateField,
        }

    department = forms.CharField(
        label=u'部门',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly'
            }
        ),
    )
    name = forms.CharField(
        label=u'姓名',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
            }
        ),
    )
    workId = forms.CharField(
        label=u'工号',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly'
            }
        ),
    )
    projectLeaderWorkId = forms.CharField(
        label=u'项目负责人工号',
    )
    projectLeaderName = forms.CharField(
        label=u'项目负责人'
    )

    class IcbcPay:

        def __init__(self):
            self.name = ''
            self.date = ''
            self.amount = 0.0
            self.actualAmount = 0.0
            self.icbcCard = ''
            self.payType = 0

    class CashPay:

        def __init__(self):
            self.name = ''
            self.amount = 0.0
            self.ccbCard = ''
            self.bankName = ''
            self.payType = 0

    def showCommonStream(self, request, indexForm):
        stuff = indexForm.getStuffFromRequest(request)
        if not stuff:
            return indexForm.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        form = CommonStreamForm(
            initial={'department': stuff.department.name,
                'name': stuff.name, 'workId': stuff.workId, 'applyDate': datetime.today(),
                'projectLeaderWorkId': stuff.workId, 'projectLeaderName': stuff.name}
        )
        return render_to_response('FiProcess/commonStream.html', RequestContext(request, {'form': form}))

    def commonStreamPost(self, request, indexForm):
        stream = FiStream()
        form = CommonStreamForm(request.POST, instance=stream)
        if not form.is_valid():
            return render_to_response('FiProcess/commonStream.html', RequestContext(request, {'form': form}))
        errorMsg = []
        warningMsg = []

        i = 1
        icbcList = []
        while ('icbc_cardHolderName' + str(i)) in request.POST:
            record = self.IcbcPay()
            record.name = request.POST['icbc_cardHolderName' + str(i)]
            record.date = request.POST['icbc_date' + str(i)]
            record.amount = request.POST['icbc_amount' + str(i)]
            record.actualAmount = request.POST['icbc_actualAmount' + str(i)]
            record.icbcCard = request.POST['icbc_account' + str(i)]
            record.payType = request.POST['icbc_spendType' + str(i)]
            icbcList.append(record)
            i = i + 1
        i = 1
        for icbc in icbcList:
            try:
                date = datetime.strptime(icbc.date, '%Y-%m-%d')
                if date.year < 2007:
                    raise Exception
            except:
                errorMsg.append(u'请正确填写第' + str(i) + u'条公务卡刷卡日期')
            try:
                print icbc.amount
                amount = float(icbc.amount)
                print 'float is ' + str(amount)
            except:
                errorMsg.append(u'请正确填写第' + str(i) + u'条公务卡刷卡金额')
            try:
                actualAmount = float(icbc.actualAmount)
            except:
                errorMsg.append(u'请正确填写第' + str(i) + u'条公务卡实报金额')
            if actualAmount > amount:
                errorMsg.append(u'第' + str(i) + u'条公务卡实报金额大于消费金额')
            try:
                Stuff.objects.get(name__exact=icbc.name, icbcCard__exact=icbc.icbcCard)
            except:
                errorMsg.append(u'第' + str(i) + u'条公务卡未在系统中注册')
            i = i + 1

        i = 1
        ccbList = []
        while ('ccb_cardHolderName' + str(i)) in request.POST:
            record = self.CashPay()
            record.name = request.POST['ccb_cardHolderName' + str(i)]
            record.amount = request.POST['ccb_amount' + str(i)]
            record.ccbCard = request.POST['ccb_account' + str(i)]
            record.bankName = request.POST['ccb_bankName' + str(i)]
            record.payType = request.POST['ccb_spendType' + str(i)]
            ccbList.append(record)
            i = i + 1
        i = 1
        for ccb in ccbList:
            try:
                float(ccb.amount)
            except:
                errorMsg.append(u'请正确填写第' + str(i) + u'条现金支付的金额')
            try:
                Stuff.objects.get(name__exact=ccb.name, ccbCard__exact=ccb.ccbCard)
            except:
                warningMsg.append(u'第' + str(i) + u'条现金支付的工资卡未在系统中注册，请核对无误')
            i = i + 1

        i = 1
        companyList = []
        while ('company_cardHolderName' + str(i)) in request.POST:
            record = self.CashPay()
            record.name = request.POST['company_cardHolderName' + str(i)]
            record.amount = request.POST['company_amount' + str(i)]
            record.ccbCard = request.POST['company_account' + str(i)]
            record.bankName = request.POST['company_bankName' + str(i)]
            record.payType = request.POST['company_spendType' + str(i)]
            companyList.append(record)
            i = i + 1
        i = 1
        for company in companyList:
            try:
                float(company.amount)
            except:
                errorMsg.append(u'请正确填写第' + str(i) + u'条对公转账的金额')
            i = i + 1
        if len(errorMsg):
            errorMsg.insert(0, u'请更正下列信息异常')
            return render_to_response('FiProcess/commonStream.html',
                RequestContext(request, {'form': form, 'errorMsg': errorMsg,
                    'list': icbcList, 'ccbList': ccbList, 'companyList': companyList}))

        stuff = indexForm.getStuffFromRequest(request)
        if not stuff:
            return indexForm.logout(request, u'用户信息异常，请保存本条错误信息，并联系管理员')
        stream.applicante = stuff
        stream.projectLeader = stuff
        stream.currentStage = 'create'
        stream.save()
        for icbc in icbcList:
            self.saveIcbcRecord(stream, icbc, request, indexForm)
        for ccb in ccbList:
            self.saveCcbRecord(stream, ccb)
        for com in companyList:
            self.saveCompanyRecord(stream, com)
        if len(warningMsg):
            return HttpResponseRedirect('FiProcess/commonStreamDetail.html',
                RequestContext(request, {'streamId': stream.id, 'warningMsg': warningMsg}))
        return HttpResponseRedirect('FiProcess/commonStreamDetail.html',
            RequestContext(request, {'streamId': stream.Id}))

    def saveIcbcRecord(self, stream, icbc, request, indexForm):
        spendProof = SpendProof()
        spendProof.fiStream = stream
        spendProof.spendType = icbc.payType
        spendProof.spendAmount = Decimal(icbc.amount)
        spendProof.proofDiscript = ''
        spendProof.save()
        icbcCardRec = IcbcCardRecord()
        icbcCardRec.spendProof = spendProof
        try:
            icbcCardRec.stuff = Stuff.objects.get(name__exact=icbc.name, icbcCard__exact=icbc.icbcCard)
        except:
            return indexForm.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        icbcCardRec.date = icbc.date
        icbcCardRec.spendAmount = Decimal(icbc.amount)
        icbcCardRec.cantApplyAmount = Decimal(icbc.amount) - Decimal(icbc.actualAmount)
        icbcCardRec.cantApplyReason = ''
        icbcCardRec.save()

    def saveCompanyRecord(self, stream, com):
        spendProof = self.saveSpendProofFromCcb(stream, com)
        comRec = CompanyPayRecord()
        comRec.spendProof = spendProof
        comRec.companyName = com.name
        comRec.bankName = com.bankName
        comRec.bankAccount = com.ccbCard
        comRec.save()

    def saveSpendProofFromCcb(self, stream, ccb):
        spendProof = SpendProof()
        spendProof.fiStream = stream
        spendProof.spendType = ccb.payType
        spendProof.spendAmount = Decimal(ccb.amount)
        spendProof.proofDiscript = ''
        spendProof.save()
        return spendProof

    def saveCcbRecord(self, stream, ccb):
        spendProof = self.saveSpendProofFromCcb(stream, ccb)
        ccbRec = CashPay()
        ccbRec.spendProof = spendProof
        ccbRec.receiverName = ccb.name
        ccbRec.receiverCard = ccb.ccbCard
        ccbRec.receiverTitle = ''
        ccbRec.bankName = ccb.bankName
        ccbRec.workDate = datetime.today()
        try:
            stuff = Stuff.objects.get(name__exact=ccb.name, ccbCard__exact=ccb.ccbCard)
            ccbRec.receiverWorkId = stuff.workId
            ccbRec.receiverBelong = stuff.department.name
        except:
            ccbRec.receiverWorkId = '0'
            ccbRec.receiverBelong = ''
        ccbRec.save()
